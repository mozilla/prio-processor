from base64 import b64decode, b64encode
import json
import pytest
from click.testing import CliRunner
from prio.cli import commands


def test_shared_seed():
    runner = CliRunner()
    result = runner.invoke(commands.shared_seed)
    assert result.exit_code == 0
    # PRG_SEED_LENGTH == AES_128_KEY_LENGTH == 16
    assert len(b64decode(result.output)) == 16


def test_keygen():
    runner = CliRunner()
    result = runner.invoke(commands.keygen)
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert set(data.keys()) == set(["private_key", "public_key"])
    # CURVE25519_KEY_LEN_HEX == 64 bytes
    assert len(data["private_key"]) == len(data["public_key"]) == 64
