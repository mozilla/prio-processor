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


def test_generate_integration(spark, tmp_path, root):
    """Reference of the directory structure.

        /tmp/pytest-of-machine/pytest-0/test_generate_integration0
    ├── [   0]  _SUCCESS
    ├── [4.0K]  server_id=a
    │   ├── [4.0K]  batch_id=bad-id
    │   │   └── [ 65K]  part-00000-1c0d52c3-6866-4c5a-b118-ad79b0f20852.c000.json
    │   ├── [4.0K]  batch_id=test-0
    │   │   ├── [ 30K]  part-00000-1c0d52c3-6866-4c5a-b118-ad79b0f20852.c000.json
    │   │   └── [ 36K]  part-00001-1c0d52c3-6866-4c5a-b118-ad79b0f20852.c000.json
    │   └── [4.0K]  batch_id=test-1
    │       └── [107K]  part-00001-1c0d52c3-6866-4c5a-b118-ad79b0f20852.c000.json
    └── [4.0K]  server_id=b
        ├── [4.0K]  batch_id=bad-id
        │   └── [ 26K]  part-00000-1c0d52c3-6866-4c5a-b118-ad79b0f20852.c000.json
        ├── [4.0K]  batch_id=test-0
        │   ├── [ 12K]  part-00000-1c0d52c3-6866-4c5a-b118-ad79b0f20852.c000.json
        │   └── [ 15K]  part-00001-1c0d52c3-6866-4c5a-b118-ad79b0f20852.c000.json
        └── [4.0K]  batch_id=test-1
            └── [ 27K]  part-00001-1c0d52c3-6866-4c5a-b118-ad79b0f20852.c000.json
    """

    server_a_keys = json.loads((root / "server_a_keys.json").read_text())
    server_b_keys = json.loads((root / "server_b_keys.json").read_text())
    output = tmp_path

    project_root = Path(__file__).parent.parent
    config_path = project_root / "config" / "test-small.json"
    n_rows = 100
    result = CliRunner().invoke(
        commands.generate_integration,
        [
            "--data-config",
            str(config_path),
            "--public-key-hex-internal",
            server_a_keys["public_key"],
            "--public-key-hex-external",
            server_a_keys["public_key"],
            "--output",
            str(output),
            "--n-rows",
            n_rows,
            "--n-partitions",
            2,
        ],
    )
    assert result.exit_code == 0, result.stdout_bytes

    # assert the directory structure
    server_a_dir = output / "server_id=a"
    server_b_dir = output / "server_id=b"
    assert server_a_dir.exists()
    assert server_b_dir.exists()
    assert (server_a_dir / "batch_id=bad-id").exists() and (
        server_b_dir / "batch_id=bad-id"
    ).exists()

    # assert that there are 100 rows
    assert spark.read.json(str(server_a_dir / "batch_id=bad-id")).count() == n_rows
    assert spark.read.json(str(server_b_dir / "batch_id=bad-id")).count() == n_rows
    # assert size of normal batch
    assert spark.read.json(str(server_a_dir / "batch_id=test-0")).count() == n_rows
    # assert the number of batch_ids
    assert spark.read.json(str(output)).select("batch_id").distinct().count() == 4


def test_generate_integration_drop_column(spark, tmp_path, root):
    server_a_keys = json.loads((root / "server_a_keys.json").read_text())
    server_b_keys = json.loads((root / "server_b_keys.json").read_text())
    output = tmp_path

    project_root = Path(__file__).parent.parent
    config_path = project_root / "config" / "test-small.json"
    n_rows = 100
    result = CliRunner().invoke(
        commands.generate_integration,
        [
            "--data-config",
            str(config_path),
            "--public-key-hex-internal",
            server_a_keys["public_key"],
            "--public-key-hex-external",
            server_a_keys["public_key"],
            "--output",
            str(output),
            "--n-drop-batch",
            1,
        ],
    )
    assert result.exit_code == 0, result.stdout_bytes
    # assert that one of the ids has been dropped
    assert set(
        [
            r.batch_id
            for r in spark.read.json(str(output))
            .select("batch_id")
            .distinct()
            .collect()
        ]
    ) == {"test-0", "test-1", "bad-id"}


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


def test_publish(tmp_path, root, server_a_args):
    output = tmp_path / "output"
    args = server_a_args + [
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
            / "server_a"
            / "intermediate"
            / "external"
            / "aggregate"
            / "data.ndjson"
        ),
        "--output",
        str(output),
    ]
    print(" ".join(map(str, args)))
    result = CliRunner().invoke(commands.publish, args)
    assert result.exit_code == 0, result
    expect = json.loads((root / "server_a" / "processed" / "data.ndjson").read_text())
    actual = json.loads(next(output.glob("*.json")).read_text())
    assert actual["payload"] == expect["payload"]
