import pytest
import json
import os

from pathlib import Path
from uuid import uuid4
from click.testing import CliRunner
from prio_processor import staging
from pyspark.sql import Row
from base64 import b64encode


BASE_DATE = "2019-06-26"
BASE_DATE_NEXT = "2019-06-27"
NUM_HOURS = 2
NUM_PARTS = 2
NUM_PINGS = 2


def pubsub_message(ping: str):
    return {
        "attributeMap": {
            "document_namespace": "telemetry",
            "document_type": "prio",
            "document_version": "4",
            # ...
        },
        "payload": b64encode(ping.encode("utf-8")).decode("utf-8"),
    }


@pytest.fixture()
def prio_ping():
    """ Read a ping as seen from a Firefox client.

    ```bash
    $ jq '.payload.prioData | .[] | .encoding' tests/resources/fx-69.0a1.json \
      | sort | uniq -c

    3 "content.blocking_blocked_TESTONLY-0"
    3 "content.blocking_blocked_TESTONLY-1"
    ```
    """
    path = Path(__file__).parent / "resources" / "fx-69.0a1.json"
    return json.load(open(path))


@pytest.fixture()
def moz_fx_data_stage_data(tmp_path, prio_ping):
    """ Create a bucket that mirrors the google cloud storage sink in the
    ingestion service.
    """

    # bucket / re-publisher name / output sink
    sink_dir = Path(
        tmp_path
        / "moz-fx-data-stage-data"
        / "telemetry-decoded_gcs-sink-doctype_prio"
        / "output"
    )

    # date (YYYY-MM-DD) / hour (HH) / namespace / type / version / *.ndjson
    folders = [
        sink_dir / BASE_DATE / f"{hour:02d}" / "telemetry" / "prio" / "4"
        for hour in range(NUM_HOURS)
    ] + [sink_dir / BASE_DATE_NEXT / "00" / "telemetry" / "prio" / "4"]
    for folder in folders:
        folder.mkdir(parents=True)
        for part_id in range(NUM_PARTS):
            with (folder / f"part-{part_id}.ndjson").open("w") as f:
                for _ in range(NUM_PINGS):
                    ping = prio_ping.copy()
                    ping["id"] = str(uuid4())
                    pubsub = pubsub_message(json.dumps(ping))
                    f.write(json.dumps(pubsub))
                    f.write("\n")
    return sink_dir


@pytest.fixture()
def extracted(spark, moz_fx_data_stage_data):
    return staging.CloudStorageExtract(spark).extract(moz_fx_data_stage_data, BASE_DATE)


def test_extract(extracted):
    assert extracted.count() == NUM_HOURS * NUM_PARTS * NUM_PINGS
    assert not {"id", "prioData"} - set(extracted.columns)
    assert extracted.schema == staging.ExtractPrioPing.payload_schema


def test_estimate_num_partitions(spark):
    df = spark.createDataFrame([Row(prio="#" * 100)] * 100)
    # 10kb of data with 1k partitions => 10 partitions
    num_partitions = staging.estimate_num_partitions(df, partition_size_mb=0.001)
    assert num_partitions == 10


def test_transform(extracted):
    df = staging.transform(extracted)

    assert df.columns == ["batch_id", "server_id", "id", "payload"]

    # 2 servers, 2 batch-ids, 3 blocks, 8 pings
    assert df.count() == 2 * 2 * 3 * 8

    # check that there are only two servers
    server_ids = [x.server_id for x in df.select("server_id").distinct().collect()]
    assert set(server_ids) == {"a", "b"}

    # check the set of "encoding" or "batch-id" fields in the pings
    batch_ids = [x.batch_id for x in df.select("batch_id").distinct().collect()]
    assert set(batch_ids) == {
        "content.blocking_blocked_TESTONLY-0",
        "content.blocking_blocked_TESTONLY-1",
    }

    # check that the cardinality of the new dataset corresponds to the values
    # from the jq expression in the `prio_ping` fixture
    unique_ids = (
        df.where("batch_id = 'content.blocking_blocked_TESTONLY-0'")
        .where("server_id == 'a'")
        .select("id")
        .distinct()
        .count()
    )
    # (3 blocks per ping) * (8 pings across the raw dataset)
    assert unique_ids == 3 * 8


