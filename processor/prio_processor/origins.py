import click
import urllib.request
from collections import namedtuple
import json

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
    resp = urllib.request.urlopen(url)
    parsed = map(eval, filter(ignore, resp.readlines()))
    data = [transform(idx, origin) for idx, origin in enumerate(parsed)]
    output.write(json.dumps(data, indent=2))


if __name__ == "__main__":
    run()
