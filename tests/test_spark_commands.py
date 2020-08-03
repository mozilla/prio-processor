from base64 import b64decode, b64encode
import fileinput
import json
import os
import pytest
from pathlib import Path
from click.testing import CliRunner
from prio_processor.spark import commands


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


@pytest.fixture()
def server_b_args(root):
    config = json.loads((root / "config.json").read_text())
    server_a_keys = json.loads((root / "server_a_keys.json").read_text())
    server_b_keys = json.loads((root / "server_b_keys.json").read_text())
    shared_seed = json.loads((root / "shared_seed.json").read_text())
    return [
        "--server-id",
        "B",
        "--private-key-hex",
        server_b_keys["private_key"],
        "--shared-secret",
        shared_seed["shared_seed"],
        "--public-key-hex-internal",
        server_b_keys["public_key"],
        "--public-key-hex-external",
        server_a_keys["public_key"],
        "--n-data",
        config["n_data"],
        "--batch-id",
        config["batch_id"],
    ]


def test_verify1(spark, tmp_path, root, server_a_args):
    output = tmp_path / "output"
    result = CliRunner().invoke(
        commands.verify1,
        server_a_args
        + ["--input", str(root / "server_a" / "raw"), "--output", str(output)],
    )
    assert result.exit_code == 0, result
    joined = (
        spark.read.json(
            str(root / "server_a" / "intermediate" / "internal" / "verify1")
        )
        .withColumnRenamed("payload", "payload_expected")
        .join(spark.read.json(str(output)), on="id")
    )
    assert joined.count()
    assert joined.where("length(payload) <> length(payload_expected)").count() == 0


def test_verify2(spark, tmp_path, root, server_a_args):
    output = tmp_path / "output"
    result = CliRunner().invoke(
        commands.verify2,
        server_a_args
        + [
            "--input",
            str(root / "server_a" / "raw"),
            "--input-internal",
            str(root / "server_a" / "intermediate" / "internal" / "verify1"),
            "--input-external",
            str(root / "server_b" / "intermediate" / "internal" / "verify1"),
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0, result
    joined = (
        spark.read.json(
            str(root / "server_a" / "intermediate" / "internal" / "verify2")
        )
        .withColumnRenamed("payload", "payload_expected")
        .join(spark.read.json(str(output)), on="id")
    )
    assert joined.count()
    assert joined.where("length(payload) <> length(payload_expected)").count() == 0


def test_aggregate(tmp_path, root, server_a_args):
    output = tmp_path / "output"
    result = CliRunner().invoke(
        commands.aggregate,
        server_a_args
        + [
            "--input",
            str(root / "server_a" / "raw"),
            "--input-internal",
            str(root / "server_a" / "intermediate" / "internal" / "verify2"),
            "--input-external",
            str(root / "server_b" / "intermediate" / "internal" / "verify2"),
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0, result
    data = json.loads(next(output.glob("*.json")).read_text())
    assert data["error"] == 0
    assert data["total"] == 5


# TODO: this is required because the new command-line interface deviates from
# the original in a few ways. This should be resolved by revisiting the original
# API so it returns the expected payload format.
@pytest.fixture()
def aggregate(tmp_path, root, server_a_args, server_b_args):
    output = tmp_path
    result = CliRunner().invoke(
        commands.aggregate,
        server_a_args
        + [
            "--input",
            str(root / "server_a" / "raw"),
            "--input-internal",
            str(root / "server_a" / "intermediate" / "internal" / "verify2"),
            "--input-external",
            str(root / "server_b" / "intermediate" / "internal" / "verify2"),
            "--output",
            str(output / "a"),
        ],
    )
    result = CliRunner().invoke(
        commands.aggregate,
        server_b_args
        + [
            "--input",
            str(root / "server_b" / "raw"),
            "--input-internal",
            str(root / "server_b" / "intermediate" / "internal" / "verify2"),
            "--input-external",
            str(root / "server_a" / "intermediate" / "internal" / "verify2"),
            "--output",
            str(output / "b"),
        ],
    )
    return output


def test_publish(tmp_path, root, server_a_args, aggregate):
    output = tmp_path / "output"
    config = json.loads((root / "config.json").read_text())
    batch_id = config["batch_id"]
    result = CliRunner().invoke(
        commands.publish,
        server_a_args
        + [
            "--input-internal",
            str(next(aggregate.glob("a/*.json"))),
            "--input-external",
            str(next(aggregate.glob("b/*.json"))),
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0, result
    expect = json.loads((root / "server_a" / "processed" / "data.ndjson").read_text())
    actual = json.loads(next(output.glob("*.json")).read_text())
    assert actual["payload"] == expect["payload"]
