import json
import urllib.request
from collections import namedtuple

import click

TELEMETRY_ORIGIN_DATA = "https://hg.mozilla.org/mozilla-central/raw-file/tip/toolkit/components/telemetry/core/TelemetryOriginData.inc"
ORIGIN = namedtuple("Origin", ["name", "hash"])


def ignore(line):
    return not (line.startswith(b"//") or not line.strip())


def transform(index, origin):
    return {"name": origin.name, "hash": origin.hash, "index": index}


@click.command()
@click.option("--url", type=str, default=TELEMETRY_ORIGIN_DATA)
@click.option("--output", type=click.File("w"), default="-")
def run(url, output):
    """Fetch data about origins being collected by Firefox telemetry via Prio."""
    resp = urllib.request.urlopen(url)
    parsed = map(eval, filter(ignore, resp.readlines()))
    data = [transform(idx, origin) for idx, origin in enumerate(parsed)]

    # in-band metadata about origin telemetry
    # https://searchfox.org/mozilla-central/rev/325c1a707819602feff736f129cb36055ba6d94f/toolkit/components/telemetry/core/TelemetryOrigin.cpp#145-149
    data.append(
        {"name": "__UNKNOWN__", "hash": "__UNKNOWN__", "index": data[-1]["index"] + 1}
    )
    output.write(json.dumps(data, indent=2))


if __name__ == "__main__":
    run()
