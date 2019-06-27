# The Prio Server Runtime

The application folder contains all of the components that are necessary for
running a Mozilla-compatible Prio server. The back-ends can be replaced for
different deployment configurations.

## Quickstart

```bash
# build the container
make build

# run the container on localhost
make test

# TODO: deploy the application to GKE
```

## Overview

The bin folder contains scripts for data processing in Google Cloud Platform
(GCP).

* `cleanup` - Resets the private and shared buckets to a clean state
* `generate` - Generate testing data and sync into private buckets
* `process` - Process multiple partitions of data in parallel, blocking on each
  step as necessary.
* `integrate` - Coordinate data generation and processing servers in a local
  docker-compose workflow.
