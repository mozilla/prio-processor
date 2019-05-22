# Batched Processing

This example is an example of a minimal two-server aggregation scheme that
fulfils the privacy guarantees of the Prio system.

## Building

docker build -t prio-dev ../..


# Resources

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

The last example:
https://docs.aws.amazon.com/AmazonS3/latest/dev/example-policies-s3.html


# TODO

* Update triggering logic to work based on `_SUCCESS` files for Hadoop compatibility
* Add a million document test set