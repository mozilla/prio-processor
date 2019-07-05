#!/bin/bash

# This script controls the docker-compose workflow for integration testing. The
# containers are defined in the docker-compose.yml, but are orchestrated through
# this script for verification.
#
# See: https://stackoverflow.com/questions/40907954/terminate-docker-compose-when-test-container-finishes

set -euo pipefail

docker-compose up -d

# Add a cleanup handler for the exit signal
function cleanup {
    docker-compose down
}
trap cleanup EXIT

# Start server A
docker-compose run server_a scripts/server.sh &
server_a_pid=$!

# Start server B
docker-compose run server_b scripts/server.sh &
server_b_pid=$!

# Copy data into the appropriate buckets
docker-compose run client scripts/client.sh

# Return the exit code of the backgrounded docker-compose container. Since
# `wait` is a blocking function, a failure in server B will not be detected
# until timeout in server A. 
wait $server_a_pid
wait $server_b_pid

docker-compose run client scripts/check-aggregates.sh
