# Prio Processor

`mozilla/prio-processor` is a container application that implements the privacy
and correctness guarantees of Prio, a privacy-preserving aggregation system. The
processor inter-operates with the Firefox Data Platform by an agreed convention
of data exchange across cloud storage.

The initial release (v1.0) contain an automated workflow for batched processing
of ["prio"
pings](https://firefox-source-docs.mozilla.org/toolkit/components/telemetry/telemetry/data/prio-ping.html)
that are ingested via
[mozilla/gcp-ingestion](https://github.com/mozilla/gcp-ingestion).

This processor aggregates [Origin Telemetry
pings](https://firefox-source-docs.mozilla.org/toolkit/components/telemetry/telemetry/collection/origin.html)
configured to measure blocklist exceptions in Firefox on pre-release channels.

## Quick start

```bash
# build the container
make build

# run the container on localhost
make test
```

Several integration tests are currently configured under the `deployments`
directory. Choose a configuration that's relevant to your situation and the
follow the instructions. Many of these will require provisioning infrastructure
such as Google Cloud Platform resources.

Some functionality requires access to Mozilla's Data Platform e.g. reading from
the Prio ping for Origin Telemetry data in BigQuery. To request service account
access, file a bug under [Data Platform and Tools ::
Operations](https://bugzilla.mozilla.org/enter_bug.cgi?product=Data%20Platform%20and%20Tools).

### Running the `staging` job

A Spark job populates the processors with data from Mozilla's ingestion system.
You will need a project that is configured in the Firefox data operations
sandbox, configured with a service account for running Cloud DataProc. Data is
staged for processing by reading data from a warehoused location into buckets
that are polled for processing.

Run the bootstrap command from the container to populate a prefix in a
storage bucket with the python module.

```bash
docker run \
    -e GOOGLE_APPLICATION_CREDENTIALS=/app/.credentials \
    -v <CREDENTIAL_FILE>:/app/.credentials \
    -it mozilla/prio-processor:latest bash -c \
        "cd processor; prio-processor bootstrap --output gs://<BUCKET>/bootstrap/"
```

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

Run the job.

```bash
gcloud dataproc jobs submit pyspark \
    gs://<BUCKET>/bootstrap/runner.py \
    --cluster test-cluster  \
    --jars gs://spark-lib/bigquery/spark-bigquery-latest.jar \
    --py-files gs://<BUCKET>/bootstrap/prio_processor.egg \
        -- \
        staging \
        --source bigquery \
        --date <YYYY-MM-DD> \
        --input moz-fx-data-shar-nonprod-efed.payload_bytes_decoded.telemetry_telemetry__prio_v4 \
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

Finally, start the processor. Be sure to configure the appropriate variables.

```bash
docker run \
    -e SERVER_ID \
    -e SHARED_SECRET \
    -e PRIVATE_KEY_HEX \
    -e PUBLIC_KEY_HEX_INTERNAL \
    -e PUBLIC_KEY_HEX_EXTERNAL \
    -e APP_NAME \
    -e BUCKET_PREFIX \
    -e BUCKET_INTERNAL_INGEST \
    -e BUCKET_INTERNAL_PRIVATE \
    -e BUCKET_INTERNAL_SHARED \
    -e BUCKET_EXTERNAL_SHARED \
    -e RETRY_LIMIT=90 \
    -e RETRY_DELAY=10 \
    -e RETRY_BACKOFF_EXPONENT=1 \
    -e DATA_CONFIG=/app/processor/config/content.json \
    -e GOOGLE_APPLICATION_CREDENTIALS=/app/.credentials \
    -v <CREDENTIAL_FILE>:/app/.credentials \
    -it mozilla/prio-processor:latest \
    processor/bin/process
```

Once data has been detected under
`${BUCKET_INTERNAL_INGEST}/{BUCKET_PREFIX}/{SUBMISSION_DATE}/raw`, the server
will begin processing.

## Container application overview

The container can be built from source using Docker. This can be run locally or
in a container service such as Google Kubernetes Engine (GKE). The built docker
image can be pulled from the
[mozilla/prio-processor](https://hub.docker.com/r/mozilla/prio-processor)
dockerhub repository:

```bash
docker pull mozilla/prio-processor:latest
```

### Configuring Environment Variables

| Name                             | Purpose                                                                          |
| -------------------------------- | -------------------------------------------------------------------------------- |
| `APP_NAME`                       | The name of the application, unique to a data config by convention.              |
| `SUBMISSION_DATE`                | The date of data being processed. Defaults to today's date in ISO8601.           |
| `DATA_CONFIG`                    | A JSON file containing the mapping of `batch-id` to `n-data`.                    |
| `SERVER_ID`                      | The identifier for the processor, either `A` or `B`                              |
| `SHARED_SECRET`                  | A shared secret generated by `prio shared-seed`.                                 |
| `PRIVATE_KEY_HEX`                | The private key of the processor as a hex binary string.                         |
| `PUBLIC_KEY_HEX_INTERNAL`        | The public key of the processor as a hex binary string.                          |
| `PUBLIC_KEY_HEX_EXTERNAL`        | The public key of the co-processor as a hex binary string.                       |
| `BUCKET_INTERNAL_INGEST`         | The bucket containing data from an ingestion server, triggers processing         |
| `BUCKET_INTERNAL_PRIVATE`        | The bucket containing data that is viewable by the processor alone.              |
| `BUCKET_INTERNAL_SHARED`         | The bucket containing data from the processor's previous stage.                  |
| `BUCKET_EXTERNAL_SHARED`         | The bucket containing incoming data from the co-processor's previous stage.      |
| `BUCKET_PREFIX`                  | The bucket prefix for storing data. Defaults to `data/v1`                        |
| `GOOGLE_APPLICATION_CREDENTIALS` | The path on the container filesystem containing GCP service account credentials. |
| `RETRY_LIMIT`                    | The number of retry attempts for fetching shared data.                           |
| `RETRY_DELAY`                    | The number of seconds to wait before retrying.                                   |
| `RETRY_BACKOFF_EXPONENT`         | Used to implement exponential backoff.                                           |

Data configuration should be mounted into the `/app/processor/config` directory
and set via `DATA_CONFIG`. Likewise, the GCP service account JSON key-file
should be mounted into `/app/.credentials` and set via
`GOOGLE_APPLICATION_CREDENTIALS`.

### Building an image from source

To build the container locally:

```bash
make build
```

This will generate two images that are ready to use. The development image is
configured to run unit and integration tests, while the production image will
initialize the single trigger, batched-processing mode.

```bash
# run the tests
docker run prio:dev

# start a shell session
# --interactive --tty
docker run -it prio:dev bash

# start the server
docker run prio:prod
```

See the prio-processor README for more details about the development
environment.

### Ranged Partitioning

Data is bundled into partitions where partitions have been assigned based on
matching ids.

```sh
├── _SUCCESS
└── submission_date=2019-06-26
    ├── server_id=a
    │   ├── batch_id=content.blocking_blocked_TESTONLY-0
    │   │   ├── part-00000-6adba759-6e58-4092-8120-6331705e2e46.c000.json
    │   │   └── part-00001-6adba759-6e58-4092-8120-6331705e2e46.c000.json
    │   └── batch_id=content.blocking_blocked_TESTONLY-1
    │       ├── part-00002-6adba759-6e58-4092-8120-6331705e2e46.c000.json
    │       └── part-00003-6adba759-6e58-4092-8120-6331705e2e46.c000.json
    └── server_id=b
        ├── batch_id=content.blocking_blocked_TESTONLY-0
        │   ├── part-00000-6adba759-6e58-4092-8120-6331705e2e46.c000.json
        │   └── part-00001-6adba759-6e58-4092-8120-6331705e2e46.c000.json
        └── batch_id=content.blocking_blocked_TESTONLY-1
            ├── part-00002-6adba759-6e58-4092-8120-6331705e2e46.c000.json
            └── part-00003-6adba759-6e58-4092-8120-6331705e2e46.c000.json
```

### Filesystem exchange

The co-processors share data by using cloud storage. Each storage unit is
separated by path hierarchy and permissions implemented by the filesystem. The
path encodes various metadata.

At a high level, the directories represent a logical step in the processing
pipeline. There is a directory for each communication that occurs between
processors.

```bash
filesystem
├── server_a
│   ├── intermediate
│   │   ├── external
│   │   │   ├── aggregate
│   │   │   ├── verify1
│   │   │   └── verify2
│   │   └── internal
│   │       ├── aggregate
│   │       ├── verify1
│   │       └── verify2
│   ├── processed
│   └── raw
└── server_b
    ├── intermediate
    │   ├── external
    │   │   ├── aggregate
    │   │   ├── verify1
    │   │   └── verify2
    │   └── internal
    │       ├── aggregate
    │       ├── verify1
    │       └── verify2
    ├── processed
    └── raw
```

The view of the paths when viewed from one project.

```bash
filesystem
├── server_a
│   ├── intermediate
│   │   ├── external
│   │   │   ├── aggregate
│   │   │   ├── verify1
│   │   │   └── verify2
│   │   └── internal
│   │       ├── aggregate
│   │       ├── verify1
│   │       └── verify2
│   ├── processed
│   └── raw
└── server_b
    └─── intermediate
        └─── external
            ├── aggregate
            ├── verify1
            └── verify2
```

In order to support general use-cases, the storage convention ends up taking a
more intricate structure. Here, we'll look at the structure for an integration
test looking from the perspective of server A.

A bucket is a namespace in the file system chosen for this project (Amazon S3
compatible stores). The directories are split across three buckets for granular
permissions. The following buckets are configured:

```bash
BUCKET_INTERNAL_INGEST=a-ingest-d70d758a4b28a791
BUCKET_INTERNAL_PRIVATE=a-private-d70d758a4b28a791
BUCKET_INTERNAL_SHARED=a-shared-d70d758a4b28a791
BUCKET_EXTERNAL_SHARE=b-shared-d70d758a4b28a791
```

The ingest bucket is shared between server A and an ingestion service that
collects and partitions data. The private bucket is accessible only to server A.
The internal shared bucket is used to receive data from server B. The external
shared bucket is used to send data to server B.

In addition, the following variables are configured:

```bash
APP_NAME=test-app
BUCKET_PREFIX=test-app/v1
PUBLIC_KEY_INTERNAL=E58761F983D681367F854C4DE70D2BFA7BE6CDE79422B57B4B850ABD7FCB6839
PUBLIC_KEY_EXTERNAL=C629C221FBCF524FE2FC746A0E114749DF18013F893280B4203F20859CA7FC4B
SUBMISSION_DATE=2021-04-27
```

Every transaction is prefixed with the following directory structure:

```bash
{BUCKET_PREFIX}/{PUBLIC_KEY_EXTERNAL}/{APP_NAME}/{SUBMISSION_DATE}
```

When sending data, the internal public key is encoded into the path for
bookkeeping by the other server.

This results in a hierarchy that takes the following shape:

```bash
a-ingest-d70d758a4b28a791
└── test-app
    └── v1
        └── C629C221FBCF524FE2FC746A0E114749DF18013F893280B4203F20859CA7FC4B
            └── test-app
                └── 2021-04-27
                    └── raw
                        └── shares
                            └── batch_id=content.blocking_blocked_TESTONLY-0
a-private-d70d758a4b28a791
└── test-app
    └── v1
        └── C629C221FBCF524FE2FC746A0E114749DF18013F893280B4203F20859CA7FC4B
            └── test-app
                └── 2021-04-27
                    ├── intermediate
                    │   └── internal
                    │       ├── aggregate
                    │       │   └── batch_id=content.blocking_blocked_TESTONLY-0
                    │       ├── verify1
                    │       │   └── batch_id=content.blocking_blocked_TESTONLY-0
                    │       └── verify2
                    │           └── batch_id=content.blocking_blocked_TESTONLY-0
                    └── processed
                        └── publish
                            └── batch_id=content.blocking_blocked_TESTONLY-0
a-shared-d70d758a4b28a791
└── test-app
    └── v1
        └── C629C221FBCF524FE2FC746A0E114749DF18013F893280B4203F20859CA7FC4B
            └── test-app
                └── 2021-04-27
                    └── intermediate
                        └── external
                            ├── aggregate
                            │   └── batch_id=content.blocking_blocked_TESTONLY-0
                            ├── verify1
                            │   └── batch_id=content.blocking_blocked_TESTONLY-0
                            └── verify2
                                └── batch_id=content.blocking_blocked_TESTONLY-0
b-shared-d70d758a4b28a791
└── test-app
    └── v1
        └── E58761F983D681367F854C4DE70D2BFA7BE6CDE79422B57B4B850ABD7FCB6839
            └── test-app
                └── 2021-04-27
                    └── intermediate
                        └── external
                            ├── aggregate
                            │   └── batch_id=content.blocking_blocked_TESTONLY-0
                            ├── verify1
                            │   └── batch_id=content.blocking_blocked_TESTONLY-0
                            └── verify2
                                └── batch_id=content.blocking_blocked_TESTONLY-0
```

There are few things to note:

- There are no namespace clashes when overlaying the files in the three buckets.
  This is intentional, for allowing the use of a single bucket in testing
  scenarios.
- Files are read and written using an HDFS connector, so parameters like the
  `batch_id` are written using the `{key}={variable}` convention to specify new
  partitions of data.

#### Configuring cloud storage

Currently, only Google Cloud Storage has been thoroughly tested. However, the
tooling supports S3 compatible file-stores via
[`gsutil`](https://cloud.google.com/storage/docs/interoperability).

### Triggering mechanism

The processor is designed for ad-hoc usage that can be scheduled externally. The
application starts up and waits for data in a specified location. When data is
signaled in the receiving bucket, it processes the partition at a time, and
writes it to the other server's receiving bucket. This process is repeated for
all of the stages involved in aggregation: `verify1`, `verify2`, `aggregate`,
and `publish`.

Once all stages are complete, the processor will terminate and clear the state
of the buckets.

### Scheduling

The staging frequency should match the processor job frequency. Both servers
should come online within the tolerances of the retry mechanism controlled by
the `RETRY_*` variables.

## Suggested configuration

A reference data-set size is 1 million records containing shares of size
`N_DATA=2000`. Pairs of shares are encoded into strings that total 50 kilobytes.
The entire data-set totals approximately 50 gigabytes.

The staging job has been configured with an upper bound of 0.25 gigabytes per
partition. This should result in an evenly-sized data-set contain approximately
200 partitions.

Processing efficiency is measured through compute and memory utilization. The
suggested configuration is to use a large number of cores (32+) with 0.5
gigabytes of memory per core. Persistent disk should match the data-set size and
volume of messages between both servers. The [`n1-standard`
family](https://cloud.google.com/compute/docs/machine-types#general_purpose) of
general purpose machines is sufficient for processing.
