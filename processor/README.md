# Prio Processor Runtime

The processor folder contains all of the components that are necessary for
running a Mozilla-compatible Prio server. The back-ends can be replaced for
different deployment configurations.

## Quick start

```bash
# build the container
make build

# run the container on localhost
make test
```

Set the following environment variables in a `.env` file in the current
directory:

```bash
GOOGLE_APPLICATION_CREDENTIALS_A=...
GOOGLE_APPLICATION_CREDENTIALS_B=...
```

The integration tests are currently configured for `moz-fx-priotest-project-a`
and `moz-fx-priotest-project-b` Google Cloud Platform. To request service
account access, file a bug under [Data Platform and Tools ::
Operations](https://bugzilla.mozilla.org/enter_bug.cgi?product=Data%20Platform%20and%20Tools).

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

* `BUCKET_INTERNAL_PRIVATE` - The bucket containing private data for the server
* `BUCKET_INTERNAL_SHARED` - The bucket containing incoming messages
* `BUCKET_EXTERNAL_SHARED` - The bucket containing outgoing messages
* `GOOGLE_APPLICATION_CREDENTIALS` - The location of the JSON google application
  credentials
