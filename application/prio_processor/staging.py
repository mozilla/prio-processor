import click

import apache_beam as beam
from apache_beam.io import ReadFromText, WriteToText
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions


class PrioPingTransform(beam.PTransform):
    """A transform for preprocessing Prio pings"""

    def expand(self, pings):
        return pings


@click.command()
@click.option("--input", type=str, required=True)
@click.option("--output", type=str, required=True)
def run(**kwargs):
    options = PipelineOptions.from_dictionary(kwargs)
    # propagate global context like imports
    options.view_as(SetupOptions).save_main_session = True
    with beam.Pipeline(options=options) as p:
        data = p | f"Read: {p.options.input}" >> ReadFromText(p.options.input)
        processed = data | PrioPingTransform()
        processed | f"Write: {p.options.output}" >> WriteToText(p.options.output)


if __name__ == "__main__":
    run()
