#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""
The entry-point into 
"""

import sys

from os import environ
from subprocess import run
from pathlib import Path

verify1_config = {
    "input": "raw",
    "output_internal": "intermediate/internal/verify1",
    "output_external": "intermediate/external/verify1",
}

verify2_config = {
    "input_internal": "intermediate/internal/verify1",
    "input_external": "intermediate/external/verify1",
    "output_internal": "intermediate/internal/verify2",
    "output_external": "intermediate/external/verify2",
}

aggregate_config = {
    "input_internal": "intermediate/internal/verify2",
    "input_external": "intermediate/external/verify2",
    "output_internal": "intermediate/internal/aggregate",
    "output_external": "intermediate/external/aggregate",
}

publish_config = {
    "input_internal": "intermediate/internal/aggregate",
    "input_external": "intermediate/external/aggregate",
    "output": "processed",
}


def check_environment():
    """Check that the keys are set in the environment."""
    keys = {
        "N_DATA",
        "BATCH_ID",
        "SERVER_ID",
        "SHARED_SECRET",
        "PRIVATE_KEY_HEX",
        "PUBLIC_KEY_HEX_INTERNAL",
        "PUBLIC_KEY_HEX_EXTERNAL",
    }
    unset_keys = keys - set(environ.keys())
    if unset_keys:
        print("The following environment variables must be set:")
        for key in unset_keys:
            print("\t", key)
        sys.exit()


def prio_step(command, config={}, env={}):
    args = sum([[f"--{k}", v] for k, v in config.items()], [])
    return run(["prio", command] + args, env={**environ, **env})


def main():
    prio_step("keygen")


if __name__ == "__main__":
    main()
