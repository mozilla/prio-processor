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

TARGET="minio"

mc config host add $TARGET http://minio:9000 $MINIO_ACCESS_KEY $MINIO_SECRET_KEY --api s3v4;

cd /tmp
mkdir -p data/raw
mkdir -p data/intermediate/internal/verify1
mkdir -p data/intermediate/internal/verify2
mkdir -p data/intermediate/internal/aggregate
mkdir -p data/intermediate/external/verify1
mkdir -p data/intermediate/external/verify2
mkdir -p data/intermediate/external/aggregate
mkdir -p data/processed
cd data


function trigger_on_event() {
    path=$(( mc watch --json $1 & ) | head -n 1 | jq -r '.events.path')
    # Remove the url portion
    echo "$TARGET/${path##http://minio:9000/}"
}

function poll_for_data() {
    retries=0
    while ! mc stat $1 &>/dev/null; do
        sleep 2;
        : $((retries++))
        if $((retries > 5)); then
            exit 1
        fi
    done
}

###########################################################
# verify1
###########################################################

path=$(trigger_on_event "${TARGET}/${BUCKET_INTERNAL}/raw/")
filename=$(basename $path)

mc cp $path raw/

prio verify1 \
    --n-data $N_DATA \
    --batch-id $BATCH_ID \
    --server-id $SERVER_ID \
    --private-key-hex $PRIVATE_KEY \
    --shared-secret $SHARED_SECRET \
    --public-key-hex-internal $PUBLIC_KEY_INTERNAL \
    --public-key-hex-external $PUBLIC_KEY_EXTERNAL \
    --input raw/$filename \
    --output intermediate/internal/verify1

jq -c '.' intermediate/internal/verify1/$filename

mc cp \
    intermediate/internal/verify1/$filename \
    ${TARGET}/${BUCKET_EXTERNAL}/intermediate/external/verify1/

###########################################################
# verify2
###########################################################

path="${TARGET}/${BUCKET_INTERNAL}/intermediate/external/verify1/$filename"
poll_for_data $path
mc cp $path intermediate/external/verify1/

prio verify2 \
    --n-data $N_DATA \
    --batch-id $BATCH_ID \
    --server-id $SERVER_ID \
    --private-key-hex $PRIVATE_KEY \
    --shared-secret $SHARED_SECRET \
    --public-key-hex-internal $PUBLIC_KEY_INTERNAL \
    --public-key-hex-external $PUBLIC_KEY_EXTERNAL \
    --input raw/$filename \
    --input-internal intermediate/internal/verify1/$filename \
    --input-external intermediate/external/verify1/$filename \
    --output intermediate/internal/verify2/ \

jq -c '.' intermediate/internal/verify2/$filename

mc cp \
    intermediate/internal/verify2/$filename \
    ${TARGET}/${BUCKET_EXTERNAL}/intermediate/external/verify2/

###########################################################
# aggregate
###########################################################

path="${TARGET}/${BUCKET_INTERNAL}/intermediate/external/verify2/$filename"
poll_for_data $path
mc cp $path intermediate/external/verify2/

prio aggregate \
    --n-data $N_DATA \
    --batch-id $BATCH_ID \
    --server-id $SERVER_ID \
    --private-key-hex $PRIVATE_KEY \
    --shared-secret $SHARED_SECRET \
    --public-key-hex-internal $PUBLIC_KEY_INTERNAL \
    --public-key-hex-external $PUBLIC_KEY_EXTERNAL \
    --input raw/$filename \
    --input-internal intermediate/internal/verify2/$filename \
    --input-external intermediate/external/verify2/$filename \
    --output intermediate/internal/aggregate/

jq -c '.' intermediate/internal/aggregate/$filename

mc cp \
    intermediate/internal/aggregate/$filename \
    ${TARGET}/${BUCKET_EXTERNAL}/intermediate/external/aggregate/

###########################################################
# publish
###########################################################

path="${TARGET}/${BUCKET_INTERNAL}/intermediate/external/aggregate/$filename"
poll_for_data $path
mc cp $path intermediate/external/aggregate/

prio publish \
    --n-data $N_DATA \
    --batch-id $BATCH_ID \
    --server-id $SERVER_ID \
    --private-key-hex $PRIVATE_KEY \
    --shared-secret $SHARED_SECRET \
    --public-key-hex-internal $PUBLIC_KEY_INTERNAL \
    --public-key-hex-external $PUBLIC_KEY_EXTERNAL \
    --input-internal intermediate/internal/aggregate/$filename \
    --input-external intermediate/external/aggregate/$filename \
    --output processed/

jq -c '.' processed/$filename
