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

function wait_for_data() {
    path=$(( mc watch --json $1 & ) | head -n 1 | jq -r '.events.path')
    # Remove the url portion
    echo "minio/${path##http://minio:9000/}"
}

sleep 3
mkdir -p data/raw
mkdir -p data/intermediate/internal/verify1
mkdir -p data/intermediate/internal/verify2
mkdir -p data/intermediate/internal/aggregate
mkdir -p data/intermediate/external/verify1
mkdir -p data/intermediate/external/verify2
mkdir -p data/intermediate/external/aggregate
mkdir -p data/processed
cd data

###########################################################
# verify1
###########################################################

path=$(wait_for_data "minio/$BUCKET_INTERNAL/raw/")
filename=$(basename $path)

mc cp $path raw/

prio verify1 \
    --n-data $N_DATA \
    --batch-id $BATCH_ID \
    --server-id $SERVER_ID \
    --private-key $PRIVATE_KEY \
    --shared-secret $SHARED_SECRET \
    --public-key-internal $PUBLIC_KEY_INTERNAL \
    --public-key-external $PUBLIC_KEY_EXTERNAL \
    --input raw/$filename \
    --output intermediate/internal/verify1

jq -c '.' intermediate/internal/verify1/$filename

cp \
    ${BUCKET_INTERNAL}/intermediate/internal/verify1/$filename \
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
    --input ${BUCKET_INTERNAL}/raw/$filename \
    --input-internal ${BUCKET_INTERNAL}/intermediate/internal/verify1/$filename \
    --input-external ${BUCKET_INTERNAL}/intermediate/external/verify1/$filename \
    --output ${BUCKET_INTERNAL}/intermediate/internal/verify2/ \

jq -c '.' ${BUCKET_INTERNAL}/intermediate/internal/verify2/$filename

cp \
    ${BUCKET_INTERNAL}/intermediate/internal/verify2/$filename \
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
    --input ${BUCKET_INTERNAL}/raw/$filename \
    --input-internal ${BUCKET_INTERNAL}/intermediate/internal/verify2/$filename \
    --input-external ${BUCKET_INTERNAL}/intermediate/external/verify2/$filename \
    --output ${BUCKET_INTERNAL}/intermediate/internal/aggregate/

jq -c '.' ${BUCKET_INTERNAL}/intermediate/internal/aggregate/$filename

cp \
    ${BUCKET_INTERNAL}/intermediate/internal/aggregate/$filename \
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
    --input-internal ${BUCKET_INTERNAL}/intermediate/internal/aggregate/$filename \
    --input-external ${BUCKET_INTERNAL}/intermediate/external/aggregate/$filename \
    --output ${BUCKET_INTERNAL}/processed/

jq -c '.' ${BUCKET_INTERNAL}/processed/$filename
