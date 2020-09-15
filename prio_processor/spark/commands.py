import math
from base64 import b64decode, b64encode
from datetime import datetime
from functools import partial
from pathlib import Path
from uuid import uuid4

import click
from prio_processor.prio.commands import import_keys, match_server
from prio_processor.prio.options import (
    data_config,
    input_1,
    input_2,
    output_1,
    output_2,
    public_key,
    server_config,
)
from prio_processor.spark import udf
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

ROOT = Path(__file__).parent.parent.parent


def spark_session():
    spark = SparkSession.builder.getOrCreate()
    spark.conf.set("spark.sql.session.timeZone", "UTC")
    spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "true")
    return spark


@click.group()
def entry_point():
    pass


@entry_point.command()
@data_config
@public_key
@output_1
@click.option("--n-rows", type=int, help="Number of rows randomly generate.")
@click.option(
    "--scale", type=int, default=1, help="Factor to duplicate shares for output."
)
@click.option("--partition-size-mb", type=int, default=250, help="")
def generate(
    batch_id,
    n_data,
    public_key_hex_internal,
    public_key_hex_external,
    output,
    n_rows,
    scale,
    partition_size_mb,
):
    shares = (
        spark_session()
        .range(n_rows * n_data)
        .select(
            (F.col("id") % n_rows).alias("row_id"),
            F.when(F.rand() > 0.5, 1).otherwise(0).alias("payload"),
        )
        .groupBy("row_id")
        .agg(F.collect_list("payload").alias("payload"))
        .select(
            F.pandas_udf(
                partial(
                    udf.encode,
                    batch_id,
                    n_data,
                    public_key_hex_internal,
                    public_key_hex_external,
                ),
                returnType="a: binary, b: binary",
            )("payload").alias("shares")
        )
        # repeat this data `scale` times
        .withColumn("_repeat", F.explode(F.array_repeat(F.lit(0), scale)))
        .drop("_repeat")
        .withColumn("id", F.udf(lambda: str(uuid4()), returnType="string")())
    )
    # we can make an estimate with just a single row, since the configuration
    # is the same here.
    row = shares.first()
    dataset_estimate_mb = (
        (len(b64encode(row.shares.a)) + len(str(uuid4())))
        * n_rows
        * scale
        * 1.0
        / 10 ** 6
    )
    num_partitions = math.ceil(dataset_estimate_mb / partition_size_mb)
    click.echo(f"writing {num_partitions} partitions")

    # try to be efficient without caching by repartitioning
    repartitioned = (
        shares.withColumn(
            "shares",
            F.map_from_arrays(
                F.array(F.lit("a"), F.lit("b")), F.array("shares.a", "shares.b")
            ),
        )
        .repartitionByRange(num_partitions, "id")
        .select("id", F.explode("shares").alias("server_id", "payload"))
    )
    repartitioned.write.partitionBy("server_id").json(output, mode="overwrite")


