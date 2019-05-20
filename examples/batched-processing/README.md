# Batched Processing

This example is an example of a minimal two-server aggregation scheme that
fulfils the privacy guarantees of the Prio system.

## Building

docker build -t prio-dev ../..


# Resources

The last example:
https://docs.aws.amazon.com/AmazonS3/latest/dev/example-policies-s3.html


# TODO

* Fix volume mounting so each server has an independent working directory
* Add testing document that is automatically written into the raw directories
* Update triggering logic to work based on `_SUCCESS` files for Hadoop compatibility
* Add a million document test set