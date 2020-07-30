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
mc config host add $TARGET http://minio:9000 ${MINIO_ACCESS_KEY} ${MINIO_SECRET_KEY}

# The bucket name is used for the local file directory and for the remote minio
# bucket.
cd /tmp
output_a=$BUCKET_SERVER_A/raw
output_b=$BUCKET_SERVER_B/raw
mkdir -p $output_a
mkdir -p $output_b

jq -c '{payload: .}' <<EOF >part-0.ndjson
[1, 0, 0]
[1, 1, 0]
[1, 1, 1]
EOF

jq -c '{payload: .}' <<EOF >part-1.ndjson
[1, 0, 1]
[1, 1, 1]
[1, 0, 1]
[1, 1, 1]
EOF

jq -c '{payload: .}' <<EOF >part-2.ndjson
[1, 0, 0]
[1, 0, 0]
[1, 0, 0]
[1, 0, 0]
[1, 1, 0]
[1, 1, 0]
[1, 1, 1]
EOF

for filename in $(find . -name "*.ndjson"); do
    prio encode-shares \
        --input $filename \
        --output-A $output_a \
        --output-B $output_b

    jq -c '.' $output_a/$filename
    jq -c '.' $output_b/$filename
done

mc cp --recursive $output_a/ $TARGET/$output_a/
mc cp --recursive $output_b/ $TARGET/$output_b/

touch _SUCCESS
mc cp _SUCCESS $TARGET/$output_a/_SUCCESS
mc cp _SUCCESS $TARGET/$output_b/_SUCCESS
