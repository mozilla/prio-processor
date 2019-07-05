# Batched Processing

This example is an example of a minimal two-server aggregation scheme that
fulfils the privacy guarantees of the Prio system.

## Quickstart

```bash
# Build the containers
make build

# Run the test
make test
```

## Resources

### Generated Keys
```json
# Server A
{
    "private_key": "19DDC146FB8EE4A0B762A7DAE7E96033F87C9528DBBF8CA899CCD1DB8CD74984",
    "public_key": "445C126981113E5684D517826E508F5731A1B35485BACCD63DAA8120DD11DA78"
}

# Server B
{
    "private_key": "E3AA3CC952C8553E46E699646A9DC3CBA7E3D4C7F0779D58574ABF945E259202",
    "public_key": "01D5D4F179ED233140CF97F79594F0190528268A99A6CDF57EF0E1569E673642"
}
```

## Misc

* Generating an [s3 policy file](https://docs.aws.amazon.com/AmazonS3/latest/dev/example-policies-s3.html)
* [MinIO multi-user quickstart guide](https://docs.min.io/docs/minio-multi-user-quickstart-guide.html)
