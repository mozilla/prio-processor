import array
import json
from base64 import b64decode
from functools import partial
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from prio_processor.prio.commands import import_keys, import_public_keys, match_server
from prio_processor.spark import udf
from pyspark.sql import Row
from pyspark.sql import functions as F


@pytest.fixture()
def root():
    return Path(__file__).parent / "resources" / "cli"


@pytest.fixture()
def args(root):
    config = json.loads((root / "config.json").read_text())
    server_a_keys = json.loads((root / "server_a_keys.json").read_text())
    server_b_keys = json.loads((root / "server_b_keys.json").read_text())
    shared_seed = json.loads((root / "shared_seed.json").read_text())

    return SimpleNamespace(
        server_id="A",
        private_key_hex=server_a_keys["private_key"].encode(),
        shared_secret=b64decode(shared_seed["shared_seed"]),
        public_key_hex_internal=server_a_keys["public_key"].encode(),
        public_key_hex_external=server_b_keys["public_key"].encode(),
        batch_id=config["batch_id"].encode(),
        n_data=config["n_data"],
    )


def test_encode(spark, root, args):
    df = spark.read.json(str(root / "client"))
    transformed = df.select(
        F.pandas_udf(
            partial(
                udf.encode,
                args.batch_id,
                args.n_data,
                args.public_key_hex_internal,
                args.public_key_hex_external,
            ),
            returnType="a: binary, b: binary",
        )("payload").alias("shares")
    ).select(F.base64("shares.a").alias("a"), F.base64("shares.b").alias("b"))

    # assert the shares are all the same length
    server_a_payload_len = (
        spark.read.json(str(root / "server_a" / "raw"))
        .select((F.expr("avg(length(payload))")).alias("len"))
        .first()
        .len
    )
    # jq '.payload | length' tests/resources/cli/server_a/raw/data.ndjson -> 396
    assert server_a_payload_len == 396
    assert (
        transformed.where(f"abs(length(a) - {server_a_payload_len}) > 1").count() == 0
    )

    server_b_payload_len = (
        spark.read.json(str(root / "server_b" / "raw"))
        .select((F.expr("avg(length(payload))")).alias("len"))
        .first()
        .len
    )
    # jq '.payload | length' tests/resources/cli/server_a/raw/data.ndjson -> 208
    assert server_b_payload_len == 208
    assert (
        transformed.where(f"abs(length(b) - {server_b_payload_len}) > 1").count() == 0
    )


def test_encode_bad_data(spark, root, args):
    # 2 good fields and 1 bad field
    data = [{"payload": [1 for _ in range(args.n_data)]} for _ in range(2)] + [
        {"payload": [-1 for _ in range(args.n_data + 1)]}
    ]
    df = spark.createDataFrame(data)
    df.show()
    transformed = df.select(
        F.pandas_udf(
            partial(
                udf.encode,
                args.batch_id,
                args.n_data,
                args.public_key_hex_internal,
                args.public_key_hex_external,
            ),
            returnType="a: binary, b: binary",
        )("payload").alias("shares")
    ).select(F.base64("shares.a").alias("a"), F.base64("shares.b").alias("b"))
    transformed.show()
    assert transformed.where("a IS NOT NULL").count() == 2
    assert transformed.where("a IS NULL").count() == 1


def test_verify1(spark, root, args):
    df = spark.read.json(str(root / "server_a" / "raw"))
    df.show(vertical=True, truncate=100)

    actual = df.select(
        "id",
        F.base64(
            F.pandas_udf(
                partial(
                    udf.verify1,
                    args.batch_id,
                    args.n_data,
                    args.server_id,
                    args.private_key_hex,
                    args.shared_secret,
                    args.public_key_hex_internal,
                    args.public_key_hex_external,
                ),
                returnType="binary",
            )(F.unbase64("payload"))
        ).alias("expected_payload"),
    )

    expected = spark.read.json(
        str(root / "server_a" / "intermediate" / "internal" / "verify1")
    )

    joined = actual.join(expected, on="id")
    joined.show(vertical=True, truncate=100)

    # NOTE: Payloads are only the same if they are processed in a deterministic
    # order using the same context due to the pseudorandom seed. The CLI
    # application assumes the same server context across all of the rows in a
    # partition. However, the UDF approach will generate a new server context
    # for every row.
    assert joined.where("length(expected_payload) <> length(payload)").count() == 0


