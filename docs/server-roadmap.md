# Server Roadmap

This document serves as a road-map for independent operation of a second server.
The python interface into libprio has been designed to be easily scriptable to
accomodate workflows in different infrastructure.

## Overview

1. Localhost: Batched file processing via object-store
2. Cloud: Sandboxing GCP-backed processors
3. Preprocessing: Firefox Telemetry Origin
4. Scheduling: telemetry-airflow
5. Cost and Performance
6. Future Improvements

## Localhost: Batched file processing via object-store

There is an example of running the Prio processing pipeline in
`examples/batched-processing`. An s3-compatible object store acts as the
intermediary between two containers running a script that polls for new data.
Processing is triggered via new files placed into a `raw/` processing directory,
after which each server runs in lock-step until completion. Each of the servers
is configured through environment variables, which are listed below:

```bash
# collection specific information
N_DATA
BATCH_ID

# Prio server configuration
SERVER_ID
SHARED_SECRET
PRIVATE_KEY_HEX
PUBLIC_KEY_HEX_INTERNAL
PUBLIC_KEY_HEX_EXTERNAL

# Data transport configuration
BUCKET_INTERNAL
BUCKET_EXTERNAL
MINIO_ACCESS_KEY
MINIO_SECRET_KEY
```

The servers interact using an s3-compatible file-store as a hand-off mechanism.
Minio implements an open-source store that can be configured to run within a
local cluster. Permissions are set appropriately so each server has access to an
`external` folder in the other store.

```
minio
├── server-a
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
└── server-b
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

## Cloud: Sandboxing GCP-backed processors

Once the local container-based system is proven to work adequately, the workflow
should be deployed to cloud-hosted infrastructure. One requirement is that the
two servers are running in separate projects.

The Google Cloud Platform (GCP) provides instances for running docker images and
an s3-compatible file-store. Servers can be isolated by placing them into
separate projects.

Here is one scheme for processing data.

* Store credentials in a secured bucket on GCS
* Spin up a compute engine instance at a pre-specified interval
* Pass appropriate credentials to the `prio:latest` container at runtime
* Wait for processing and shutdown the instance once done

## Preprocessing: Firefox Telemetry Origin

Telemetry Origin provides the API for the content blocking study. The prio
shares are contained in the following format:

```json
payload: {
    "<BATCH_ID>": {
        "a": "<BASE64 ENCODED DATA>",
        "b": "<BASE64 ENCODED DATA>"
    },
    ...
}
```

The payload must be flattened into a data-set per batch-id and server-id. Each
set is partitioned into the following format:

```json
{"id": "<UUID-4>", "payload": "<BASE64 ENCODED DATA>"}
```

These are partitioned into newline delimited json so they can be processed by
each of the servers. The partitioning format should look like the following.

```bash
<BUCKET>/prio/v1/submission_date=<DATE>/batch_id=<BATCH_ID>/server_id=<SERVER_ID>/*.ndjson
```

## Scheduling: telemetry-airflow

Batched processing occurs on a regular schedule to reduce the overhead of
coordination. A processor is triggered by copying data into the raw bucket.

A nightly job is configured to run the data transformation job to flatten the
ping into reasonable sized chunks. Once this is done, the data is copied into
the raw buckets for server A and server B.

Airflow can configure the necessary infrastructure for processing. In the data
processing pipeline for Mozilla, the container will run within the context of a
Kubernetes cluster that has been provisioned with the appropriate keys. This
cluster may be long running or provisioned by Airflow.

## Cost and Performance

The initial study is planned to run around 1-5 million pings per week with 2500
bits of information. A 1 million ping data-set at 2000 bits is estimated to be
around 50GB in size.

The main server is dealing with the main chunk of processing. If the initial
decoding process takes 100ms per share, we can expect use ~30 hours of vCPU
time for a 1 million ping data-set.


## Future Improvements

Here's a short, non-exhaustive list of improvements that can be made to this
pipeline.

* Use Parquet instead of ndjson, to take advantage of columnar data locality
* Use PubSub for stream processing (see docker-asyncio)
