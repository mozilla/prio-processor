from base64 import b64decode, b64encode
from ..prio import libprio

from pyspark.sql.functions import udf
from pyspark.sql.types import BinaryType

# TODO
def verify1(server_cb, input):
    pass


# TODO
def verify2(config_cb, server_cb, input: str, input_internal: str, input_external: str):
    pass


# TODO: pandas UDF
def aggregate(config_cb, server_cb, input_df):
    pass


# TODO
def publish(config_cb, server_id, input_internal, input_external):
    pass
