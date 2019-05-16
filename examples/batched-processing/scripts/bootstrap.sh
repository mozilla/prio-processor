#!/bin/sh

set -euo pipefail
set -x

TARGET="minio"

mc config host add $TARGET http://minio:9000 admin password
mc mb $TARGET/server-a
mc mb $TARGET/server-b

# mc admin policy add TARGET POLICYNAME POLICYFILE
mc admin policy add $TARGET server-a policy/server-a.json
mc admin policy add $TARGET server-b policy/server-b.json

# mc admin user add TARGET ACCESSKEY SECRETKEY POLICYNAME
mc admin user add $TARGET server-a password server-a
mc admin user add $TARGET server-b password server-b
