import click
import array
import json
import os
from base64 import b64decode, b64encode
from uuid import uuid4
from functools import partial

import dask.dataframe as dd
import dask.bag as db
import dask
import numpy as np

from .. import libprio
from .. import prio

from .options import (
    data_config,
    server_config,
    input_1,
    input_2,
    output_1,
    output_2,
    public_key,
)


def import_public_keys(public_key_hex_internal, public_key_hex_external):
    return (
        libprio.PublicKey_import_hex(public_key_hex_internal),
        libprio.PublicKey_import_hex(public_key_hex_external),
    )


def import_keys(private_key_hex, public_key_hex_internal, public_key_hex_external):
    return (
        libprio.PrivateKey_import_hex(private_key_hex, public_key_hex_internal),
        *import_public_keys(public_key_hex_internal, public_key_hex_external),
    )


def match_server(server_id):
    return libprio.PRIO_SERVER_A if server_id == "A" else libprio.PRIO_SERVER_B


def create_config(public_key_hex_internal, public_key_hex_external, n_data, batch_id):
    public_key_internal = prio.PublicKey().import_hex(public_key_hex_internal)
    public_key_external = prio.PublicKey().import_hex(public_key_hex_external)
    return prio.Config(n_data, public_key_internal, public_key_external, batch_id)


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
@output_2
@click.option("--size", type=int, help="Number of elements in the dataset.")
def random_shares(
    batch_id,
    n_data,
    public_key_hex_internal,
    public_key_hex_external,
    output_a,
    output_b,
    size,
):
    """Generate random shares drawn from a bernoulli distribution."""

    @dask.delayed(pure=False)
    def random_share():
        data = np.packbits(np.random.binomial(1, 0.5, n_data)).tobytes()
        libprio.Prio_init()
        config = create_config(
            public_key_hex_external, public_key_hex_internal, n_data, batch_id
        )
        shares = prio.Client(config).encode(data)
        libprio.Prio_clear()
        b64shares = [b64encode(share).decode() for share in shares]
        return str(uuid4()), b64shares[0], b64shares[1]

    results = dask.delayed(random_share() for _ in range(size))
    bag = db.from_delayed(results)
    df = bag.to_dataframe(meta=[("id", str), ("a", str), ("b", str)])
    df[["id", "a"]].rename(columns={"a": "payload"}).to_json(output_a)
    df[["id", "a"]].rename(columns={"a": "payload"}).to_json(output_b)


