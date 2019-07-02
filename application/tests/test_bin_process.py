import pytest
import subprocess
import yaml
import re
from functools import partial
from pathlib import Path
from os import environ
from subprocess import CompletedProcess, run, PIPE

if run(["docker-compose", "config"]).returncode != 0:
    pytest.skip("skipping tests that require docker", allow_module_level=True)


def ansi_escape(text):
    """https://stackoverflow.com/a/14693789"""
    escape = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
    return escape.sub("", text)


def process_run(command: str, service: str, env: dict = {}) -> CompletedProcess:
    result = run(
        [
            "bash",
            "-c",
            f'docker-compose run {service} bash -c ". bin/process; {command}"',
        ],
        env={**environ, **env},
        stdout=PIPE,
    )
    result.stdout = ansi_escape(result.stdout.decode())
    return result


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
def client_env(docker_compose_yml):
    return docker_compose_yml["services"]["client"]["environment"]


@pytest.fixture()
def process_run_a(server_a_env):
    return partial(process_run, service="server_a", env=server_a_env)


def test_docker_compose_yml_exists(docker_compose_yml):
    config = docker_compose_yml
    assert not {"server_a", "server_b", "client"} - set(config["services"].keys())


def test_docker_compose_yml_contains_consistent_keys(
    server_a_env, server_b_env, client_env
):
    assert (
        server_a_env["PUBLIC_KEY_HEX_INTERNAL"]
        == server_b_env["PUBLIC_KEY_HEX_EXTERNAL"]
        == client_env["PUBLIC_KEY_HEX_INTERNAL"]
    )

    assert (
        server_a_env["PUBLIC_KEY_HEX_EXTERNAL"]
        == server_b_env["PUBLIC_KEY_HEX_INTERNAL"]
        == client_env["PUBLIC_KEY_HEX_EXTERNAL"]
    )


def test_source_process(process_run_a):
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
