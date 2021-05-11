#!/usr/bin/env bash

set -euo pipefail
set -x

TARGET="minio"

function get_key {
    local key=$1
    jq -r ".$key" minio-config.json
}

mc config host add $TARGET \
    $BUCKET_INTERNAL_ENDPOINT \
    $BUCKET_INTERNAL_ACCESS_KEY \
    $BUCKET_INTERNAL_SECRET_KEY

for type in private shared ingest; do
    bucket="$(get_key "buckets.$type")"
    mc mb $TARGET/$bucket
done

# the internal user is the admin, and doesn't need a policy applied
for type in external ingest; do
    policy="$(get_key "policy.$type")"
    access_key="$(get_key "keys.$type.access_key")"
    secret_key="$(get_key "keys.$type.secret_key")"

    # dump policy to tmp directory
    policy_dir="/tmp/$type.json"
    echo "$policy" > "$policy_dir"

    # mc admin policy add TARGET POLICYNAME POLICYFILE
    mc admin policy add $TARGET $type $policy_dir

    # mc admin user add TARGET ACCESSKEY SECRETKEY
    mc admin user add $TARGET $access_key $secret_key

    # mc admin policy set TARGET POLICYNAME user=ACCESSKEY
    mc admin policy set $TARGET $type user=$access_key
done

echo "done setting up policies"
