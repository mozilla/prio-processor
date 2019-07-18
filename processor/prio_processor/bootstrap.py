import click
import glob
import logging

from gcsfs import GCSFileSystem


@click.command()
@click.option(
    "--output",
    type=str,
    required=True,
    help="The output directory for temporary files required by dataproc",
)
@click.option(
    "--token",
    type=str,
    envvar="GOOGLE_APPLICATION_CREDENTIALS",
    help="Path to google application credentials",
    required=False,
)
def run(output, token):
    """This script uploads the artifacts needed to run the `staging` job."""

    output = output.rstrip("/")
    egg_listing = glob.glob("dist/prio_processor-*.egg")
    if not egg_listing:
        raise RuntimeError("missing bdist_egg artifact")
    if len(egg_listing) > 1:
        raise RuntimeError("there are multiple eggs")

    fs = GCSFileSystem(token=token)

    egg = egg_listing[0]
    outfile = f"{output}/prio_processor.egg"
    logging.info(f"writing {egg} to {outfile}")
    fs.put(egg, outfile)

    logging.info(f"writing runner.py to {output}/runner.py")
    with fs.open(f"{output}/runner.py", "w") as f:
        f.write("from prio_processor import staging; staging.run()")


if __name__ == "__main__":
    run()
