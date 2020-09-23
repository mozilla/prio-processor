import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pytest
from click.testing import CliRunner
from prio_processor.origin import indexing
from pyspark.sql import Row


@pytest.fixture()
def config_path():
    return Path(__file__).parent.parent / "config"


@pytest.fixture()
def origins_dict(config_path):
    path = config_path / "telemetry_origin_data_inc.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture()
def config(config_path):
    path = config_path / "content.json"
    with open(path) as f:
        return json.load(f)


def test_origins_dict(origins_dict):
    indexing.validate_origins(origins_dict)
    assert sorted(origins_dict[0].keys()) == sorted(["name", "hash", "index"])
    assert len(origins_dict) == origins_dict[-1]["index"] + 1


def test_config(config):
    batch_id = "content.blocking_blocked-{index}"
    (part_0, part_1) = [[d["n_data"] for d in config if d["batch_id"] == batch_id.format(index=i)][i] for i in (1, 2)]
    assert part_0 == 2046
    assert part_1 == 441


@pytest.fixture()
def prio_aggregated_data(tmp_path, spark, config):
    """
    ├── _SUCCESS
    ├── batch_id=content.blocking_blocked-0
    │   └── part-00000-45945db7-4b6d-4eef-9e6f-76f98a3aefd4.c000.json
    ├── batch_id=content.blocking_blocked-1
    │   └── part-00001-45945db7-4b6d-4eef-9e6f-76f98a3aefd4.c000.json
    ...
    └── batch_id=content.blocking_storage_access_api_exempt_TESTONLY-1
        └── part-00011-45945db7-4b6d-4eef-9e6f-76f98a3aefd4.c000.json
    """
    output = str(tmp_path / "data")
    rows = []
    for d in config:
        batch_id = d["batch_id"]
        n_data = d["n_data"]
        # write data in such a way where each aggregate value matches to the
        # index value
        if int(batch_id.split("-")[1]) == 1:
            offset = 2046
        else:
            offset = 0
        datum = [offset + i for i in range(n_data)]
        row = Row(
            batch_id=batch_id,
            id=str(uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            payload=datum,
        )
        rows.append(row)
    df = spark.createDataFrame(rows)
    df.write.partitionBy("batch_id").json(output)
    return output


def test_prio_aggregated_data_fixture(spark, prio_aggregated_data, config):
    df = spark.read.json(prio_aggregated_data)
    assert df.count() == len(config)


def test_indexing_transform_unit(spark):
    whitelist = [
        {"batch_id": "test-0", "n_data": 3},
        {"batch_id": "test-1", "n_data": 2},
    ]
    origins = []
    for i, ch in enumerate("abcde"):
        origins.append({"name": ch, "hash": ch, "index": i})

    def build_row(batch_id, payload):
        return Row(
            batch_id=batch_id,
            id=str(uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            payload=payload,
        )

    data = [build_row("test-0", [0, 1, 2]), build_row("test-1", [3, 4])]
    df = spark.createDataFrame(data)
    transformed = indexing.transform(df, whitelist, origins)
    assert transformed.count() == 5
    assert transformed.where("index <> aggregate").count() == 0

    with pytest.raises(Exception):
        whitelist["test-3"] = 1
        # `origins` doesn't need to be modified because transform should throw before then
        data.append(build_row("test-3", [5]))
        indexing.transform(spark.createDataFrame(data), whitelist, origins).count()


def test_indexing_transform(spark, prio_aggregated_data, config, origins_dict):
    df = spark.read.json(prio_aggregated_data)
    transformed = indexing.transform(df, config, origins_dict)

    merged_batches = {}
    for d in config:
        batch_id = d["batch_id"]
        n_data = d["n_data"]
        key = batch_id.split("-")[0]
        merged_batches[key] = merged_batches.get(key, 0) + n_data

    assert transformed.select("batch_id").distinct().count() == len(merged_batches)
    assert transformed.count() == sum(merged_batches.values())
    assert transformed.where("index <> aggregate").count() == 0


def test_indexing_cli(spark, tmp_path, prio_aggregated_data, config_path):
    output = str(tmp_path / "output")
    runner = CliRunner()
    result = runner.invoke(
        indexing.run,
        [
            "--input",
            prio_aggregated_data,
            "--output",
            output,
            "--config",
            str(config_path / "content.json"),
            "--origins",
            str(config_path / "telemetry_origin_data_inc.json"),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    df = spark.read.json(output)
    assert df.count() > 0
    assert df.where("index <> aggregate").count() == 0