@entry_point.command()
@click.option("--submission-date", default=datetime.now().isoformat()[:10])
@click.option(
    "--config",
    type=click.Path(dir_okay=False, exists=True),
    default=str(ROOT / "config" / "test-small.json"),
)
@public_key
@output_1
@click.option(
    "--n-rows", type=int, default=100, help="Number of rows to generate per batch."
)
@click.option(
    "--n-partitions", type=int, default=2, help="Number of partitions for each batch."
)
def generate_integration(
    submission_date,
    config,
    public_key_hex_internal,
    public_key_hex_external,
    output,
    n_rows,
    n_partitions,
):
    """Generate test data from a configuration file.

    The data is generated in a deterministic way and fits into memory."""
    spark = spark_session()

    assert n_rows > 0
    config_data = spark.read.json(config, multiLine=True)

    def generate_data(batch_id, n_data):
        return dict(
            batch_id=batch_id,
            n_data=n_data,
            payload=[int(x % 3 == 0 or x % 5 == 0) for x in range(n_data)],
        )

    test_data = []
    for conf in config_data.collect():
        batch_id = conf["batch_id"]
        n_data = conf["n_data"]
        test_data += [generate_data(batch_id, n_data) for _ in range(n_rows - 1)]
        # include invalid data for a batch
        test_data += [generate_data(batch_id, n_data + 1)]
    # include unknown batch id
    test_data += [generate_data("bad-id", 10) for _ in range(n_rows)]

    shares = (
        spark.createDataFrame(test_data)
        .select(
            "batch_id",
            F.udf(udf.encode_single, returnType="a: binary, b: binary")(
                "batch_id",
                "n_data",
                F.lit(public_key_hex_internal),
                F.lit(public_key_hex_external),
                "payload",
            ).alias("shares"),
        )
        .withColumn("id", F.udf(lambda: str(uuid4()), returnType="string")())
    )

    repartitioned = (
        shares.withColumn(
            "shares",
            F.map_from_arrays(
                F.array(F.lit("a"), F.lit("b")), F.array("shares.a", "shares.b")
            ),
        )
        .repartitionByRange(n_partitions, "batch_id", "id")
        .select(
            F.lit(submission_date).alias("submission_date"),
            "batch_id",
            "id",
            F.explode("shares").alias("server_id", "payload"),
        )
    )
    repartitioned.write.partitionBy("submission_date", "server_id", "batch_id").json(
        output, mode="overwrite"
    )


@entry_point.command()
@data_config
@public_key
@input_1
@output_2
def encode_shares(
    batch_id,
    n_data,
    public_key_hex_internal,
    public_key_hex_external,
    input,
    output_a,
    output_b,
):
    click.echo("Running encode shares")
    spark = spark_session()
    shares = (
        spark.read.json(input)
        .withColumn("pid", F.spark_partition_id())
        .groupBy("pid")
        .applyInPandas(
            lambda pdf: udf.encode(
                batch_id, n_data, public_key_hex_internal, public_key_hex_external, pdf
            ),
            schema="a: binary, b: binary",
        )
        .withColumn("id", F.udf(lambda: str(uuid4()), returnType="string")())
    )
    shares.cache()
    row = shares.first()
    dataset_estimate_mb = (
        (len(b64encode(row.shares.a)) + len(str(uuid4())))
        * n_rows
        * scale
        * 1.0
        / 10 ** 6
    )
    num_partitions = math.ceil(dataset_estimate_mb / partition_size_mb)
    click.echo(f"writing {num_partitions} partitions")
    repartitioned = shares.repartitionByRange(num_partitions, "id").cache()
    repartitioned.select("id", F.base64("a").alias("payload")).write.json(
        output_a, mode="overwrite"
    )
    repartitioned.select("id", F.base64("b").alias("payload")).write.json(
        output_b, mode="overwrite"
    )


@entry_point.command()
@data_config
@server_config
@public_key
@input_1
@output_1
def verify1(
    batch_id,
    n_data,
    server_id,
    private_key_hex,
    shared_secret,
    public_key_hex_internal,
    public_key_hex_external,
    input,
    output,
):
    """Decode a batch of shares"""
    click.echo("Running verify1")
    spark = spark_session()

    (
        spark.read.json(input)
        .select(
            "id",
            F.base64(
                F.pandas_udf(
                    partial(
                        udf.verify1,
                        batch_id,
                        n_data,
                        server_id,
                        private_key_hex,
                        b64decode(shared_secret),
                        public_key_hex_internal,
                        public_key_hex_external,
                    ),
                    returnType="binary",
                )(F.unbase64("payload"))
            ).alias("payload"),
        )
        .write.json(output, mode="overwrite")
    )


