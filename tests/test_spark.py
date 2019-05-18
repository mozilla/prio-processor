import pytest
from pyspark.sql import SparkSession


@pytest.fixture()
def spark():
    spark = SparkSession.builder.master("local").appName("prio").getOrCreate()
    spark.conf.set("spark.sql.session.timeZone", "UTC")
    yield spark
    spark.stop()


def test_transform_verify1():
    raise NotImplementedError


def test_transform_verify2():
    raise NotImplementedError


def test_transform_aggregate():
    raise NotImplementedError


def test_transform_publish():
    raise NotImplementedError
