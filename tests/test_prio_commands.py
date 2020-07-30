from base64 import b64decode, b64encode
import fileinput
import json
import os
import pytest
from pathlib import Path
from click.testing import CliRunner
from prio_processor.prio import commands


@pytest.fixture()
def root():
    return Path(__file__).parent / "resources" / "cli"


@pytest.fixture()
def server_a_args(root):
    config = json.loads((root / "config.json").read_text())
    server_a_keys = json.loads((root / "server_a_keys.json").read_text())
    server_b_keys = json.loads((root / "server_b_keys.json").read_text())
    shared_seed = json.loads((root / "shared_seed.json").read_text())
    return [
        "--server-id",
        "A",
        "--private-key-hex",
        server_a_keys["private_key"],
        "--shared-secret",
        shared_seed["shared_seed"],
        "--public-key-hex-internal",
        server_a_keys["public_key"],
        "--public-key-hex-external",
        server_b_keys["public_key"],
        "--n-data",
        config["n_data"],
        "--batch-id",
        config["batch_id"],
    ]


def test_verify1(tmp_path, root, server_a_args):
    output = tmp_path
    result = CliRunner().invoke(
        commands.verify1,
        server_a_args
        + [
            "--input",
            str(root / "server_a" / "raw" / "data.ndjson"),
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0, result.stdout_bytes
    expect = (
        (root / "server_a" / "intermediate" / "internal" / "verify1" / "data.ndjson")
        .read_text()
        .strip()
    )
    actual = (output / "data.ndjson").read_text().strip()
    # NOTE: due to the non-determinstic behavior of generating the verification
    # circuit, we can only compare the relative size of the packets (or
    # otherwise go through the rest of the protocol run). On macOS, the packets
    # are the same, but on linux the packets are different. There is some
    # behavior difference in NSS that occurs between platforms.
    index = {
        item["id"]: item["payload"] for item in map(json.loads, expect.split("\n"))
    }
    for item in map(json.loads, actual.split("\n")):
        assert len(index[item["id"]]) == len(item["payload"])


def test_verify2(tmp_path, root, server_a_args):
    output = tmp_path
    result = CliRunner().invoke(
        commands.verify2,
        server_a_args
        + [
            "--input",
            str(root / "server_a" / "raw" / "data.ndjson"),
            "--input-internal",
            str(
                root
                / "server_a"
                / "intermediate"
                / "internal"
                / "verify1"
                / "data.ndjson"
            ),
            "--input-external",
            str(
                root
                / "server_b"
                / "intermediate"
                / "internal"
                / "verify1"
                / "data.ndjson"
            ),
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0, result.stdout_bytes
    expect = (
        (root / "server_a" / "intermediate" / "internal" / "verify2" / "data.ndjson")
        .read_text()
        .strip()
    )
    actual = (output / "data.ndjson").read_text().strip()
    index = {
        item["id"]: item["payload"] for item in map(json.loads, expect.split("\n"))
    }
    for item in map(json.loads, actual.split("\n")):
        assert len(index[item["id"]]) == len(item["payload"])


def test_aggregate(tmp_path, root, server_a_args):
    output = tmp_path
    result = CliRunner().invoke(
        commands.aggregate,
        server_a_args
        + [
            "--input",
            str(root / "server_a" / "raw" / "data.ndjson"),
            "--input-internal",
            str(
                root
                / "server_a"
                / "intermediate"
                / "internal"
                / "verify2"
                / "data.ndjson"
            ),
            "--input-external",
            str(
                root
                / "server_b"
                / "intermediate"
                / "internal"
                / "verify2"
                / "data.ndjson"
            ),
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0, result.stdout_bytes
    expect = (
        root / "server_a" / "intermediate" / "internal" / "aggregate" / "data.ndjson"
    ).read_text()
    actual = (output / "data.ndjson").read_text()
    assert actual == expect


def test_publish(tmp_path, root, server_a_args):
    output = tmp_path
    result = CliRunner().invoke(
        commands.publish,
        server_a_args
        + [
            "--input-internal",
            str(
                root
                / "server_a"
                / "intermediate"
                / "internal"
                / "aggregate"
                / "data.ndjson"
            ),
            "--input-external",
            str(
                root
                / "server_b"
                / "intermediate"
                / "internal"
                / "aggregate"
                / "data.ndjson"
            ),
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0, result.stdout_bytes
    expect = json.loads((root / "server_a" / "processed" / "data.ndjson").read_text())
    actual = json.loads((output / "data.ndjson").read_text())
    assert actual["payload"] == expect["payload"]
