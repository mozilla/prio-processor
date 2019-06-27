import pytest
import json
import os

from pathlib import Path
from uuid import uuid4
from click.testing import CliRunner
from prio_processor import staging

import apache_beam as beam
from apache_beam.testing.test_pipeline import TestPipeline
from apache_beam.testing.util import assert_that, equal_to

BASE_DATE = "2019-06-26"
NUM_HOURS = 2
NUM_PARTS = 2
NUM_PINGS = 2


@pytest.fixture()
def prio_ping():
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


def test_prio_ping_transform():
    with TestPipeline() as p:
        test_data = list(map(json.dumps, [{"id": "1"}, {"id": "2"}]))
        data = p | "create test data" >> beam.Create(test_data)
        result = data | staging.PrioPingTransform()
        assert_that(result, equal_to(test_data))


def test_staging_run(moz_fx_data_stage_data, tmpdir):
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
            f"{output}/part",
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert output.is_dir()
    assert len(os.listdir(output)) > 0
