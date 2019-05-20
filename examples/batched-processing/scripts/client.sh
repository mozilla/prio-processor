#!/bin/bash

set -eou pipefail
set -x

: ${N_DATA?}
: ${BATCH_ID?}
: ${PUBLIC_KEY_SERVER_A?}
: ${PUBLIC_KEY_SERVER_B?}

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
    --n-data ${N_DATA} \
    --batch-id ${BATCH_ID} \
    --public-key-hex-internal ${PUBLIC_KEY_SERVER_A} \
    --public-key-hex-external ${PUBLIC_KEY_SERVER_B} \
    --input data.ndjson \
    --output-A ${BUCKET_SERVER_A}/raw/ \
    --output-B ${BUCKET_SERVER_B}/raw/

jq -c '.' ${BUCKET_SERVER_A}/raw/data.ndjson
jq -c '.' ${BUCKET_SERVER_B}/raw/data.ndjson

mc cp --recursive $BUCKET_SERVER_A $TARGET
mc cp --recursive $BUCKET_SERVER_B $TARGET