def test_verify1_bad_data(spark, root, args):
    # we can use server b's data
    a = spark.read.json(str(root / "server_a" / "raw"))
    b = spark.read.json(str(root / "server_b" / "raw"))
    df = spark.createDataFrame(a.union(b).collect() + [Row(id=None, payload=None)])

    actual = df.select(
        "id",
        F.pandas_udf(
            partial(
                udf.verify1,
                args.batch_id,
                args.n_data,
                args.server_id,
                args.private_key_hex,
                args.shared_secret,
                args.public_key_hex_internal,
                args.public_key_hex_external,
            ),
            returnType="binary",
        )(F.unbase64("payload")).alias("expected_payload"),
    )
    actual.show()

    assert actual.where("expected_payload IS NOT NULL").count() == a.count()
    assert actual.where("expected_payload IS NULL").count() == b.count() + 1


def test_verify2(spark, root, args):
    raw = spark.read.json(str(root / "server_a" / "raw"))
    internal = spark.read.json(
        str(root / "server_a" / "intermediate" / "internal" / "verify1")
    )
    external = spark.read.json(
        str(root / "server_a" / "intermediate" / "external" / "verify1")
    )

    actual = (
        raw.select("id", F.unbase64("payload").alias("shares"))
        .join(internal.select("id", F.unbase64("payload").alias("internal")), on="id")
        .join(external.select("id", F.unbase64("payload").alias("external")), on="id")
        .select(
            "id",
            F.base64(
                F.pandas_udf(
                    partial(
                        udf.verify2,
                        args.batch_id,
                        args.n_data,
                        args.server_id,
                        args.private_key_hex,
                        args.shared_secret,
                        args.public_key_hex_internal,
                        args.public_key_hex_external,
                    ),
                    returnType="binary",
                )("shares", "internal", "external")
            ).alias("expected_payload"),
        )
    )

    expected = spark.read.json(
        str(root / "server_a" / "intermediate" / "internal" / "verify2")
    )

    joined = actual.join(expected, on="id")
    assert joined.where("length(expected_payload) <> length(payload)").count() == 0


def test_verify2_bad_data(spark, root, args):
    def read_df(uid):
        server_root = root / f"server_{uid}"
        raw = spark.read.json(str(server_root / "raw"))
        internal = spark.read.json(
            str(server_root / "intermediate" / "internal" / "verify1")
        )
        external = spark.read.json(
            str(server_root / "intermediate" / "external" / "verify1")
        )
        return (
            raw.select("id", F.unbase64("payload").alias("shares"))
            .join(
                internal.select("id", F.unbase64("payload").alias("internal")), on="id"
            )
            .join(
                external.select("id", F.unbase64("payload").alias("external")), on="id"
            )
        )

    a = read_df("a")
    b = read_df("b")
    df = spark.createDataFrame(
        a.union(b).collect() + [Row(id=None, shares=None, internal=None, external=None)]
    )

    actual = df.select(
        "id",
        F.pandas_udf(
            partial(
                udf.verify2,
                args.batch_id,
                args.n_data,
                args.server_id,
                args.private_key_hex,
                args.shared_secret,
                args.public_key_hex_internal,
                args.public_key_hex_external,
            ),
            returnType="binary",
        )("shares", "internal", "external").alias("expected_payload"),
    )
    actual.show()

    assert actual.where("expected_payload IS NOT NULL").count() == a.count()
    assert actual.where("expected_payload IS NULL").count() == b.count() + 1


def test_aggregate(spark, root, args):
    raw = spark.read.json(str(root / "server_a" / "raw"))
    internal = spark.read.json(
        str(root / "server_a" / "intermediate" / "internal" / "verify2")
    )
    external = spark.read.json(
        str(root / "server_a" / "intermediate" / "external" / "verify2")
    )

    aggregates = (
        raw.select("id", F.unbase64("payload").alias("shares"))
        .join(internal.select("id", F.unbase64("payload").alias("internal")), on="id")
        .join(external.select("id", F.unbase64("payload").alias("external")), on="id")
        .groupBy()
        .applyInPandas(
            lambda pdf: udf.aggregate(
                args.batch_id,
                args.n_data,
                args.server_id,
                args.private_key_hex,
                args.shared_secret,
                args.public_key_hex_internal,
                args.public_key_hex_external,
                pdf,
            ),
            schema="payload binary, error int, total int",
        )
    )
    aggregates.show()
    rows = aggregates.collect()
    assert len(rows) == 1
    assert rows[0].total == 5
    assert rows[0].error == 0


