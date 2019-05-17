# A scriptable command-line interface to Prio

The prio package comes with a command-line interface that can be used to
implement a privacy preserving aggregation scheme. The two servers must be
operated independently.

In this document, we will describe a schema that is achieved through security
boundaries implemented by the operating system.

## Command list

The aggregation pipeline contains four separate stages.

* `prio verify1` - Decode a batch of shares.
* `prio verify2` - Verify a batch of SNIPs (secret-shared non-interactive proof)
* `prio aggregate` - Generate an aggregate share from a batch of verified SNIPs
* `prio publish` - Generate a final aggregate for publishing

The following options are shared across all commands.

```bash
--server-id                 [REQUIRED]
--public-key-internal       [REQUIRED]
--public-key-external       [REQUIRED]
--private-key               [REQUIRED]
--batch-id                  [REQUIRED]
--n-data                    [REQUIRED]
--input-internal
--input-external
--output
```

## System setup

Two users are created on a single machine. A folder on the machine is set up
with the following hierarchy.

```bash
working/
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

User A has full access to `working/server_a/` and
`working/server_b/intermediate/external`. Likewise, User B has full access to
`working/server_b/` and `working/server_a/intermediate/external`. User A has the
following perspective of the filesystem:

```bash
working/
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

Data in `working/server_a/intermediate/internal` is copied to
`working/server_b/intermediate/external` after creation.

## Implementation of the data flow

With the command-line interface in place, we script together the pipeline
aggregating and publishing data.

```bash
# Variables that are loaded into the current scope.
#
# PRIO_SERVER_A_PUBKEY
# PRIO_SERVER_A_PVTKEY
# PRIO_SERVER_B_PUBKEY
# PRIO_BATCH_ID
# PRIO_N_DATA

workdir="working/"

# variable for interpolating common options for server A
read -d '' config_server_a << EOF
--server-id             A
--public-key-internal   ${PRIO_SERVER_A_PUBKEY}
--public-key-external   ${PRIO_SERVER_B_PUBKEY}
--private-key           ${PRIO_SERVER_A_PVTKEY}
--batch-id              ${PRIO_BATCH_ID}
--n-data                ${PRIO_N_DATA}
EOF
```

First we define some variables that are passed into the script. We read common
options into a variable to re-use across the commands.

```bash
function wait_for_data() {
    # Block until data appears in the folder specified by $1
    watchman-wait $1
}
```

We define a function that blocks until the appropriate data is returned.
[`watchman`](https://facebook.github.io/watchman/docs/watchman-wait.html) is a
cross-platform command-line utility that provides this functionality out of the
box. We may also choose to use `inotifywait` or a custom polling method.


The first stage decodes server specific data.

```bash
wait_for_data ${workdir}/server_a/raw/

prio verify1 \
    ${config_server_a} \
    --input-internal    ${workdir}/server_a/raw/* \
    --output            ${workdir}/server_a/intermediate/internal/verify1/

cp \
    ${workdir}/server_a/intermediate/internal/verify1/* \
    ${workdir}/server_b/intermediate/external/verify1/
```

The second stage processes the SNIPs.

```bash
wait_for_data ${workdir}/server_a/intermediate/external/verify1/

prio verify2 \
    ${config_server_a} \
    --input-internal    ${workdir}/server_a/intermediate/internal/verify1/* \
    --input-external    ${workdir}/server_a/intermediate/external/verify1/* \
    --output            ${workdir}/server_a/intermediate/internal/verify2/

cp \
    ${workdir}/server_a/intermediate/internal/verify2/* \
    ${workdir}/server_b/intermediate/external/verify2/
```

The third step aggregates the verified shares.

```bash
wait_for_data ${workdir}/server_a/intermediate/external/verify2/

prio aggregate \
    ${config_server_a} \
    --input-internal    ${workdir}/server_a/intermediate/internal/verify2/* \
    --input-external    ${workdir}/server_a/intermediate/external/verify2/* \
    --output            ${workdir}/server_a/intermediate/aggregate/

cp \
    ${workdir}/server_a/intermediate/internal/aggregate/* \
    ${workdir}/server_b/intermediate/external/aggregate/
```

The final share publishes a total generated from the sum of the aggregates shares.

```bash
wait_for_data ${workdir}/server_a/intermediate/external/aggregate/

prio publish \
    ${config_server_a} \
    --input-internal    ${workdir}/server_a/intermediate/internal/aggregate/* \
    --input-external    ${workdir}/server_a/intermediate/external/aggregate/* \
    --output            ${workdir}/server_a/processed/
```

This concludes the script. If implemented correctly, two scripts in separate processes should complete a full pass of data processing.

## Data format and schema

The `prio` command-line tool handles batches of encoded data that are formatted as newline-delimited JSON payload. Each line contain a payload that validates against a known JSON Schema.

As an example, the intermediate data formats are a wrapper around the serialized payloads. The payloads are treated as base64-encoded binary blobs with an associated `id` for matching corresponding payloads.

```json
{
    "$schema": "http://json-schema.org/schema#",
    "type": "object",
    "properties": {
        "id": {
            "pattern": "^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$",
            "type": "string"
        },
        "payload": {
            "type": "string"
        }
    }
}
```

An example payload may take the following form:

```
{"id": "e7f2d398-9d42-4b03-aab9-67a9137e669d", "payload": "ZTdmMmQzOTgtOWQ0Mi00YjAzLWFhYjktNjdhOTEzN2U2Njlk"}
{"id": "8176b1b2-0ad3-4bd0-bc2a-60bba996a6a3", "payload": "ODE3NmIxYjItMGFkMy00YmQwLWJjMmEtNjBiYmE5OTZhNmEz"}
{"id": "dfd27f25-8f5a-4ed4-880e-02fb967855ec", "payload": "ZGZkMjdmMjUtOGY1YS00ZWQ0LTg4MGUtMDJmYjk2Nzg1NWVj"}
{"id": "bd57e8bb-65f3-44a6-a0fe-456863139c23", "payload": "YmQ1N2U4YmItNjVmMy00NGE2LWEwZmUtNDU2ODYzMTM5YzIz"}
{"id": "50cb4a3e-79d9-4097-987b-170325c5f544", "payload": "NTBjYjRhM2UtNzlkOS00MDk3LTk4N2ItMTcwMzI1YzVmNTQ0"}
```
