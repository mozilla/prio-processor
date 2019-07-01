import click
import json
import math

from pyspark.sql import SparkSession, Row, functions as F
from pyspark.sql.functions import udf, explode, row_number, lit, col, length, unbase64
from pyspark.sql.types import StructType, StructField, ArrayType, StringType, MapType, ByteType
from pyspark.sql.window import Window

# The raw message also contains a field named attributeMap: Map[str, str], but
# is safely ignored in this processing job
pubsub_schema = StructType([StructField("payload", StringType(), False)])

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


def extract(spark, path, date):
    """Extract data from the moz-fx-data bucket that has been decoded by
    the gcp-ingestion stack. The messages are newline-delimited json documents
    representing PubSub messages (refer to the `prio_ping` test fixture for
    implementation details).

    The directory hierarchy encodes the purpose for each folder as follows:
        date / hour / namespace / type / version / *.ndjson
    """
    path = f"{path}/{date}/*/*/*/*"
    df = spark.read.json(path, schema=pubsub_schema)
    return (
        df
        .select(extract_payload_udf(unbase64(col("payload"))).alias("extracted"))
        .select("extracted.*")
    )


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
        data
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


def load(data, output, date):
    data.withColumn("submission_date", lit(date)).write.partitionBy(
        "submission_date", "batch_id", "server_id"
    ).json(output, mode="overwrite")


@click.command()
@click.option("--date", type=str, required=True)
@click.option("--input", type=str, required=True)
@click.option("--output", type=str, required=True)
def run(date, input, output):
    spark = SparkSession.builder.getOrCreate()
    spark.conf.set("fs.gs.implicit.dir.repair.enable", False)
    pings = extract(spark, input, date)
    processed = transform(pings)
    load(processed, output, date)


if __name__ == "__main__":
    run()