def test_aggregate_bad_data(spark, root, args):
    def read_df(uid):
        server_root = root / f"server_{uid}"
        raw = spark.read.json(str(server_root / "raw"))
        internal = spark.read.json(
            str(server_root / "intermediate" / "internal" / "verify2")
        )
        external = spark.read.json(
            str(server_root / "intermediate" / "external" / "verify2")
        )
        return (
            raw.select("id", F.unbase64("payload").alias("shares"))
            .join(
                internal.select("id", F.unbase64("payload").alias("internal")), on="id"
            )
            .join(
                external.select("id", F.unbase64("payload").alias("external")), on="id"
            )
        )

    a = read_df("a")
    b = read_df("b")

    # Serialize and deserialize to infer schema for null row
    df = spark.createDataFrame(
        a.union(b).collect() + [Row(id=None, shares=None, internal=None, external=None)]
    )
    assert df.where("internal is null").count() == 1

    aggregates = df.groupBy().applyInPandas(
        lambda pdf: udf.aggregate(
            args.batch_id,
            args.n_data,
            args.server_id,
            args.private_key_hex,
            args.shared_secret,
            args.public_key_hex_internal,
            args.public_key_hex_external,
            pdf,
        ),
        schema="payload binary, error int, total int",
    )
    aggregates.show()
    rows = aggregates.collect()
    assert len(rows) == 1
    assert rows[0].total == a.count() + b.count() + 1
    assert rows[0].error == b.count() + 1


def test_total_share(spark, root, args):
    raw = spark.read.json(str(root / "server_a" / "raw"))
    internal = spark.read.json(
        str(root / "server_a" / "intermediate" / "internal" / "verify2")
    )
    external = spark.read.json(
        str(root / "server_a" / "intermediate" / "external" / "verify2")
    )

    aggregates = (
        raw.select("id", F.unbase64("payload").alias("shares"))
        .join(internal.select("id", F.unbase64("payload").alias("internal")), on="id")
        .join(external.select("id", F.unbase64("payload").alias("external")), on="id")
        .repartition(2)
        .withColumn("pid", F.spark_partition_id())
        .groupBy("pid")
        .applyInPandas(
            lambda pdf: udf.aggregate(
                args.batch_id,
                args.n_data,
                args.server_id,
                args.private_key_hex,
                args.shared_secret,
                args.public_key_hex_internal,
                args.public_key_hex_external,
                pdf,
            ),
            schema="payload binary, error int, total int",
        )
    )
    aggregates.show()
    rows = aggregates.collect()
    assert len(rows) == 2
    assert {2, 3} == set(r.total for r in rows)
    assert all(r.error == 0 for r in rows)

    total_share = aggregates.groupBy().applyInPandas(
        lambda pdf: udf.total_share(
            args.batch_id,
            args.n_data,
            args.server_id,
            args.private_key_hex,
            args.shared_secret,
            args.public_key_hex_internal,
            args.public_key_hex_external,
            pdf,
        ),
        schema="payload binary, error int, total int",
    )
    total_share.show()

    rows = total_share.collect()
    assert len(rows) == 1
    assert len(rows[0].payload) > 0
    assert rows[0].total == 5
    assert rows[0].error == 0


def test_publish(spark, tmp_path, root, args):
    expect = json.loads(next((root / "server_a" / "processed").glob("*")).read_text())
    internal = root / "server_a" / "intermediate" / "internal" / "aggregate"
    external = root / "server_a" / "intermediate" / "external" / "aggregate"
    df = (
        spark.read.json(str(internal))
        .withColumn("server", F.lit("internal"))
        .union(spark.read.json(str(external)).withColumn("server", F.lit("external")))
        .withColumn("payload", F.unbase64("payload"))
        .groupBy()
        .pivot("server", ["internal", "external"])
        .agg(
            F.min("payload").alias("payload"),
            F.min("error").alias("error"),
            F.min("total").alias("total"),
        )
        .select(
            F.pandas_udf(
                partial(
                    udf.publish,
                    args.batch_id,
                    args.n_data,
                    args.server_id,
                    args.private_key_hex,
                    args.shared_secret,
                    args.public_key_hex_internal,
                    args.public_key_hex_external,
                ),
                returnType="array<int>",
            )("internal_payload", "external_payload").alias("payload"),
            F.col("internal_error").alias("error"),
            F.col("internal_total").alias("total"),
        )
    )
    assert df.count() == 1
    row = df.first()
    assert row.payload == expect["payload"]
    assert row.error == 0
    assert row.total == 5


