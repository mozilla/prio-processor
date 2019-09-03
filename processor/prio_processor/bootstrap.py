import glob
import logging
import os
from shutil import copyfile

import click
from gcsfs import GCSFileSystem


class LocalFileSystem:
    """Shim for writing files locally."""

    def put(self, src, dst):
        dirname = os.path.dirname(dst)
        os.makedirs(dirname, exist_ok=True)
        copyfile(src, dst)

    def open(self, *args, **kwargs):
        return open(*args, **kwargs)


@click.command()
@click.option(
    "--output",
    type=str,
    required=True,
    help="The output directory for temporary files required by dataproc",
)
@click.option(
    "--credentials",
    type=str,
    envvar="GOOGLE_APPLICATION_CREDENTIALS",
    help="Path to google application credentials",
    required=False,
)
def run(output, credentials):
    """This script uploads the artifacts needed to run the `staging` job."""

    output = output.rstrip("/")
    egg_listing = glob.glob("dist/prio_processor-*.egg")
    if not egg_listing:
        raise RuntimeError("missing bdist_egg artifact")
    if len(egg_listing) > 1:
        raise RuntimeError("there are multiple eggs")

    if output.startswith("gs://"):
        fs = GCSFileSystem(token=credentials)
    else:
        fs = LocalFileSystem()

    egg = egg_listing[0]
    outfile = f"{output}/prio_processor.egg"
    logging.info(f"writing {egg} to {outfile}")
    fs.put(egg, outfile)

    logging.info(f"writing runner.py to {output}/runner.py")
    with fs.open(f"{output}/runner.py", "w") as f:
        f.write("from prio_processor import cli; cli.entry_point()")


if __name__ == "__main__":
    run()
