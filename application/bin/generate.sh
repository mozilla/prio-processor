#!/bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# This scripts generates data for testing the pipeline.

set -eou pipefail

: "${N_DATA?}"
: "${BATCH_ID?}"
: "${PUBLIC_KEY_HEX_INTERNAL?}"
: "${PUBLIC_KEY_HEX_EXTERNAL?}"

: "${GCP_CREDENTIALS_INTERNAL?}"
: "${GCP_CREDENTIALS_EXTERNAL?}"
: "${BUCKET_INTERNAL_PRIVATE?}"
: "${BUCKET_EXTERNAL_PRIVATE?}"

function generate_data() {
    python -c "print([int(x % 3 == 0 or x % 5 == 0) for x in range(${N_DATA})])"
}


function main() {
    cd /tmp
    mkdir -p server_a/raw
    mkdir -p server_b/raw

    for i in {1..5}; do
        filename="part-$i.ndjson"
        for ((j=0; j < i; j++)); do
            generate_data >> $filename
        done
        prio encode-shares \
            --input $filename \
            --output-A server_a/raw \
            --output-B server_b/raw
    done

    gcloud auth activate-service-account --key-file "${GCP_CREDENTIALS_INTERNAL}"
    gsutil cp -r server_b/raw "gs://${BUCKET_INTERNAL_PRIVATE}/raw"

    gcloud auth activate-service-account --key-file "${GCP_CREDENTIALS_EXTERNAL}"
    gsutil cp -r server_b/raw "gs://${BUCKET_EXTERNAL_PRIVATE}/raw"
}

main "$@"