@entry_point.command()
@data_config
@server_config
@public_key
@input_1
@input_2
@output_1
def verify2(
    batch_id,
    n_data,
    server_id,
    private_key_hex,
    shared_secret,
    public_key_hex_internal,
    public_key_hex_external,
    input,
    input_internal,
    input_external,
    output,
):
    """Verify a batch of SNIPs"""
    click.echo("Running verify2")
    spark = spark_session()
    shares = spark.read.json(input)
    internal = spark.read.json(input_internal)
    external = spark.read.json(input_external)
    (
        shares.select("id", F.unbase64("payload").alias("shares"))
        .join(internal.select("id", F.unbase64("payload").alias("internal")), on="id")
        .join(external.select("id", F.unbase64("payload").alias("external")), on="id")
        .select(
            "id",
            F.base64(
                F.pandas_udf(
                    partial(
                        udf.verify2,
                        batch_id,
                        n_data,
                        server_id,
                        private_key_hex,
                        b64decode(shared_secret),
                        public_key_hex_internal,
                        public_key_hex_external,
                    ),
                    returnType="binary",
                )("shares", "internal", "external")
            ).alias("payload"),
        )
        .write.json(output, mode="overwrite")
    )


@entry_point.command()
@data_config
@server_config
@public_key
@input_1
@input_2
@output_1
def aggregate(
    batch_id,
    n_data,
    server_id,
    private_key_hex,
    shared_secret,
    public_key_hex_internal,
    public_key_hex_external,
    input,
    input_internal,
    input_external,
    output,
):
    """Generate an aggregate share from a batch of verified SNIPs"""
    click.echo("Running aggregate")
    spark = spark_session()
    shares = spark.read.json(input)
    internal = spark.read.json(input_internal)
    external = spark.read.json(input_external)

    args = [
        batch_id,
        n_data,
        server_id,
        private_key_hex,
        b64decode(shared_secret),
        public_key_hex_internal,
        public_key_hex_external,
    ]
    (
        shares.join(internal.withColumnRenamed("payload", "internal"), on="id")
        .join(external.withColumnRenamed("payload", "external"), on="id")
        .select(
            F.unbase64("payload").alias("shares"),
            F.unbase64("internal").alias("internal"),
            F.unbase64("external").alias("external"),
            F.spark_partition_id().alias("pid"),
        )
        .groupBy("pid")
        .applyInPandas(
            lambda pdf: udf.aggregate(*args, pdf),
            schema="payload: binary, error: int, total: int",
        )
        .groupBy()
        .applyInPandas(
            lambda pdf: udf.total_share(*args, pdf),
            schema="payload: binary, error: int, total: int",
        )
        .withColumn("payload", F.base64("payload"))
    ).write.json(output, mode="overwrite")


@entry_point.command()
@data_config
@server_config
@public_key
@input_2
@output_1
def publish(
    batch_id,
    n_data,
    server_id,
    private_key_hex,
    shared_secret,
    public_key_hex_internal,
    public_key_hex_external,
    input_internal,
    input_external,
    output,
):
    """Generate a final aggregate."""
    click.echo("Running publish")

    spark = spark_session()
    (
        spark.read.json(input_internal)
        .withColumn("server", F.lit("internal"))
        .union(spark.read.json(input_external).withColumn("server", F.lit("external")))
        .withColumn("payload", F.unbase64("payload"))
        .groupBy()
        .pivot("server", ["internal", "external"])
        .agg(*[F.min(c).alias(c) for c in ["payload", "error", "total"]])
        .select(
            F.udf(lambda: str(uuid4()), returnType="string")().alias("id"),
            F.lit(datetime.utcnow().isoformat()).alias("timestamp"),
            F.pandas_udf(
                partial(
                    udf.publish,
                    batch_id,
                    n_data,
                    server_id,
                    private_key_hex,
                    b64decode(shared_secret),
                    public_key_hex_internal,
                    public_key_hex_external,
                ),
                returnType="array<int>",
            )("internal_payload", "external_payload").alias("payload"),
            F.col("internal_error").alias("error"),
            F.col("internal_total").alias("total"),
        )
        .write.json(output, mode="overwrite")
    )


if __name__ == "__main__":
    entry_point()
