import gzip
import json
import math
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import click
from pyspark.sql import DataFrame, Row, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import col, explode, length, lit, row_number, udf, unbase64
from pyspark.sql.types import (
    ArrayType,
    ByteType,
    MapType,
    StringType,
    StructField,
    StructType,
)
from pyspark.sql.window import Window


class ExtractPrioPing(ABC):
    payload_schema = StructType(
        [
            StructField("id", StringType(), True),
            StructField(
                "prioData",
                ArrayType(
                    StructType(
                        [
                            StructField("encoding", StringType(), True),
                            StructField(
                                "prio", MapType(StringType(), StringType()), True
                            ),
                        ]
                    )
                ),
                True,
            ),
        ]
    )

    def __init__(self, spark: SparkSession, materialization_project: str):
        self.spark = spark
        self.materialization_project = materialization_project

    @staticmethod
    def estimate_num_partitions(
        df: DataFrame, column: str = "prio", partition_size_mb: int = 250
    ) -> int:
        """Given a column in a dataframe, determine how many partitions to
        create. The colum is assumed to comprise most of the size of the dataset
        e.g. the share for server A is much greater than the metadata like the
        uuid and batch_id.
        """
        size_b = df.select(F.sum(length(column)).alias("size")).collect()[0].size or 0
        return math.ceil(size_b * 1.0 / 10 ** 6 / partition_size_mb)

    @abstractmethod
    def extract(self, path: str, date: str) -> DataFrame:
        pass

    def transform(self, data: DataFrame) -> DataFrame:
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

        num_partitions = self.estimate_num_partitions(df, col("prio")["a"])

        return (
            df.repartitionByRange(num_partitions, "batch_id", "id")
            # explode the values per server
            .select("batch_id", "id", explode("prio").alias("server_id", "payload"))
            # reorder the final columns
            .select("batch_id", "server_id", "id", "payload")
        )

    def load(self, data: DataFrame, output: str, date: str):
        """Write the results of the transformed data to storage."""
        data.withColumn("submission_date", lit(date)).write.partitionBy(
            "submission_date", "server_id", "batch_id"
        ).json(output, mode="overwrite")


class CloudStorageExtract(ExtractPrioPing):
    @staticmethod
    @udf(ExtractPrioPing.payload_schema)
    def extract_payload_udf(ping: str) -> Row:
        data = json.loads(ping)
        return Row(id=data["id"], prioData=data["payload"]["prioData"])

    def extract(self, path: str, date: str) -> DataFrame:
        """Extract data from the moz-fx-data bucket that has been decoded by
        the gcp-ingestion stack. The messages are newline-delimited json
        documents representing PubSub messages (refer to the `prio_ping` test
        fixture for implementation details).

        The directory hierarchy encodes the purpose for each folder as follows:
            date / hour / namespace / type / version / *.ndjson
        """
        # The raw message also contains a field named attributeMap: Map[str,
        # str], but is safely ignored in this processing job
        pubsub_schema = StructType([StructField("payload", StringType(), False)])

        path = f"{path}/{date}/*/*/*/*"
        df = self.spark.read.json(path, schema=pubsub_schema)
        return df.select(
            self.extract_payload_udf(unbase64(col("payload"))).alias("extracted")
        ).select("extracted.*")


class BigQueryStorageExtract(ExtractPrioPing):
    @staticmethod
    def date_add(date_ds: str, days: int) -> str:
        fmt = "%Y-%m-%d"
        dt = datetime.strptime(date_ds, fmt)
        return datetime.strftime(dt + timedelta(days), fmt)

    @staticmethod
    @udf(ExtractPrioPing.payload_schema)
    def extract_payload_udf(ping: bytes) -> Row:
        data = json.loads(gzip.decompress(ping).decode("utf-8"))
        return Row(id=data["id"], prioData=data["payload"]["prioData"])

    def extract(self, table: str, date: str) -> DataFrame:
        """Extract data from the payload_bytes_decoded BigQuery table."""
        df = (
            self.spark.read.format("bigquery")
            .option("table", table)
            .option(
                "filter",
                f"submission_timestamp >= '{date}'"
                f" AND submission_timestamp < '{self.date_add(date, 1)}'",
            )
            .load()
        )
        return df.select(
            self.extract_payload_udf(col("payload")).alias("extracted")
        ).select("extracted.*")


