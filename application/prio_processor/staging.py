import click

import apache_beam as beam
from apache_beam.io import ReadFromText, WriteToText
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions


class PrioPingTransform(beam.PTransform):
    """A transform for preprocessing Prio pings"""

    def expand(self, pings):
        return pings


@click.command()
@click.option("--date", type=str, required=True)
@click.option("--input", type=str, required=True)
@click.option("--output", type=str, required=True)
@click.argument("pipeline_args", nargs=-1, type=click.UNPROCESSED)
def run(date, input, output, pipeline_args):
    options = PipelineOptions(pipeline_args)
    # propagate global context like imports
    options.view_as(SetupOptions).save_main_session = True
    with beam.Pipeline(options=options) as p:
        data = p | f"Read: {input}" >> ReadFromText(f"{input}/{date}/**/*.ndjson")
        processed = data | PrioPingTransform()
        processed | f"Write: {output}" >> WriteToText(output, ".njson")


if __name__ == "__main__":
    run()
