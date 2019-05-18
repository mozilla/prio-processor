from base64 import b64decode, b64encode
from ..prio import libprio
from pyspark.sql import SparkSession


def verify1(df):
    pass


def verify2(df):
    pass


def aggregate(df):
    pass


def publish(df):
    pass


import click
from ..cli import options
from ..cli.commands import match_server, import_keys


@click.command()
@options.data_config
@options.server_config
@options.public_key
@options.input_1
@options.input_2
@options.output_1
def prio_spark(
    batch_id,
    n_data,
    server_id,
    private_key_hex,
    shared_secret,
    public_key_hex_internal,
    public_key_hex_external,
    input,
    input_internal,
    input_external,
    output,
):
    spark = SparkSession.builder.appName("prio").getOrCreate()

    def create_config():
        private_key, public_key_internal, public_key_external = import_keys(
            private_key_hex, public_key_hex_internal, public_key_hex_external
        )
        return libprio.PrioConfig_new(
            n_data, public_key_internal, public_key_external, batch_id
        )

    def create_server():
        config = create_config()
        return libprio.PrioServer_new(
            config, match_server(server_id), private_key, b64decode(shared_secret)
        )

    config_var = spark.sparkContext.broadcast(create_config)
    server_var = spark.sparkContext.broadcast(create_server)

    import code

    code.interact(local=locals())


@click.group()
def main():
    pass


main.add_command(prio_spark)

if __name__ == "__main__":
    main()
