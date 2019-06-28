import pytest
import json
import os

from pathlib import Path
from uuid import uuid4
from click.testing import CliRunner
from prio_processor import staging


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


def test_extract(spark, moz_fx_data_stage_data):
    df = staging.extract(spark, moz_fx_data_stage_data, BASE_DATE)
    assert df.count() == NUM_HOURS * NUM_PARTS * NUM_PINGS


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
