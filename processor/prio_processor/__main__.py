import logging
import click
from . import bootstrap, staging, origins, indexing

logging.basicConfig(level=logging.INFO)


@click.group()
def entry_point():
    pass


entry_point.add_command(bootstrap.run, "bootstrap")
entry_point.add_command(staging.run, "staging")
entry_point.add_command(origins.run, "fetch-origins")
entry_point.add_command(indexing.run, "index")
entry_point()
