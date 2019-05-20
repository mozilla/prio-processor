import pytest
from pyspark.sql import SparkSession


@pytest.fixture()
def spark():
    spark = SparkSession.builder.master("local").appName("prio").getOrCreate()
    spark.conf.set("spark.sql.session.timeZone", "UTC")
    yield spark
    spark.stop()


def test_function_verify1():
    raise NotImplementedError


def test_function_verify2():
    raise NotImplementedError


def test_function_aggregate():
    raise NotImplementedError


def test_function_publish():
    raise NotImplementedError