def test_staging_run(moz_fx_data_stage_data, tmp_path):
    """
    To update the directory tree, run `tree` over the `tmp_path` folder.

    ├── moz-fx-data-stage-data
    │   └── telemetry-decoded_gcs-sink-doctype_prio
    │       └── output
    │           └── 2019-06-26
    │               ├── 00
    │               │   └── telemetry
    │               │       └── prio
    │               │           └── 4
    │               │               ├── part-0.ndjson
    │               │               └── part-1.ndjson
    │               └── 01
    │                   └── telemetry
    │                       └── prio
    │                           └── 4
    │                               ├── part-0.ndjson
    │                               └── part-1.ndjson
    └── output
        ├── _SUCCESS
        └── submission_date=2019-06-26
            ├── server_id=a
            │   ├── batch_id=content.blocking_blocked_TESTONLY-0
            │   │   └── part-00000-8bd2216c-55dc-49df-9d95-59349163c9a6.c000.json
            │   └── batch_id=content.blocking_blocked_TESTONLY-1
            │       └── part-00000-8bd2216c-55dc-49df-9d95-59349163c9a6.c000.json
            └── server_id=b
                ├── batch_id=content.blocking_blocked_TESTONLY-0
                │   └── part-00000-8bd2216c-55dc-49df-9d95-59349163c9a6.c000.json
                └── batch_id=content.blocking_blocked_TESTONLY-1
                    └── part-00000-8bd2216c-55dc-49df-9d95-59349163c9a6.c000.json
    """
    output = Path(tmp_path / "output")
    runner = CliRunner()
    result = runner.invoke(
        staging.run,
        [
            "--date",
            BASE_DATE,
            "--input",
            str(moz_fx_data_stage_data),
            "--output",
            str(output),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert output.is_dir()
    assert len(os.listdir(output)) > 0


def test_staging_run_fixed_partitions(moz_fx_data_stage_data, tmp_path, monkeypatch):
    """Run the entire pipeline again, except fix the number of partitions when
    repartitioning by range.

    The corresponding partitions for each server should contain the same ids.
    """

    def mock_estimate_num_partitions(*args, **kwargs):
        """
        ├── _SUCCESS
        └── submission_date=2019-06-26
            ├── server_id=a
            │   ├── batch_id=content.blocking_blocked_TESTONLY-0
            │   │   ├── part-00000-6adba759-6e58-4092-8120-6331705e2e46.c000.json
            │   │   └── part-00001-6adba759-6e58-4092-8120-6331705e2e46.c000.json
            │   └── batch_id=content.blocking_blocked_TESTONLY-1
            │       ├── part-00002-6adba759-6e58-4092-8120-6331705e2e46.c000.json
            │       └── part-00003-6adba759-6e58-4092-8120-6331705e2e46.c000.json
            └── server_id=b
                ├── batch_id=content.blocking_blocked_TESTONLY-0
                │   ├── part-00000-6adba759-6e58-4092-8120-6331705e2e46.c000.json
                │   └── part-00001-6adba759-6e58-4092-8120-6331705e2e46.c000.json
                └── batch_id=content.blocking_blocked_TESTONLY-1
                    ├── part-00002-6adba759-6e58-4092-8120-6331705e2e46.c000.json
                    └── part-00003-6adba759-6e58-4092-8120-6331705e2e46.c000.json
        """
        return 4

    monkeypatch.setattr(
        staging, "estimate_num_partitions", mock_estimate_num_partitions
    )

    output = Path(tmp_path / "output")
    runner = CliRunner()
    result = runner.invoke(
        staging.run,
        [
            "--date",
            BASE_DATE,
            "--input",
            str(moz_fx_data_stage_data),
            "--output",
            str(output),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    def list_json(path):
        return [name for name in os.listdir(path) if name.endswith(".json")]

    def get_id_set(path, part):
        s = set()
        with (path / part).open() as f:
            for row in map(json.loads, f.readlines()):
                if not row:
                    continue
                s.add(row["id"])
        return s

    # manually verify each of the partitions by hand
    batch_ids = [
        "content.blocking_blocked_TESTONLY-0",
        "content.blocking_blocked_TESTONLY-1",
    ]
    for batch_id in batch_ids:
        path = output / f"submission_date={BASE_DATE}"
        path_a = path / "server_id=a" / f"batch_id={batch_id}"
        path_b = path / "server_id=b" / f"batch_id={batch_id}"

        assert path_a.is_dir()
        assert path_b.is_dir()

        # each folder should contain the same partitions
        assert list_json(path_a) == list_json(path_b)

        for part in list_json(path_a):
            set_a = get_id_set(path_a, part)
            set_b = get_id_set(path_b, part)
            assert len(set_a) > 0
            assert set_a == set_b


def test_staging_run_incremental(moz_fx_data_stage_data, tmp_path):
    output = str(tmp_path / "output")
    runner = CliRunner()
    runner.invoke(
        staging.run,
        [
            "--date",
            BASE_DATE,
            "--input",
            str(moz_fx_data_stage_data),
            "--output",
            output,
        ],
        catch_exceptions=False,
    )

    runner.invoke(
        staging.run,
        [
            "--date",
            BASE_DATE_NEXT,
            "--input",
            str(moz_fx_data_stage_data),
            "--output",
            output,
        ],
        catch_exceptions=False,
    )
    dates = sorted(
        [p.split("=")[1] for p in os.listdir(output) if "submission_date=" in p]
    )
    assert dates == [BASE_DATE, BASE_DATE_NEXT]


def test_staging_run_idempotent(spark, moz_fx_data_stage_data, tmp_path):
    output = tmp_path / "output"

    def run() -> int:
        CliRunner().invoke(
            staging.run,
            [
                "--date",
                BASE_DATE,
                "--input",
                str(moz_fx_data_stage_data),
                "--output",
                str(output),
            ],
            catch_exceptions=False,
        )
        return spark.read.json(str(output)).count()

    initial = run()
    rerun = run()
    assert initial == rerun
