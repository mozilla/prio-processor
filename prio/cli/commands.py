import click
import json
import os
from base64 import b64decode, b64encode
from uuid import uuid4

from .. import libprio
from .options import (
    data_config,
    server_config,
    input_1,
    input_2,
    output_1,
    output_2,
    public_key,
)


@click.command()
def shared_seed():
    """Generate a shared server secret in base64."""
    seed = libprio.PrioPRGSeed_randomize()
    click.echo(b64encode(seed))


@click.command()
def keygen():
    """Generate a curve25519 key pair as json."""
    private, public = libprio.Keypair_new()
    private_hex = libprio.PrivateKey_export_hex(private).decode("utf-8")[:-1]
    public_hex = libprio.PublicKey_export_hex(public).decode("utf-8")[:-1]
    data = json.dumps({"private_key": private_hex, "public_key": public_hex})
    click.echo(data)


@click.command()
@data_config
@public_key
@input_1
@output_2
def encode_shares(
    batch_id,
    n_data,
    public_key_internal,
    public_key_external,
    input,
    output_a,
    output_b,
):
    public_key_internal = libprio.PublicKey_import_hex(public_key_internal)
    public_key_external = libprio.PublicKey_import_hex(public_key_external)
    config = libprio.PrioConfig_new(
        n_data, public_key_internal, public_key_external, batch_id
    )

    data = []
    with open(input, "r") as f:
        for line in f.readlines():
            data.append(json.loads(line))

    name = os.path.basename(input)
    path_a = os.path.join(output_a, name)
    path_b = os.path.join(output_b, name)
    with open(path_a, "w") as fp_a, open(path_b, "w") as fp_b:
        for datum in data:
            share_a, share_b = libprio.PrioClient_encode(config, bytes(datum))
            json.dump(
                {"id": str(uuid4()), "payload": b64encode(share_a).decode()}, fp_a
            )
            json.dump(
                {"id": str(uuid4()), "payload": b64encode(share_b).decode()}, fp_b
            )


@click.command()
@data_config
@server_config
@public_key
@input_1
@output_2
def verify1():
    """Decode a batch of shares"""
    click.echo("Running verify1")


@click.command()
@data_config
@server_config
@public_key
@input_2
@output_1
def verify2():
    """Verify a batch of SNIPs"""
    click.echo("Running verify2")


@click.command()
@data_config
@server_config
@public_key
@input_2
@output_1
def aggregate():
    """Generate an aggregate share from a batch of verified SNIPs"""
    click.echo("Running aggregate")


@click.command()
@data_config
@server_config
@public_key
@input_2
@output_1
def publish():
    """Generate a final aggregate and remap data to a content blocklist"""
    click.echo("Running publish")
