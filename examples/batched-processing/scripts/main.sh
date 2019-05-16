#!/bin/bash

set -eou pipefail
set -x

: ${N_DATA?}
: ${BATCH_ID?}
: ${SERVER_ID}
: ${SHARED_SECRET?}
: ${PRIVATE_KEY?}
: ${PUBLIC_KEY_INTERNAL?}
: ${PUBLIC_KEY_EXTERNAL?}

: ${MINIO_ACCESS_KEY?}
: ${MINIO_SECRET_KEY?}
: ${BUCKET_INTERNAL?}
: ${BUCKET_EXTERNAL?}

mc config host add minio http://minio:9000 $MINIO_ACCESS_KEY $MINIO_SECRET_KEY --api s3v4;

###########################################################
# verify1
###########################################################

path=$(( mc watch --json & ) | head -n 1 | jq -r '.events.path')

prio verify1 \
    --n-data $N_DATA \
    --batch-id $BATCH_ID \
    --server-id $SERVER_ID \
    --private-key $PRIVATE_KEY \
    --shared-secret $SHARED_SECRET \
    --public-key-internal $PUBLIC_KEY_INTERNAL \
    --public-key-external $PUBLIC_KEY_EXTERNAL \
    --input ${BUCKET_INTERNAL}/raw/data.ndjson \
    --output ${BUCKET_INTERNAL}/intermediate/internal/verify1

jq -c '.' ${BUCKET_INTERNAL}/intermediate/internal/verify1/data.ndjson

cp \
    ${BUCKET_INTERNAL}/intermediate/internal/verify1/data.ndjson \
    ${BUCKET_EXTERNAL}/intermediate/external/verify1/

###########################################################
# verify2
###########################################################

prio verify2 \
    --n-data $N_DATA \
    --batch-id $BATCH_ID \
    --server-id $SERVER_ID \
    --private-key $PRIVATE_KEY \
    --shared-secret $SHARED_SECRET \
    --public-key-internal $PUBLIC_KEY_INTERNAL \
    --public-key-external $PUBLIC_KEY_EXTERNAL \
    --input ${BUCKET_INTERNAL}/raw/data.ndjson \
    --input-internal ${BUCKET_INTERNAL}/intermediate/internal/verify1/data.ndjson \
    --input-external ${BUCKET_INTERNAL}/intermediate/external/verify1/data.ndjson \
    --output ${BUCKET_INTERNAL}/intermediate/internal/verify2/ \

jq -c '.' ${BUCKET_INTERNAL}/intermediate/internal/verify2/data.ndjson

cp \
    ${BUCKET_INTERNAL}/intermediate/internal/verify2/data.ndjson \
    ${BUCKET_EXTERNAL}/intermediate/external/verify2/

###########################################################
# aggregate
###########################################################

prio aggregate \
    --n-data $N_DATA \
    --batch-id $BATCH_ID \
    --server-id $SERVER_ID \
    --private-key $PRIVATE_KEY \
    --shared-secret $SHARED_SECRET \
    --public-key-internal $PUBLIC_KEY_INTERNAL \
    --public-key-external $PUBLIC_KEY_EXTERNAL \
    --input ${BUCKET_INTERNAL}/raw/data.ndjson \
    --input-internal ${BUCKET_INTERNAL}/intermediate/internal/verify2/data.ndjson \
    --input-external ${BUCKET_INTERNAL}/intermediate/external/verify2/data.ndjson \
    --output ${BUCKET_INTERNAL}/intermediate/internal/aggregate/

jq -c '.' ${BUCKET_INTERNAL}/intermediate/internal/aggregate/data.ndjson

cp \
    ${BUCKET_INTERNAL}/intermediate/internal/aggregate/data.ndjson \
    ${BUCKET_EXTERNAL}/intermediate/external/aggregate/

###########################################################
# publish
###########################################################

prio publish \
    --n-data $N_DATA \
    --batch-id $BATCH_ID \
    --server-id $SERVER_ID \
    --private-key $PRIVATE_KEY \
    --shared-secret $SHARED_SECRET \
    --public-key-internal $PUBLIC_KEY_INTERNAL \
    --public-key-external $PUBLIC_KEY_EXTERNAL \
    --input-internal ${BUCKET_INTERNAL}/intermediate/internal/aggregate/data.ndjson \
    --input-external ${BUCKET_INTERNAL}/intermediate/external/aggregate/data.ndjson \
    --output ${BUCKET_INTERNAL}/processed/

jq -c '.' ${BUCKET_INTERNAL}/processed/data.ndjson
