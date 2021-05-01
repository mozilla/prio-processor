# Testing configuration for v4 containers

This directory contains terraform configuration to bring relevant resources for
an integration test of the prio-processor v4.x containers.

To create a new project that uses the same configuration, change the terraform
backend appropriately. Here, the state is placed into a storage bucket that has
been created beforehand. Ensure the project has also been created. Then:

```bash
cd terraform

# if you're choosing a different project or change any modules
terraform init

# apply any changes
terraform apply
```

To configure the tests:

```bash
# There is a maximum of 10 keys per service account. This script doesn't
# handle key rotations, so disable old keys as necessary.
scripts/generate-service-account-keys

# generate new keys (or alternatively copy .env.template files to their .env locations)
scripts/generate-dotenv
```

The above commands only need to be run once. To run the tests:

```bash
# run the integration script
scripts/integrate

# clean up the buckets
scripts/cleanup
```

In order to be agnostic to the storage provider, MinIO and `mc` are used for
transferring data between the different parties. A GCS gateway is provisioned
for each container that is associated with a service account. Each MinIO
container has an HTTP entrypoint for browsing files that can be found on the
following locations:

- http://localhost:9001 for the ingestion server
- http://localhost:9002 for server a
- http://localhost:9003 for server b
