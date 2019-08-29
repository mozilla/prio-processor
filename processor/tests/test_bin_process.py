import json
import re
import subprocess
from collections import Counter
from functools import partial
from os import environ
from pathlib import Path
from subprocess import PIPE, CompletedProcess, Popen, run

import gcsfs
import pytest
import yaml
from dotenv import load_dotenv

try:
    run(["docker-compose", "config"])
except:
    pytest.skip("skipping tests that require docker", allow_module_level=True)

load_dotenv()
assert environ.get("GOOGLE_APPLICATION_CREDENTIALS_A"), "missing credentials"
assert environ.get("GOOGLE_APPLICATION_CREDENTIALS_B"), "missing credentials"


def gcsfs_a():
    return gcsfs.GCSFileSystem(token=environ["GOOGLE_APPLICATION_CREDENTIALS_A"])


def gcsfs_b():
    return gcsfs.GCSFileSystem(token=environ["GOOGLE_APPLICATION_CREDENTIALS_B"])


def ansi_escape(text):
    """https://stackoverflow.com/a/14693789"""
    escape = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
    return escape.sub("", text)


def process_run(command: str, service: str, env: dict = {}) -> CompletedProcess:
    env_str = " ".join(f"-e {k}={v}" for k, v in env.items())
    result = run(
        [
            "bash",
            "-c",
            f'docker-compose run {env_str} {service} bash -c ". bin/process; {command}"',
        ],
        stdout=PIPE,
    )
    result.stdout = ansi_escape(result.stdout.decode())
    return result


@pytest.fixture()
def cleanup():
    """Runs the cleanup function before and after a test is run. It also returns
    a function that can be called manually at any point in the test.
    """

    def _cleanup():
        run(["bash", "-c", "docker-compose run server_a bin/cleanup"])
        run(["bash", "-c", "docker-compose run server_b bin/cleanup"])

    _cleanup()
    yield _cleanup
    _cleanup()


@pytest.fixture()
def docker_compose_yml():
    result = run("docker-compose config".split(), stdout=PIPE)
    return yaml.load(result.stdout, Loader=yaml.SafeLoader)


@pytest.fixture()
def server_a_env(docker_compose_yml):
    return docker_compose_yml["services"]["server_a"]["environment"]


@pytest.fixture()
def server_b_env(docker_compose_yml):
    return docker_compose_yml["services"]["server_b"]["environment"]


@pytest.fixture()
def admin_env(docker_compose_yml):
    return docker_compose_yml["services"]["admin"]["environment"]


@pytest.fixture()
def process_run_a(server_a_env):
    return partial(process_run, service="server_a", env=server_a_env)


def test_docker_compose_yml_exists(docker_compose_yml):
    config = docker_compose_yml
    assert not {"server_a", "server_b", "admin"} - set(config["services"].keys())


def test_docker_compose_yml_contains_consistent_keys(
    server_a_env, server_b_env, admin_env
):
    assert (
        server_a_env["PUBLIC_KEY_HEX_INTERNAL"]
        == server_b_env["PUBLIC_KEY_HEX_EXTERNAL"]
        == admin_env["PUBLIC_KEY_HEX_INTERNAL"]
    )

    assert (
        server_a_env["PUBLIC_KEY_HEX_EXTERNAL"]
        == server_b_env["PUBLIC_KEY_HEX_INTERNAL"]
        == admin_env["PUBLIC_KEY_HEX_EXTERNAL"]
    )


def test_bin_process_can_be_sourced(process_run_a):
    # `:` is the bash no-op command
    result = process_run_a(":")
    result.check_returncode()


def test_config_get(process_run_a):
    result = process_run_a("config_get content.blocking_blocked_TESTONLY-0")
    assert int(result.stdout.split()[-1]) == 2046

    result = process_run_a("config_get content.blocking_blocked_TESTONLY-1")
    assert int(result.stdout.split()[-1]) == 441

    result = process_run_a("config_get non-existent_batch_id")
    assert result.stdout.split()[-1] == "null"


def test_extract_batch_id(process_run_a):
    result = process_run_a("extract_batch_id branch/batch_id=test/leaf")
    assert result.stdout.split()[-1] == "test"


def test_scope_based_authentication_fails_locally(server_a_env):
    result = process_run(
        "authenticate",
        service="server_a",
        env={**server_a_env, **{"GOOGLE_APPLICATION_CREDENTIALS": ""}},
    )
    with pytest.raises(subprocess.CalledProcessError):
        result.check_returncode()


