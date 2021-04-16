#!/bin/sh

set -euo pipefail
set -x

TARGET="minio"

mc config host add $TARGET http://proxy:80 admin password
mc mb $TARGET/server-b-internal
mc mb $TARGET/server-b-external

# mc admin policy add TARGET POLICYNAME POLICYFILE
mc admin policy add $TARGET server-a policy/server-a.json
mc admin policy add $TARGET server-b policy/server-b.json

# mc admin user add TARGET ACCESSKEY SECRETKEY
mc admin user add $TARGET server-a password
mc admin user add $TARGET server-b password

# mc admin policy set TARGET POLICYNAME user=ACCESSKEY
mc admin policy set $TARGET server-a user=server-a
mc admin policy set $TARGET server-b user=server-b
