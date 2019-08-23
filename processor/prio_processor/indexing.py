"""Map prio-aggregated data to their origins."""
import click
from pyspark.sql import SparkSession


def extract(spark, input, origin_file):
    aggregates = spark.read.json(input)
    origins = spark.read.json(origin_file)
    return aggregates, origins


def transform(aggregates, origins):
    pass


def load(df, output):
    pass


@click.command()
@click.option(
    "--input", type=str, required=True, help="location of the prio aggregated-data"
)
@click.option("--output", type=str, required=True, help="location of the indexed data")
@click.option(
    "--origin-file", type=str, required=True, help="JSON document with origins data"
)
def run(input, output, origin_file):
    transformed = transform(*extract(input))
    load(transformed, output)


if __name__ == "__main__":
    run()
