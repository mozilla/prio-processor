import pytest
from pyspark.sql import SparkSession


@pytest.fixture()
def spark():
    spark = SparkSession.builder.master("local").appName("prio").getOrCreate()
    spark.conf.set("spark.sql.session.timeZone", "UTC")
    yield spark
    spark.stop()
