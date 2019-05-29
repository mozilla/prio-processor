#!/bin/bash

set -eou pipefail
set -x

# Parameters that are read through the environment
: ${N_DATA?}
: ${BATCH_ID?}
: ${SERVER_ID}
: ${SHARED_SECRET?}
: ${PRIVATE_KEY_HEX?}
: ${PUBLIC_KEY_HEX_INTERNAL?}
: ${PUBLIC_KEY_HEX_EXTERNAL?}

: ${MINIO_ACCESS_KEY?}
: ${MINIO_SECRET_KEY?}
: ${BUCKET_INTERNAL?}
: ${BUCKET_EXTERNAL?}

TARGET="minio"

mc config host add $TARGET http://minio:9000 $MINIO_ACCESS_KEY $MINIO_SECRET_KEY --api s3v4;

cd /tmp
mkdir -p raw
mkdir -p intermediate/internal/verify1
mkdir -p intermediate/internal/verify2
mkdir -p intermediate/internal/aggregate
mkdir -p processed

# create the file that is used to notify that processing for a step is done
touch _SUCCESS


function poll_for_data() {
    set +e
    max_retries=5
    retries=0
    backoff=2
    while ! mc stat $1 &>/dev/null; do
        sleep $backoff;
        ((backoff *= 2))
        ((retries++))
        if [[ "$retries" -gt "$max_retries" ]]; then
            echo "Reached the maximum number of retries."
            exit 1
        fi
    done
    set -e
}


###########################################################
# verify1
###########################################################

input="raw"
output_internal="intermediate/internal/verify1"
output_external="intermediate/external/verify1"

path=${TARGET}/${BUCKET_INTERNAL}/$input
poll_for_data $path/_SUCCESS
mc cp --recursive $path/ $input/

filenames=$(find $input -type f -not -name "_SUCCESS" -printf "%f\n")
for filename in $filenames; do
    prio verify1 \
        --input $input/$filename \
        --output $output_internal

    jq -c '.' $output_internal/$filename
done

mc cp --recursive $output_internal/ ${TARGET}/${BUCKET_EXTERNAL}/$output_external/
mc cp _SUCCESS ${TARGET}/${BUCKET_EXTERNAL}/$output_external/

###########################################################
# verify2
###########################################################

input_internal="intermediate/internal/verify1"
input_external="intermediate/external/verify1"
output_internal="intermediate/internal/verify2"
output_external="intermediate/external/verify2"

path="${TARGET}/${BUCKET_INTERNAL}/$input_external"
poll_for_data $path/_SUCCESS
mc cp --recursive $path/ $input_external/

filenames=$(find $input_internal -type f -not -name "_SUCCESS" -printf "%f\n")
for filename in $filenames; do
    prio verify2 \
        --input $input/$filename \
        --input-internal $input_internal/$filename \
        --input-external $input_external/$filename \
        --output $output_internal

    jq -c '.' $output_internal/$filename
done

mc cp --recursive $output_internal/ ${TARGET}/${BUCKET_EXTERNAL}/$output_external/
mc cp _SUCCESS ${TARGET}/${BUCKET_EXTERNAL}/$output_external/


###########################################################
# aggregate
###########################################################

input_internal="intermediate/internal/verify2"
input_external="intermediate/external/verify2"
output_internal="intermediate/internal/aggregate"
output_external="intermediate/external/aggregate"

path="${TARGET}/${BUCKET_INTERNAL}/$input_external"
poll_for_data $path/_SUCCESS
mc cp --recursive $path/ $input_external/

filenames=$(find $input_internal -type f -not -name "_SUCCESS" -printf "%f\n")
for filename in $filenames; do
    prio aggregate \
        --input $input/$filename \
        --input-internal $input_internal/$filename \
        --input-external $input_external/$filename \
        --output $output_internal

    jq -c '.' $output_internal/$filename
done

mc cp --recursive $output_internal/ ${TARGET}/${BUCKET_EXTERNAL}/$output_external/
mc cp _SUCCESS ${TARGET}/${BUCKET_EXTERNAL}/$output_external/

###########################################################
# publish
###########################################################

input_internal="intermediate/internal/aggregate"
input_external="intermediate/external/aggregate"
output="processed"

path="${TARGET}/${BUCKET_INTERNAL}/$input_external"
poll_for_data $path/_SUCCESS
mc cp --recursive $path/ $input_external/

filenames=$(find $input_internal -type f -not -name "_SUCCESS" -printf "%f\n")
for filename in $filenames; do
    prio publish \
        --input-internal $input_internal/$filename \
        --input-external $input_external/$filename \
        --output $output

    jq -c '.' $output/$filename
done

mc cp --recursive $output/ ${TARGET}/${BUCKET_INTERNAL}/$output/
mc cp _SUCCESS ${TARGET}/${BUCKET_INTERNAL}/$output/