def test_buckets_are_empty_after_cleanup(cleanup, server_a_env, server_b_env):
    run(["bash", "-c", "docker-compose run admin bin/generate"])

    # test the state of server a
    assert len(gcsfs_a().walk(server_a_env["BUCKET_INTERNAL_PRIVATE"])) > 0
    assert len(gcsfs_a().walk(server_a_env["BUCKET_INTERNAL_SHARED"])) == 0

    # test the state of server b
    assert len(gcsfs_b().walk(server_b_env["BUCKET_INTERNAL_PRIVATE"])) > 0
    assert len(gcsfs_b().walk(server_b_env["BUCKET_INTERNAL_SHARED"])) == 0

    cleanup()
    # check that the data has been cleaned up
    assert len(gcsfs_a().walk(server_a_env["BUCKET_INTERNAL_PRIVATE"])) == 0
    assert len(gcsfs_b().walk(server_b_env["BUCKET_INTERNAL_PRIVATE"])) == 0


def test_generated_data_follows_filesystem_convention(
    cleanup, server_a_env, server_b_env
):
    run(["bash", "-c", "docker-compose run admin bin/generate"])

    path = Path(__file__).parent.parent / "config" / "content.json"
    with open(path) as f:
        n_batch_ids = len(json.load(f).keys())

    # include "bad-id"
    n_batch_ids += 1
    n_parts_per_batch = 5

    files_a = gcsfs_a().walk(server_a_env["BUCKET_INTERNAL_PRIVATE"])
    files_b = gcsfs_b().walk(server_b_env["BUCKET_INTERNAL_PRIVATE"])

    def relative(path, n=1):
        return "/".join(path.split("/")[n:])

    assert set(map(relative, files_a)) == set(map(relative, files_b))
    assert len([x for x in files_a if "_SUCCESS" in x]) == 1

    # directory structure
    # bucket / raw / batch_id={value} / *.json
    def process(path):
        batch_id_idx = 3
        return path.split("/")[batch_id_idx].split("=")[-1]

    batch_ids = [process(x) for x in files_a if x.endswith(".json")]
    assert len(batch_ids) == n_batch_ids * n_parts_per_batch

    counter = Counter(batch_ids)
    assert len(counter.keys()) == n_batch_ids
    assert all([v == n_parts_per_batch for v in counter.values()])


@pytest.mark.slow
def test_processing_generated_data_results_in_published_aggregates(
    cleanup, server_a_env, server_b_env
):
    # NOTE: a test failure will spit out a large amount of text
    run(["bash", "-c", "docker-compose run admin bin/generate"])
    server_a = Popen(["bash", "-c", "docker-compose run server_a bin/process"])
    server_b = Popen(["bash", "-c", "docker-compose run server_b bin/process"])

    server_a.wait()
    server_b.wait()

    assert server_a.returncode == 0
    assert server_b.returncode == 0

    def _validate(fs, server_env):
        paths = [
            path
            for path in fs.walk(server_env["BUCKET_INTERNAL_PRIVATE"])
            if path.endswith(".json") and path.split("/")[1] == "processed"
        ]
        assert len(paths) > 0
        for path in paths:
            # test data should be name `{batch_id}-part-{part_num}.json`
            part_num = int(path.split("-")[-1].split(".")[0])
            data = json.load(fs.open(path))["payload"]

            n = len(data)
            assert n > 0
            expected = [int(i % 3 == 0 or i % 5 == 0) * part_num for i in range(n)]
            assert data == expected

    _validate(gcsfs_a(), server_a_env)
    _validate(gcsfs_b(), server_b_env)

    # assert that bad-id is not in the final published set
    paths = gcsfs_a().walk(server_a_env["BUCKET_INTERNAL_PRIVATE"])
    processed = [p for p in paths if "processed" in p]
    raw = [p for p in paths if "raw" in p]

    # raw paths contains bad-id and other valid ids
    assert any(["batch_id=bad-id" in p for p in raw])
    assert any(["batch_id=content.blocking_blocked_TESTONLY-0" in p for p in raw])

    # bad-id is skipped and not part of the processed paths
    assert not any(["batch_id=bad-id" in p for p in processed])
    assert any(["batch_id=content.blocking_blocked_TESTONLY-0" in p for p in processed])
