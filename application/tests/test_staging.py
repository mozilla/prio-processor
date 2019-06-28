import pytest
import json
import os

from pathlib import Path
from uuid import uuid4
from click.testing import CliRunner
from prio_processor import staging
from pyspark.sql import Row


BASE_DATE = "2019-06-26"
NUM_HOURS = 2
NUM_PARTS = 2
NUM_PINGS = 2


@pytest.fixture()
def prio_ping():
    """
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
def moz_fx_data_stage_data(tmpdir, prio_ping):

    # bucket / re-publisher name / output sink
    sink_dir = Path(
        tmpdir
        / "moz-fx-data-stage-data"
        / "telemetry-decoded_gcs-sink-doctype_prio"
        / "output"
    )

    # date (YYYY-MM-DD) / hour (HH) / namespace / type / version / *.ndjson
    folders = [
        sink_dir / BASE_DATE / f"{hour:02d}" / "telemetry" / "prio" / "4"
        for hour in range(NUM_HOURS)
    ]
    for folder in folders:
        folder.mkdir(parents=True)
        for part_id in range(NUM_PARTS):
            with (folder / f"part-{part_id}.ndjson").open("w") as f:
                for _ in range(NUM_PINGS):
                    ping = prio_ping.copy()
                    ping["id"] = str(uuid4())
                    f.write(json.dumps(ping))
                    f.write("\n")
    return sink_dir


@pytest.fixture()
def extracted(spark, moz_fx_data_stage_data):
    return staging.extract(spark, moz_fx_data_stage_data, BASE_DATE)


def test_extract(extracted):
    assert extracted.count() == NUM_HOURS * NUM_PARTS * NUM_PINGS


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


def test_staging_run(moz_fx_data_stage_data, tmpdir):
    """
    To update the directory tree, run `tree` over the `tmpdir` folder.

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
            ├── batch_id=content.blocking_blocked_TESTONLY-0
            │   ├── server_id=a
            │   │   └── part-00000-312e29a4-ad3e-4451-97b1-c3aeb437ce12.c000.json
            │   └── server_id=b
            │       └── part-00000-312e29a4-ad3e-4451-97b1-c3aeb437ce12.c000.json
            └── batch_id=content.blocking_blocked_TESTONLY-1
                ├── server_id=a
                │   └── part-00000-312e29a4-ad3e-4451-97b1-c3aeb437ce12.c000.json
                └── server_id=b
                    └── part-00000-312e29a4-ad3e-4451-97b1-c3aeb437ce12.c000.json
    """
    output = Path(tmpdir / "output")
    runner = CliRunner()
    result = runner.invoke(
        staging.run,
        [
            "--date",
            BASE_DATE,
            "--input",
            f"{moz_fx_data_stage_data}",
            "--output",
            f"{output}",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert output.is_dir()
    assert len(os.listdir(output)) > 0


def test_staging_run_fixed_partitions(moz_fx_data_stage_data, tmpdir, monkeypatch):
    """Run the entire pipeline again, except fix the number of partitions when
    repartitioning by range.

    The corresponding partitions for each server should contain the same ids.
    """

    def mock_estimate_num_partitions(*args, **kwargs):
        """
        output
        ├── _SUCCESS
        └── submission_date=2019-06-26
            ├── batch_id=content.blocking_blocked_TESTONLY-0
            │   ├── server_id=a
            │   │   ├── part-00000-8e329ed1-6d7e-4912-9746-6845ca90ad47.c000.json
            │   │   ├── part-00001-8e329ed1-6d7e-4912-9746-6845ca90ad47.c000.json
            │   │   ├── part-00002-8e329ed1-6d7e-4912-9746-6845ca90ad47.c000.json
            │   │   └── part-00003-8e329ed1-6d7e-4912-9746-6845ca90ad47.c000.json
            │   └── server_id=b
            │       ├── part-00000-8e329ed1-6d7e-4912-9746-6845ca90ad47.c000.json
            │       ├── part-00001-8e329ed1-6d7e-4912-9746-6845ca90ad47.c000.json
            │       ├── part-00002-8e329ed1-6d7e-4912-9746-6845ca90ad47.c000.json
            │       └── part-00003-8e329ed1-6d7e-4912-9746-6845ca90ad47.c000.json
            └── batch_id=content.blocking_blocked_TESTONLY-1
                ├── server_id=a
                │   ├── part-00004-8e329ed1-6d7e-4912-9746-6845ca90ad47.c000.json
                │   ├── part-00005-8e329ed1-6d7e-4912-9746-6845ca90ad47.c000.json
                │   ├── part-00006-8e329ed1-6d7e-4912-9746-6845ca90ad47.c000.json
                │   └── part-00007-8e329ed1-6d7e-4912-9746-6845ca90ad47.c000.json
                └── server_id=b
                    ├── part-00004-8e329ed1-6d7e-4912-9746-6845ca90ad47.c000.json
                    ├── part-00005-8e329ed1-6d7e-4912-9746-6845ca90ad47.c000.json
                    ├── part-00006-8e329ed1-6d7e-4912-9746-6845ca90ad47.c000.json
                    └── part-00007-8e329ed1-6d7e-4912-9746-6845ca90ad47.c000.json
        """
        return 8

    monkeypatch.setattr(
        staging, "estimate_num_partitions", mock_estimate_num_partitions
    )

    output = Path(tmpdir / "output")
    runner = CliRunner()
    result = runner.invoke(
        staging.run,
        [
            "--date",
            BASE_DATE,
            "--input",
            f"{moz_fx_data_stage_data}",
            "--output",
            f"{output}",
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
        path = output / f"submission_date={BASE_DATE}" / f"batch_id={batch_id}"
        path_a = path / "server_id=a"
        path_b = path / "server_id=b"

        assert path_a.is_dir()
        assert path_b.is_dir()

        # each folder should contain the same partitions
        assert list_json(path_a) == list_json(path_b)

        for part in list_json(path_a):
            set_a = get_id_set(path_a, part)
            set_b = get_id_set(path_b, part)
            assert len(set_a) > 0
            assert set_a == set_b
