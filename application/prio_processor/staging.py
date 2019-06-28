import click
import json
import math

from pyspark.sql import SparkSession, Row, functions as F
from pyspark.sql.functions import udf, explode, row_number, lit, col, length
from pyspark.sql.types import StructType, StructField, ArrayType, StringType, MapType
from pyspark.sql.window import Window


def extract(spark, path, date):
    # hour / namespace / type / version / *.ndjson
    path = f"{path}/{date}/*/*/*/*/*"
    return spark.read.text(path)


payload_schema = StructType(
    [
        StructField("id", StringType(), False),
        StructField(
            "prioData",
            ArrayType(
                StructType(
                    [
                        StructField("encoding", StringType(), False),
                        StructField("prio", MapType(StringType(), StringType()), False),
                    ]
                )
            ),
            False,
        ),
    ]
)


@udf(payload_schema)
def extract_payload_udf(ping):
    data = json.loads(ping)
    return Row(id=data["id"], prioData=data["payload"]["prioData"])


def estimate_num_partitions(df, column="prio", partition_size_mb=250):
    size_b = df.select(F.sum(length(column)).alias("size")).collect()[0].size
    return math.ceil(size_b * 1.0 / 10 ** 6 / partition_size_mb)


def transform(data):
    """Flatten nested prioData into a flattened dataframe that is optimally
    partitioned for batched processing in a tool agnostic fashion.

    The dataset is first partitioned by the batch_id, which determines the
    dimension and encoding of the underlying shares. The flattened rows are
    reassigned a new primary key for coordinating messages between servers. The
    dataset is then partitioned by server_id. The partitions for each server
    should contain the same set of join keys.
    """
    df = (
        data.select(extract_payload_udf("value").alias("value"))
        .select("value.*")
        # NOTE: is it worth counting duplicates?
        .dropDuplicates(["id"])
        .withColumn("data", explode("prioData"))
        # drop the id and assign a new one per encoding type
        # this id is used as a join-key during the decoding process
        .select(col("data.encoding").alias("batch_id"), "data.prio")
        .withColumn(
            "id", row_number().over(Window.partitionBy("batch_id").orderBy(lit(0)))
        )
    )

    num_partitions = estimate_num_partitions(df, col("prio")["a"])

    return (
        df.repartitionByRange(num_partitions, "batch_id", "id")
        # explode the values per server
        .select("batch_id", "id", explode("prio").alias("server_id", "payload"))
        # reorder the final columns
        .select("batch_id", "server_id", "id", "payload")
    )


def load(data, output):
    data.write.partitionBy("batch_id", "server_id").json(output, mode="overwrite")


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
