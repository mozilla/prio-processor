# prio-processor

[![CircleCI](https://circleci.com/gh/mozilla/prio-processor.svg?style=svg)](https://circleci.com/gh/mozilla/prio-processor)

Prio is a system for aggregating data in a privacy-preserving way. This
repository includes a command-line tool for batch processing in Prio's
multi-server architecture.

For more information about Prio, see [this blog
post](https://hacks.mozilla.org/2018/10/testing-privacy-preserving-telemetry-with-prio/).

## Docker

This project contains a pre-configured build and test environment via docker.

```bash
make

# or run directly though docker-compose
docker-compose build
```

You can mount your working directory and shell into the container for
development work.

```bash
docker-compose run -v $PWD:/app prio_processor bash
```

## Adding new dependencies

To add new Python dependencies to the container, use `pip-tools` to manage the
`requirements.txt`.

```bash
pip install pip-tools

# generate the installation requirements from setup.py
pip-compile

# generate dev requirements
pip-compile requirements-dev.in
```

Any new system dependencies should be added to the `Dockerfile` at the root of
the repository. These will be available during runtime.

## Deployment Configuration

See the `deployment` directory for examples of configuration that can be used to
aid deployment. These may also be run as integration tests to determine whether
resources are configured properly. These will typically assume Google Cloud
Platform (GCP) as a resource provider.

See the [guide](docs/guide.md) for more details.
