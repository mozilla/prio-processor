# prio-processor

[![CircleCI](https://circleci.com/gh/mozilla/prio-processor.svg?style=svg)](https://circleci.com/gh/mozilla/prio-processor)

Prio is a system for aggregating data in a privacy-preserving way. This
repository includes a Python wrapper around
[libprio](https://github.com/mozilla/libprio) and a command-line tool for batch
processing in Prio's multi-server architecture.

For more information about Prio, see [this blog
post](https://hacks.mozilla.org/2018/10/testing-privacy-preserving-telemetry-with-prio/).

## Docker

This project contains a pre-configured build and test environment via docker.

```bash
make

# or using docker directly by building the development stage
docker build --target development -t prio:dev .
```

`make` at the root directory will generate two containers in a multi-stage
build. The `prio:dev` image is suitable for development. The `prio:latest` image
is the production image that is suitable for server deployments.

You can mount your working directory and shell into the container for
development work.

```bash
docker run -v `pwd`:/app -it prio:dev bash
cd prio
make
make test
```

## Adding new Python dependencies

To add new Python dependencies to the container, use `pip-tools` to manage the
`requirements.txt`.

```bash
pip install pip-tools

# add new requirement to requirements.in

# generate a new requirements.txt
pip-compile
```
