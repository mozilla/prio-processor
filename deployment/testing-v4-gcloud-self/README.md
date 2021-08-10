# Testing configuration for v4 containers

This directory contains terraform configuration to bring relevant resources for
an integration test of the prio-processor v4.x containers.

To create a new environment that uses the same configuration, change the
terraform backend appropriately. Here, the state is placed into a storage bucket
that has been created beforehand. Ensure the GCP project has also been created.
Then run the terraform for the ingestion and server A resource:

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


# generate minio configuration for server B
scripts/generate-minio-configuration

# copy configuration into server B's compose directory
scripts/copy-minio-configuration


# generate new keys (or alternatively copy .env.template files to their .env locations)
scripts/generate-dotenv
```

The above commands only need to be run once. To run the tests:

```bash
# run the integration script
scripts/integrate

# if at any time there is a failure in the containers, there's a separate script
# for bringing all of the services down.
scripts/down

# clean up the buckets
scripts/cleanup
```

In order to be agnostic to the storage provider, MinIO and `mc` are used for
transferring data between the different parties. A GCS gateway is provisioned
for each container that is associated with a service account. Each MinIO
container has an HTTP entrypoint for browsing files that can be found on the
following locations:

- http://localhost:9001 for ingestion's gcs gateway
- http://localhost:9002 for server a's gcs gateway
- http://localhost:9003 for server b's gcs gateway
- http://localhost:9004 for server b's minio service

## Adapting compose files for external host

The test in this directory assumes that the MinIO service for server b is hosted
on the local machine. The test takes advantage of docker's networking
capabilities for resolving the name of server b's MinIO server from the ingest
and server a compose files.

Concretely, this means specifying the network as external and adding it to the
main application.

```yaml
networks:
  testing-v4-gcloud-self-b_default:
    external: true

services:
  app:
    networks:
      - default
      - testing-v4-gcloud-self-b_default
  # rest of the configuration....
```

Server b's composed service must exist on the local machine for any of the other
composed services to come online so `http://minio-b:9000` is reachable.

Remove references to `testing-v4-gcloud-self-b_default` from the ingest and
server-b configuration files. Then set `BUCKET_EXTERNAL_ENDPOINT` to the IP
address of the server-b's files.

## Adapting environment with manually generated configuration

A complete integration test may involve more multiple operators. To ensure secrets
are privy to only a single party, the `.env` files may be manually edited.

### Generating new Prio keys

To generate new keys for Prio, run the following command:

```bash
docker run --rm -it mozilla/prio-processor:latest prio keygen
```

Replace the following keys in your `.env` file with `.private_key` and `.public_key`

```bash
PRIVATE_KEY_HEX=...
PUBLIC_KEY_HEX_INTERNAL=...
```

Provide the public key to the partner in the following format:

```bash
PUBLIC_KEY_HEX_EXTERNAL=...
```

### Generating new MinIO keys

In server B, to generate new buckets and access keys, run the following command:

```bash
scripts/generate-minio-configuration
```

#### Modifying internal environment variables

This will create a new file called `.secrets/minio-config.json` with bucket
names, policy files, and access keys. Replace the following variables in the
`.env` file with values from the configuration file:

```bash
BUCKET_INTERNAL_INGEST=...      # .buckets.ingest
BUCKET_INTERNAL_PRIVATE=...     # .buckets.private
BUCKET_INTERNAL_SHARED=...      # .buckets.shares
BUCKET_INTERNAL_ACCESS_KEY=...  # .keys.internal.access_key
BUCKET_INTERNAL_SECRET_KEY=...  # .keys.internal.secret_key

# NOTE: the external keys are the same as the internal keys because access to
# server A is being proxied through the minio instance. Therefore, the proxy
# should be configured with a keypair known only to server B.
BUCKET_EXTERNAL_ACCESS_KEY=...  # .keys.internal.access_key
BUCKET_EXTERNAL_SECRET_KEY=...  # .keys.internal.secret_key
```

The default endpoint of `http://minio-b:9000` will suffice for local access by
the application.

Before providing variables for the external and ingestion services, ensure MinIO
is available to the public internet. By default, the MinIO service is made
available to the host on port 9004. Forward this port to and provide the
following as the endpoint: `http://{host}:{port}`. Alternatively, change port
9004 to 80. It may be preferable to provide this [via reverse-proxy ala
NGINX](https://docs.min.io/docs/setup-nginx-proxy-with-minio.html). If using a
reverse proxy, [ensure that host
headers](https://github.com/minio/minio/issues/7936) are being proxied
correctly.

#### Providing external partners with environment variables

The following environment variables are named from the perspective of the
running server. Create a new text file with the following variables for the
ingestion service and send them to the partner via a secured channel:

```bash
PUBLIC_KEY_HEX_EXTERNAL=...     # public key of server B
BUCKET_EXTERNAL_INGEST=...      # .buckets.ingest
BUCKET_EXTERNAL_ACCESS_KEY=...  # .keys.ingest.access_key
BUCKET_EXTERNAL_SECRET_KEY=...  # .keys.ingest.secret_key
BUCKET_EXTERNAL_ENDPOINT=...    # endpoint computed above
```

Create a new text file with the following variables for server A and send them
to the partner via a secured channel.

```bash
PUBLIC_KEY_HEX_EXTERNAL=...     # public key of server B
BUCKET_EXTERNAL_SHARED=...      # .buckets.shared
BUCKET_EXTERNAL_ACCESS_KEY=...  # .keys.external.access_key
BUCKET_EXTERNAL_SECRET_KEY=...  # .keys.external.secret_key
BUCKET_EXTERNAL_ENDPOINT=...    # endpoint computed above
```
