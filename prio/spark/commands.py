from base64 import b64decode, b64encode
from functools import partial

import click
from pyspark.sql import SparkSession
from ..prio import libprio
from ..cli import options
from ..cli.commands import match_server, import_keys, import_public_keys


def create_config(public_key_hex_internal, public_key_hex_external, n_data, batch_id):
    _, public_key_internal, public_key_external = import_public_keys(
        private_key_hex, public_key_hex_internal, public_key_hex_external
    )
    return libprio.PrioConfig_new(
        n_data, public_key_internal, public_key_external, batch_id
    )


def create_server(
    private_key_hex,
    public_key_hex_internal,
    public_key_hex_external,
    n_data,
    batch_id,
    server_id,
    shared_secret,
):
    private_key, public_key_internal, public_key_external = import_keys(
        private_key_hex, public_key_hex_internal, public_key_hex_external
    )
    config = libprio.PrioConfig_new(
        n_data, public_key_internal, public_key_external, batch_id
    )
    return libprio.PrioServer_new(
        config, match_server(server_id), private_key, b64decode(shared_secret)
    )


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

    broadcast_config_func = spark.sparkContext.broadcast(
        partial(
            create_config,
            public_key_hex_internal,
            public_key_hex_external,
            n_data,
            batch_id,
        )
    )
    broadcast_server_func = spark.sparkContext.broadcast(
        partial(
            create_server,
            private_key_hex,
            public_key_hex_internal,
            public_key_hex_external,
            n_data,
            batch_id,
            server_id,
            shared_secret,
        )
    )

    # NOTE: jump into a session with spark started for testing
    import code

    code.interact(local=locals())


@click.group()
def main():
    pass


main.add_command(prio_spark)

if __name__ == "__main__":
    main()
