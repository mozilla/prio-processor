import json
import urllib.request
from io import BytesIO

import pytest
from click.testing import CliRunner
from prio_processor.origin import origins

# First five origins from mozilla-central
# https://hg.mozilla.org/mozilla-central/raw-file/tip/toolkit/components/telemetry/core/TelemetryOriginData.inc
TELEMETRY_ORIGIN_DATA_INC = """
// dummy origin, this is used to be a counter of page loads.
ORIGIN("PAGELOAD", "PAGELOAD")

ORIGIN("advertstream.com", "lzPiT1FuoHNMKQ1Hw8AaTi68TokOB24ciFBqmCk62ek=")
ORIGIN("kitaramedia.com", "r+U9PL3uMrjCKe8/T8goY9MHPA+6JckC3R+/1R9TQKA=")
ORIGIN("questionmarket.com", "3KCO/qN+KmApmfH3RaXAmdR65Z/TRfrr6pds7aDKn1c=")
ORIGIN("3lift.com", "33Xrix7c41Jc9q3InjMWHq+yKVoa/u2IB511kr4X+Ro=")
"""


@pytest.fixture()
def mock_request(monkeypatch):
    def _mocked(*args, **kwargs):
        return BytesIO(TELEMETRY_ORIGIN_DATA_INC.encode())

    monkeypatch.setattr(urllib.request, "urlopen", _mocked)


def test_origins_cli(mock_request, tmp_path):
    output = str(tmp_path / "output")
    runner = CliRunner()
    result = runner.invoke(
        origins.run, ["--output", str(output)], catch_exceptions=False
    )
    assert result.exit_code == 0

    with open(output) as f:
        data = json.load(f)

    assert len(data) == 6
    assert data[0] == {"name": "PAGELOAD", "hash": "PAGELOAD", "index": 0}
    assert data[-2] == {
        "name": "3lift.com",
        "hash": "33Xrix7c41Jc9q3InjMWHq+yKVoa/u2IB511kr4X+Ro=",
        "index": 4,
    }
    assert data[-1] == {"name": "__UNKNOWN__", "hash": "__UNKNOWN__", "index": 5}
