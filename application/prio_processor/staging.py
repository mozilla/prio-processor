import click

from pyspark.sql import SparkSession


def extract(spark, path, date):
    # hour / namespace / type / version / *.ndjson
    path = f"{path}/{date}/*/*/*/*/*"
    return spark.read.text(path)


def transform(data):
    return data


def load(data, output):
    data.write.json(output)


@click.command()
@click.option("--date", type=str, required=True)
@click.option("--input", type=str, required=True)
@click.option("--output", type=str, required=True)
def run(date, input, output):
    spark = SparkSession.builder.getOrCreate()
    pings = extract(spark, input, date)
    processed = transform(pings)
    load(processed, output)


if __name__ == "__main__":
    run()