@pytest.mark.parametrize("num_partitions", [1, 2])
def test_end_to_end(spark, tmp_path, root, num_partitions):
    server_a_keys = json.loads((root / "server_a_keys.json").read_text())
    server_b_keys = json.loads((root / "server_b_keys.json").read_text())
    shared_seed = json.loads((root / "shared_seed.json").read_text())["shared_seed"]

    batch_id = "test_batch"
    n_data = 7
    n_rows = 20

    params_a = [
        batch_id.encode(),
        n_data,
        "A",
        server_a_keys["private_key"].encode(),
        b64decode(shared_seed),
        server_a_keys["public_key"].encode(),
        server_b_keys["public_key"].encode(),
    ]
    params_b = [
        batch_id.encode(),
        n_data,
        "B",
        server_b_keys["private_key"].encode(),
        b64decode(shared_seed),
        server_b_keys["public_key"].encode(),
        server_a_keys["public_key"].encode(),
    ]

    def show(df):
        df.show()
        return df

    def explain(df):
        df.explain()
        return df

    shares = (
        spark.createDataFrame(
            [Row(payload=[int(i % 3 == 0 or i % 5 == 0) for i in range(n_data)])]
            * n_rows
        )
        .select(
            F.pandas_udf(
                partial(
                    udf.encode,
                    batch_id.encode(),
                    n_data,
                    server_a_keys["public_key"].encode(),
                    server_b_keys["public_key"].encode(),
                ),
                returnType="a: binary, b: binary",
            )("payload").alias("shares")
        )
        .withColumn("id", F.udf(lambda: str(uuid4()), "string")())
    )
    shares.cache()
    shares.show()

    verify1_a = shares.select(
        "id",
        F.pandas_udf(partial(udf.verify1, *params_a), returnType="binary")(
            "shares.a"
        ).alias("verify1_a"),
    )

    verify1_b = shares.select(
        "id",
        F.pandas_udf(partial(udf.verify1, *params_b), returnType="binary")(
            "shares.b"
        ).alias("verify1_b"),
    )

    verify2_a = (
        shares.join(verify1_a, on="id")
        .join(verify1_b, on="id")
        .select(
            "id",
            F.pandas_udf(partial(udf.verify2, *params_a), returnType="binary")(
                "shares.a", "verify1_a", "verify1_b"
            ).alias("verify2_a"),
        )
    )

    verify2_b = (
        shares.join(verify1_a, on="id")
        .join(verify1_b, on="id")
        .select(
            "id",
            F.pandas_udf(partial(udf.verify2, *params_b), returnType="binary")(
                "shares.b", "verify1_b", "verify1_a"
            ).alias("verify2_b"),
        )
    )

    aggregate_a = (
        shares.join(verify2_a, on="id")
        .join(verify2_b, on="id")
        .select(
            F.col("shares.a").alias("shares"),
            F.col("verify2_a").alias("internal"),
            F.col("verify2_b").alias("external"),
        )
        # this only works if partition < 4GB
        .groupBy()
        .applyInPandas(
            lambda pdf: udf.aggregate(*params_a, pdf),
            schema="payload binary, error int, total int",
        )
        .groupBy()
        .applyInPandas(
            lambda pdf: udf.total_share(*params_a, pdf),
            schema="payload binary, error int, total int",
        )
    )

    aggregate_b = explain(
        show(
            shares.join(verify2_a, on="id")
            .join(verify2_b, on="id")
            .repartitionByRange(num_partitions, "id")
            .select(
                F.col("shares.b").alias("shares"),
                F.col("verify2_b").alias("internal"),
                F.col("verify2_a").alias("external"),
            )
            .withColumn("pid", F.spark_partition_id())
        )
        .groupBy("pid")
        .applyInPandas(
            lambda pdf: udf.aggregate(*params_b, pdf),
            schema="payload binary, error int, total int",
        )
        .groupBy()
        .applyInPandas(
            lambda pdf: udf.total_share(*params_b, pdf),
            schema="payload binary, error int, total int",
        )
    )

    def test_total_shares(aggregate):
        print(aggregate)
        assert len(aggregate.payload) > 0
        assert aggregate.error == 0
        assert aggregate.total == n_rows
        return True

    assert test_total_shares(aggregate_a.first())
    assert test_total_shares(aggregate_b.first())

    published = show(
        aggregate_a.withColumn("server", F.lit("internal"))
        .union(aggregate_b.withColumn("server", F.lit("external")))
        .groupBy()
        .pivot("server", ["internal", "external"])
        .agg(*[F.min(x).alias(x) for x in aggregate_a.columns])
    ).select(
        F.pandas_udf(partial(udf.publish, *params_a), returnType="array<int>")(
            "internal_payload", "external_payload"
        ).alias("payload"),
        F.col("internal_error").alias("error"),
        F.col("internal_total").alias("total"),
    )
    published.cache()
    assert published.count() == 1
    row = published.first()
    assert row.error == 0
    assert row.total == n_rows
    assert row.payload == [
        int(i % 3 == 0 or i % 5 == 0) * n_rows for i in range(n_data)
    ]
