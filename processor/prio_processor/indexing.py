"""Map prio-aggregated data to their origins."""
import click
import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, explode
from pyspark.sql.types import (
    ArrayType,
    StructType,
    StructField,
    StringType,
    IntegerType,
)
from jsonschema import validate


def validate_origins(origins):
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "hash": {"type": "string"},
                "index": {"type": "integer", "minimum": 0},
            },
        },
    }
    validate(instance=origins, schema=schema)


def extract(spark, input):
    return spark.read.json(input)


def transform(aggregates, config, origins):
    @udf(
        ArrayType(
            StructType(
                [
                    StructField("batch_id", StringType(), False),
                    StructField("origin", StringType(), False),
                    StructField("hash", StringType(), False),
                    StructField("index", IntegerType(), False),
                    StructField("aggregate", IntegerType(), False),
                ]
            )
        )
    )
    def _apply_structure(batch_id, payload):
        """Create a user-defined function that maps partitioned batch-ids into
        rows containing all the necessary information."""

        # assumption: hyphens are used to define a partition of origins
        if batch_id not in config:
            return []

        # currently all batch-ids contain a single hyphen with 2 parts
        split = batch_id.split("-")
        batch_id = split[0]
        part_num = int(split[1])

        if part_num == 0:
            offset = 0
        elif part_num == 1:
            offset = config[f"{batch_id}-0"]
        else:
            # Hard-fail, this code path should not occur if the config file is
            # being properly maintained.
            raise NotImplementedError("batch-id is split into more than 2 parts")

        result = []
        for origin, aggregate in zip(origins[offset:], payload):
            row = (batch_id, origin["name"], origin["hash"], origin["index"], aggregate)
            result.append(row)
        return result

    return aggregates.withColumn(
        "indexed", explode(_apply_structure("batch_id", "payload"))
    ).select("submission_date", "id", "timestamp", "indexed.*")


def load(df, output):
    df.repartition(1).write.json(output)


@click.command()
@click.option(
    "--input", type=str, required=True, help="location of the prio aggregated-data"
)
@click.option(
    "--output", type=str, required=True, help="location of the resulting indexed data"
)
@click.option(
    "--config",
    type=str,
    required=True,
    help="location of the whitelist of batch-ids and their sizes",
)
@click.option(
    "--origins", type=str, required=True, help="JSON document with origins data"
)
def run(input, output, config, origins):
    spark = SparkSession.builder.getOrCreate()
    extracted = extract(spark, input)

    with open(config) as f:
        config_data = json.load(f)
    with open(origins) as f:
        origin_data = json.load(f)

    validate_origins(origin_data)

    transformed = transform(extracted, config_data, origin_data)
    load(transformed, output)


if __name__ == "__main__":
    run()
