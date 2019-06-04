#!/bin/bash

# Check that aggregates that are computed via client.sh and server.sh are
# correct and published to the correct location. This script should be run
# inside of the client container.

set -euo pipefail
set -x

: ${MINIO_ACCESS_KEY?}
: ${MINIO_SECRET_KEY?}
: ${BUCKET_SERVER_A?}
: ${BUCKET_SERVER_B?}

TARGET="minio"
mc config host add $TARGET http://minio:9000 ${MINIO_ACCESS_KEY} ${MINIO_SECRET_KEY}

[[ $(mc cat $TARGET/$BUCKET_SERVER_A/processed/part-0.ndjson) == "[3, 2, 1]" ]]
[[ $(mc cat $TARGET/$BUCKET_SERVER_B/processed/part-0.ndjson) == "[3, 2, 1]" ]]

[[ $(mc cat $TARGET/$BUCKET_SERVER_A/processed/part-1.ndjson) == "[4, 2, 4]" ]]
[[ $(mc cat $TARGET/$BUCKET_SERVER_B/processed/part-1.ndjson) == "[4, 2, 4]" ]]

[[ $(mc cat $TARGET/$BUCKET_SERVER_A/processed/part-2.ndjson) == "[7, 3, 1]" ]]
[[ $(mc cat $TARGET/$BUCKET_SERVER_B/processed/part-2.ndjson) == "[7, 3, 1]" ]]
