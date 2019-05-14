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

###########################################################
# verify1
###########################################################

python -m prio verify1 \
    --n-data $N_DATA \
    --batch-id $BATCH_ID \
    --server-id $SERVER_ID \
    --private-key $PRIVATE_KEY \
    --shared-secret $SHARED_SECRET \
    --public-key-internal $PUBLIC_KEY_INTERNAL \
    --public-key-external $PUBLIC_KEY_EXTERNAL \
    --input working/server_a/raw/data.ndjson \
    --output working/server_a/intermediate/internal/verify1

jq -c '.' working/server_a/intermediate/internal/verify1/data.ndjson

cp \
    working/server_a/intermediate/internal/verify1/data.ndjson \
    working/server_b/intermediate/external/verify1/

###########################################################
# verify2
###########################################################

python -m prio verify2 \
    --n-data $N_DATA \
    --batch-id $BATCH_ID \
    --server-id $SERVER_ID \
    --private-key $PRIVATE_KEY \
    --shared-secret $SHARED_SECRET \
    --public-key-internal $PUBLIC_KEY_INTERNAL \
    --public-key-external $PUBLIC_KEY_EXTERNAL \
    --input working/server_a/raw/data.ndjson \
    --input-internal working/server_a/intermediate/internal/verify1/data.ndjson \
    --input-external working/server_a/intermediate/external/verify1/data.ndjson \
    --output working/server_a/intermediate/internal/verify2/ \

jq -c '.' working/server_a/intermediate/internal/verify2/data.ndjson

cp \
    working/server_a/intermediate/internal/verify2/data.ndjson \
    working/server_b/intermediate/external/verify2/

###########################################################
# aggregate
###########################################################

python -m prio aggregate \
    --n-data $N_DATA \
    --batch-id $BATCH_ID \
    --server-id $SERVER_ID \
    --private-key $PRIVATE_KEY \
    --shared-secret $SHARED_SECRET \
    --public-key-internal $PUBLIC_KEY_INTERNAL \
    --public-key-external $PUBLIC_KEY_EXTERNAL \
    --input working/server_a/raw/data.ndjson \
    --input-internal working/server_a/intermediate/internal/verify2/data.ndjson \
    --input-external working/server_a/intermediate/external/verify2/data.ndjson \
    --output working/server_a/intermediate/internal/aggregate/

jq -c '.' working/server_a/intermediate/internal/aggregate/data.ndjson

cp \
    working/server_a/intermediate/internal/aggregate/data.ndjson \
    working/server_b/intermediate/external/aggregate/

###########################################################
# publish
###########################################################

python -m prio publish \
    --n-data $N_DATA \
    --batch-id $BATCH_ID \
    --server-id $SERVER_ID \
    --private-key $PRIVATE_KEY \
    --shared-secret $SHARED_SECRET \
    --public-key-internal $PUBLIC_KEY_INTERNAL \
    --public-key-external $PUBLIC_KEY_EXTERNAL \
    --input-internal working/server_a/intermediate/internal/aggregate/data.ndjson \
    --input-external working/server_a/intermediate/external/aggregate/data.ndjson \
    --output working/server_a/processed/

jq -c '.' working/server_a/processed/data.ndjson
