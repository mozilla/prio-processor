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

## Adding new Python dependencies

To add new Python dependencies to the container, use `pip-tools` to manage the
`requirements.txt`.

```bash
pip install pip-tools

# generate the installation requirements from setup.py
pip-compile

# generate dev requirements
pip-compile requirements-dev.in
```

## Prio Processor Runtime

The processor folder contains all of the components that are necessary for
running a Mozilla-compatible Prio server. The back-ends can be replaced for
different deployment configurations.

### Overview

The bin folder contains scripts for data processing in Google Cloud Platform
(GCP).

- `cleanup` - Resets the private and shared buckets to a clean state
- `generate` - Generate testing data and sync into private buckets
- `process` - Process multiple partitions of data in parallel, blocking on each
  step as necessary.
- `integrate` - Coordinate data generation and processing servers in a local
  docker-compose workflow.

Running integration tests will require setting up two separate GCP projects.
Each project should have a service account that contains authorization to the
appropriate storage buckets that are used in this project. In particular, the
following environment variables are set per server:

- `BUCKET_INTERNAL_PRIVATE` - The bucket containing private data for the server
- `BUCKET_INTERNAL_SHARED` - The bucket containing incoming messages
- `BUCKET_EXTERNAL_SHARED` - The bucket containing outgoing messages
- `GOOGLE_APPLICATION_CREDENTIALS` - The location of the JSON google application
  credentials

### Deployment Configuration

See the `deployment` directory for examples of configuration that can be used to
aid deployment. These may also be run as integration tests to determine whether
resources are configured properly.
