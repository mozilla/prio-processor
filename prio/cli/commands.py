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

    with open(input, "r") as f:
        data = map(json.loads, f.readlines())

    name = os.path.basename(input)
    path_a = os.path.join(output_a, name)
    path_b = os.path.join(output_b, name)
    with open(path_a, "w") as fp_a, open(path_b, "w") as fp_b:
        for datum in data:
            share_a, share_b = libprio.PrioClient_encode(config, bytes(datum))
            uid = str(uuid4())
            json.dump({"id": uid, "payload": b64encode(share_a).decode()}, fp_a)
            fp_a.write("\n")
            json.dump({"id": uid, "payload": b64encode(share_b).decode()}, fp_b)
            fp_b.write("\n")


@click.command()
@data_config
@server_config
@public_key
@input_1
@output_1
def verify1(
    batch_id,
    n_data,
    server_id,
    private_key,
    shared_secret,
    public_key_internal,
    public_key_external,
    input,
    output,
):
    """Decode a batch of shares"""
    click.echo("Running verify1")

    private_key = libprio.PrivateKey_import_hex(private_key, public_key_internal)
    public_key_internal = libprio.PublicKey_import_hex(public_key_internal)
    public_key_external = libprio.PublicKey_import_hex(public_key_external)
    server_id = libprio.PRIO_SERVER_A if server_id == "A" else libprio.PRIO_SERVER_B
    shared_secret = b64decode(shared_secret)

    config = libprio.PrioConfig_new(
        n_data, public_key_internal, public_key_external, batch_id
    )
    server = libprio.PrioServer_new(config, server_id, private_key, shared_secret)
    verifier = libprio.PrioVerifier_new(server)
    packet = libprio.PrioPacketVerify1_new()

    with open(input, "r") as f:
        data = map(json.loads, f.readlines())

    name = os.path.basename(input)
    outfile = os.path.join(output, name)
    with open(outfile, "w") as f:
        for datum in data:
            share = b64decode(datum["payload"])
            libprio.PrioVerifier_set_data(verifier, share)
            libprio.PrioPacketVerify1_set_data(packet, verifier)
            packet_data = libprio.PrioPacketVerify1_write(packet)
            datum["payload"] = b64encode(packet_data).decode()
            json.dump(datum, f)
            f.write("\n")


@click.command()
@data_config
@server_config
@public_key
@input_2
@output_1
def verify2(
    batch_id,
    n_data,
    server_id,
    private_key,
    shared_secret,
    public_key_internal,
    public_key_external,
    input_internal,
    input_external,
    output,
):
    """Verify a batch of SNIPs"""
    click.echo("Running verify2")

    private_key = libprio.PrivateKey_import_hex(private_key, public_key_internal)
    public_key_internal = libprio.PublicKey_import_hex(public_key_internal)
    public_key_external = libprio.PublicKey_import_hex(public_key_external)
    server_id = libprio.PRIO_SERVER_A if server_id == "A" else libprio.PRIO_SERVER_B
    shared_secret = b64decode(shared_secret)

    config = libprio.PrioConfig_new(
        n_data, public_key_internal, public_key_external, batch_id
    )
    server = libprio.PrioServer_new(config, server_id, private_key, shared_secret)
    verifier = libprio.PrioVerifier_new(server)

    packet1_internal = libprio.PrioPacketVerify1_new()
    packet1_external = libprio.PrioPacketVerify1_new()
    packet = libprio.PrioPacketVerify2_new()

    with open(input_internal, "r") as f:
        data_internal = map(json.loads, f.readlines())
    with open(input_internal, "r") as f:
        data_external = map(json.loads, f.readlines())

    # Create an index for matching internal payloads to external payloads. This
    # acts as an in-memory hash join on id.
    external_index = {d["id"]: d["payload"] for d in data_external}

    name = os.path.basename(input_internal)
    outfile = os.path.join(output, name)
    with open(outfile, "w") as f:
        for datum in data_internal:
            internal = b64decode(datum["payload"])
            external = b64decode(external_index[datum["id"]])

            libprio.PrioPacketVerify1_read(packet1_internal, internal, config)
            libprio.PrioPacketVerify1_read(packet1_external, external, config)

            libprio.PrioPacketVerify2_set_data(
                packet, verifier, packet1_internal, packet1_external
            )
            packet_data = libprio.PrioPacketVerify2_write(packet)
            datum["payload"] = b64encode(packet_data).decode()
            json.dump(datum, f)
            f.write("\n")


@click.command()
@data_config
@server_config
@public_key
@input_2
@output_1
def aggregate(
    batch_id,
    n_data,
    server_id,
    private_key,
    shared_secret,
    public_key_internal,
    public_key_external,
    input_internal,
    input_external,
    output,
):
    """Generate an aggregate share from a batch of verified SNIPs"""
    click.echo("Running aggregate")


@click.command()
@data_config
@server_config
@public_key
@input_2
@output_1
def publish(
    batch_id,
    n_data,
    server_id,
    private_key,
    shared_secret,
    public_key_internal,
    public_key_external,
    input_internal,
    input_external,
    output,
):
    """Generate a final aggregate and remap data to a content blocklist"""
    click.echo("Running publish")