@click.command()
@data_config
@public_key
@input_1
@output_2
def encode_shares(
    batch_id,
    n_data,
    public_key_hex_internal,
    public_key_hex_external,
    input,
    output_a,
    output_b,
):
    public_key_internal, public_key_external = import_public_keys(
        public_key_hex_internal, public_key_hex_external
    )
    config = libprio.PrioConfig_new(
        n_data, public_key_internal, public_key_external, batch_id
    )

    with open(input) as f:
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
    private_key_hex,
    shared_secret,
    public_key_hex_internal,
    public_key_hex_external,
    input,
    output,
):
    """Decode a batch of shares"""
    click.echo("Running verify1")

    private_key, public_key_internal, public_key_external = import_keys(
        private_key_hex, public_key_hex_internal, public_key_hex_external
    )

    config = libprio.PrioConfig_new(
        n_data, public_key_internal, public_key_external, batch_id
    )
    server = libprio.PrioServer_new(
        config, match_server(server_id), private_key, b64decode(shared_secret)
    )
    verifier = libprio.PrioVerifier_new(server)
    packet = libprio.PrioPacketVerify1_new()

    with open(input) as f:
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
@input_1
@input_2
@output_1
def verify2(
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
    """Verify a batch of SNIPs"""
    click.echo("Running verify2")

    private_key, public_key_internal, public_key_external = import_keys(
        private_key_hex, public_key_hex_internal, public_key_hex_external
    )

    config = libprio.PrioConfig_new(
        n_data, public_key_internal, public_key_external, batch_id
    )
    server = libprio.PrioServer_new(
        config, match_server(server_id), private_key, b64decode(shared_secret)
    )
    verifier = libprio.PrioVerifier_new(server)

    packet1_internal = libprio.PrioPacketVerify1_new()
    packet1_external = libprio.PrioPacketVerify1_new()
    packet = libprio.PrioPacketVerify2_new()

    with open(input) as f:
        data = map(json.loads, f.readlines())
    with open(input_internal) as f:
        data_internal = map(json.loads, f.readlines())
    with open(input_external) as f:
        data_external = map(json.loads, f.readlines())

    # Create an index for matching shares to corresponding verification packets.
    internal_index = {d["id"]: d["payload"] for d in data_internal}
    external_index = {d["id"]: d["payload"] for d in data_external}

    name = os.path.basename(input_internal)
    outfile = os.path.join(output, name)
    with open(outfile, "w") as f:
        for datum in data:
            share = b64decode(datum["payload"])
            internal = b64decode(internal_index[datum["id"]])
            external = b64decode(external_index[datum["id"]])

            libprio.PrioVerifier_set_data(verifier, share)
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
@input_1
@input_2
@output_1
def aggregate(
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
    """Generate an aggregate share from a batch of verified SNIPs"""
    click.echo("Running aggregate")

    private_key, public_key_internal, public_key_external = import_keys(
        private_key_hex, public_key_hex_internal, public_key_hex_external
    )

    config = libprio.PrioConfig_new(
        n_data, public_key_internal, public_key_external, batch_id
    )
    server = libprio.PrioServer_new(
        config, match_server(server_id), private_key, b64decode(shared_secret)
    )
    verifier = libprio.PrioVerifier_new(server)

    packet2_internal = libprio.PrioPacketVerify2_new()
    packet2_external = libprio.PrioPacketVerify2_new()

    with open(input) as f:
        data = map(json.loads, f.readlines())
    with open(input_internal) as f:
        data_internal = map(json.loads, f.readlines())
    with open(input_external) as f:
        data_external = map(json.loads, f.readlines())

    # Create an index for matching shares to corresponding verification packets.
    internal_index = {d["id"]: d["payload"] for d in data_internal}
    external_index = {d["id"]: d["payload"] for d in data_external}

    for datum in data:
        share = b64decode(datum["payload"])
        internal = b64decode(internal_index[datum["id"]])
        external = b64decode(external_index[datum["id"]])

        libprio.PrioVerifier_set_data(verifier, share)
        libprio.PrioPacketVerify2_read(packet2_internal, internal, config)
        libprio.PrioPacketVerify2_read(packet2_external, external, config)
        try:
            libprio.PrioVerifier_isValid(verifier, packet2_internal, packet2_external)
        except RuntimeError:
            # the current packet is invalid
            continue
        libprio.PrioServer_aggregate(server, verifier)

    name = os.path.basename(input_internal)
    outfile = os.path.join(output, name)
    with open(outfile, "w") as f:
        shares = libprio.PrioTotalShare_new()
        libprio.PrioTotalShare_set_data(shares, server)
        data = libprio.PrioTotalShare_write(shares)
        json.dump(b64encode(data).decode(), f)


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
    private_key_hex,
    shared_secret,
    public_key_hex_internal,
    public_key_hex_external,
    input_internal,
    input_external,
    output,
):
    """Generate a final aggregate and remap data to a content blocklist"""
    click.echo("Running publish")

    _, public_key_internal, public_key_external = import_keys(
        private_key_hex, public_key_hex_internal, public_key_hex_external
    )

    config = libprio.PrioConfig_new(
        n_data, public_key_internal, public_key_external, batch_id
    )

    with open(input_internal) as f:
        data_internal = b64decode(json.load(f))
    with open(input_external) as f:
        data_external = b64decode(json.load(f))

    share_internal = libprio.PrioTotalShare_new()
    share_external = libprio.PrioTotalShare_new()

    libprio.PrioTotalShare_read(share_internal, data_internal, config)
    libprio.PrioTotalShare_read(share_external, data_external, config)

    # ordering matters
    if match_server(server_id) == libprio.PRIO_SERVER_B:
        share_internal, share_external = share_external, share_internal

    final = libprio.PrioTotalShare_final(config, share_internal, share_external)
    final = list(array.array("L", final))

    name = os.path.basename(input_internal)
    outfile = os.path.join(output, name)
    with open(outfile, "w") as f:
        json.dump(final, f)
