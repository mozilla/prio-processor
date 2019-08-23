import pytest
import json

from pathlib import Path
from click.testing import CliRunner
from prio_processor import indexing
from pyspark.sql import Row
from uuid import uuid4
from datetime import datetime


@pytest.fixture()
def config_path():
    return Path(__file__).parent.parent / "config"


@pytest.fixture()
def origins_path(config_path):
    return config_path / "telemetry_origin_data_inc.json"


@pytest.fixture()
def content_dict(config_path):
    path = config_path / "content.json"
    with open(path) as f:
        return json.load(f)


def test_origins_path(origins_path):
    with open(origins_path) as f:
        data = json.load(f)

    # test the schema
    assert sorted(data[0].keys()) == sorted(["name", "hash", "index"])
    assert len(data) == data[-1]["index"] + 1


def test_content_dict(content_dict):
    batch_id = "content.blocking_blocked-{index}"
    assert content_dict[batch_id.format(index=0)] == 2046
    assert content_dict[batch_id.format(index=1)] == 441


@pytest.fixture()
def prio_aggregated_data(tmp_path, spark, content_dict):
    """
    ├── _SUCCESS
    └── submission_date=2019-08-22
        ├── batch_id=content.blocking_blocked-0
        │   └── part-00000-45945db7-4b6d-4eef-9e6f-76f98a3aefd4.c000.json
        ├── batch_id=content.blocking_blocked-1
        │   └── part-00001-45945db7-4b6d-4eef-9e6f-76f98a3aefd4.c000.json
        ...
        └── batch_id=content.blocking_storage_access_api_exempt_TESTONLY-1
            └── part-00011-45945db7-4b6d-4eef-9e6f-76f98a3aefd4.c000.json
    """
    output = tmp_path / "data"
    rows = []
    for batch_id, n_data in content_dict.items():
        datum = [(i % 3 or i % 5) * 100 for i in range(n_data)]
        row = Row(
            submission_date="2019-08-22",
            batch_id=batch_id,
            id=str(uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            payload=datum,
        )
        rows.append(row)
    df = spark.createDataFrame(rows)
    df.write.partitionBy("submission_date", "batch_id").json(str(output))
    return output


def test_prio_aggregated_data(spark, prio_aggregated_data, content_dict):
    df = spark.read.json(prio_aggregated_data)
    assert df.count() == len(content_dict)
