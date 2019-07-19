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

### Running the `staging` job

A Spark job populates the processors with data from Mozilla's ingestion system.
You will need a project that is configured in the Firefox data operations
sandbox, configured with a service account for running Cloud DataProc.

Initialize a dataproc cluster with the appropriate dependencies installed:

```bash
gcloud dataproc clusters create test-cluster \
    --zone <ZONE> \
    --image-version 1.4 \
    --metadata 'PIP_PACKAGES=click' \
    --service-account <SERVICE_ACCOUNT_ADDRESS> \
    --initialization-actions \
        gs://dataproc-initialization-actions/python/pip-install.sh
```

Run the bootstrap command from the container to populate a prefix in a
storage bucket with the python module.

```bash
docker run \
    -e GOOGLE_APPLICATION_CREDENTIALS=/app/.credentials \
    -v <CREDENTIAL_FILE>:/app/.credentials \
    -it prio:latest bash -c \
        "cd processor; prio-processor bootstrap --output gs://<BUCKET>/bootstrap/"
```

Run the job.

```bash
gcloud dataproc jobs submit pyspark \
    gs://<BUCKET>/bootstrap/runner.py \
    --cluster test-cluster  \
    --py-files gs://<BUCKET>/bootstrap/prio_processor.egg \
        -- \
        --date <YYYY-MM-DD> \
        --input gs://moz-fx-data-stage-data/telemetry-decoded_gcs-sink-doctype_prio/output \
        --output gs://<BUCKET>/prio_staging/
```

Clean up the resources, and copy the files into the private buckets to initiate
the batched processing scheme.

```bash
gsutil rm -r gs://<BUCKET>/bootstrap/
gcloud dataproc clusters delete test-cluster
```

See [PR#62](https://github.com/mozilla/prio-processor/pull/62#issue-298714211)
for more details.

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
