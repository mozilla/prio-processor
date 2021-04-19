# Server B

This is an example server B deployment that is entirely self-hosted. It uses
docker-compose for coordinating the services and runs MinIO for all the
object-store related activities.

Ensure the subdomain of the minio server begins with a valid format for boto
support (see [this snippet for
details](https://github.com/boto/boto/blob/91ba037e54ef521c379263b0ac769c66182527d7/boto/auth.py#L655-L665)).
The internal address of the minio server is `s3.minio:80`.

Note that the due to [boto/boto#2623](https://github.com/boto/boto/issues/2623),
the port of the s3 enpoint must be either 80 or 443. This is a requirement

```
# test that the minio server is online
mc alias set minio http://minio:9000 server-b password

mc ls minio
mc ls minio/server-b-internal

# copy the a file for testing the s3a adapter
mc cp config/test-small.json minio/server-b-internal

pyspark
df = spark.read.json("s3a://server-b-internal/test-small.json", multiLine=True)
```

https://docs.min.io/docs/deploy-minio-on-docker-compose.html
