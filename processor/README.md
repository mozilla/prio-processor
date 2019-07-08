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
```

Set the following environment variables in a `.env` file in the current directory:

```
GOOGLE_APPLICATION_CREDENTIALS_A=...
GOOGLE_APPLICATION_CREDENTIALS_B=...
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

Running integration tests will require setting up two separate GCP projects.
Each project should have a service account that contains authorization to the
appropriate storage buckets that are used in this project. In particular, the
following environment variables are set per server:

```
BUCKET_INTERNAL_PRIVATE - The bucket containing private data for the server
BUCKET_INTERNAL_SHARED - The bucket containing incoming messages
BUCKET_EXTERNAL_SHARED - The bucket containing outgoing messages
GCP_CREDENTIALS - The location of the JSON google application credentials
```
