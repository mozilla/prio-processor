#!/bin/bash

set -eou pipefail
set -x

# Parameters that are read through the environment
: ${N_DATA?}
: ${BATCH_ID?}
: ${PUBLIC_KEY_HEX_INTERNAL?}
: ${PUBLIC_KEY_HEX_EXTERNAL?}

: ${MINIO_ACCESS_KEY?}
: ${MINIO_SECRET_KEY?}
: ${BUCKET_SERVER_A?}
: ${BUCKET_SERVER_B?}

TARGET="minio"
mc config host add $TARGET http://minio:9000 admin password

# The bucket name is used for the local file directory and for the remote minio
# bucket.
cd /tmp
mkdir -p $BUCKET_SERVER_A/raw
mkdir -p $BUCKET_SERVER_B/raw

cat << EOF > data.ndjson
[1, 0, 0]
[1, 1, 0]
[1, 1, 1]
EOF

jq -c '.' data.ndjson

prio encode-shares \
    --input data.ndjson \
    --output-A ${BUCKET_SERVER_A}/raw/ \
    --output-B ${BUCKET_SERVER_B}/raw/

jq -c '.' ${BUCKET_SERVER_A}/raw/data.ndjson
jq -c '.' ${BUCKET_SERVER_B}/raw/data.ndjson

mc cp --recursive $BUCKET_SERVER_A $TARGET
mc cp --recursive $BUCKET_SERVER_B $TARGET