class BigQueryStorageExtractStructured(ExtractPrioPing):
    def extract(self, table: str, date: str) -> DataFrame:
        """Extract data from the structured ingestion BigQuery table.

        This assumes the job runs in moz-fx-data-shared-prod or mozdata, where
        there is a `tmp` dataset for miscellaneous queries like this.
        """

        self.spark.conf.set("viewsEnabled", "true")
        self.spark.conf.set("materializationDataset", "tmp")
        if self.materialization_project:
            self.spark.conf.set("materializationProject", self.materialization_project)

        sql = f"""
        WITH deduped AS (
            SELECT
                id,
                array_agg(payload)[offset(0)] AS payload,
            FROM
                `{table}`
            WHERE
                date(submission_timestamp) = "{date}"
            GROUP BY
                1
        ),
        extracted AS (
            SELECT
                -- reassign the id for partitioning
                sha256(prio_data.prio.a) as id,
                prio_data.encoding AS batch_id,
                prio_data.prio AS payload
            FROM
                deduped,
                UNNEST(payload.prio_data) prio_data
        ),
        a AS (
            SELECT
                id,
                batch_id,
                'a' AS server_id,
                payload.a AS payload
            FROM
                extracted
        ),
        b AS (
            SELECT
                id,
                batch_id,
                'b' AS server_id,
                payload.b AS payload
            FROM
                extracted
        ),
        unioned AS (
            SELECT * FROM a
            UNION ALL
            SELECT * FROM b
        )
        SELECT
            id,
            batch_id,
            server_id,
            payload
        FROM
            unioned
        ORDER BY
            batch_id,
            server_id
        """
        print("Running query to be materialized:")
        print(sql)
        df = self.spark.read.format("bigquery").load(sql)

    def transform(self, data: DataFrame) -> DataFrame:
        """Transform the data to be written out in ranged partitions.

        The data has already been exploded where there is one unique identifier
        for each share.
        """
        num_partitions = self.estimate_num_partitions(
            data.where("server_id = 'a'"), "a"
        )

        return (
            data.repartitionByRange(num_partitions, "batch_id", "id")
            # reorder the final columns
            .select("batch_id", "server_id", "id", "payload")
        )


@click.command()
@click.option(
    "--date",
    type=str,
    required=True,
    help="The submission date for filtering in YYYY-MM-DD format",
)
@click.option(
    "--input",
    type=str,
    required=True,
    help="The fully-qualified GCS path or BigQuery table name",
)
@click.option("--output", type=str, required=True, help="Output path")
@click.option(
    "--source",
    type=click.Choice(["gcs", "bigquery", "bigquery-structured"]),
    default="gcs",
    help="The storage location for reading raw prio pings",
)
@click.option(
    "--credentials",
    type=str,
    envvar="GOOGLE_APPLICATION_CREDENTIALS",
    help="Path to google application credentials",
    required=False,
)
@click.option(
    "--materialization-project",
    type=str,
    help="Name of the project used for dataset materialization in BigQuery. Project should have a tmp dataset.",
)
def run(date, input, output, source, credentials, materialization_project):
    spark = SparkSession.builder.getOrCreate()
    spark.conf.set("fs.gs.implicit.dir.repair.enable", False)
    spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
    if credentials:
        spark.conf.set("credentialsFile", credentials)

    extract_method = {
        "gcs": CloudStorageExtract,
        "bigquery": BigQueryStorageExtract,
        "bigquery-structured": BigQueryStorageExtractStructured,
    }

    transformer = extract_method[source](spark, materialization_project)
    pings = transformer.extract(input, date)
    processed = transformer.transform(pings)
    transformer.load(processed, output, date)


if __name__ == "__main__":
    run()
