FROM centos:7
LABEL maintainer="amiyaguchi@mozilla.com"

ENV LANG en_US.utf8

COPY ./google-cloud-sdk.repo /etc/yum.repos.d/
RUN yum install -y epel-release \
        && yum install -y \
        nss \
        nspr \
        msgpack \
        python36 \
        java-1.8.0-openjdk \
        google-cloud-sdk \
        rsync \
        jq \
        parallel \
        which \
        tree \
        wget \
        && yum clean all \
        && rm -rf /var/cache/yum

RUN gcloud config set disable_usage_reporting true

RUN groupadd --gid 10001 app && \
        useradd -g app --uid 10001 --shell /usr/sbin/nologin --create-home \
        --home-dir /app app

WORKDIR /app
COPY requirements.txt requirements-dev.txt ./

ENV PATH="$PATH:~/.local/bin"
RUN python3 -m ensurepip && \
        pip3 install --upgrade pip wheel && \
        pip3 install -r requirements.txt -r requirements-dev.txt

ENV SPARK_HOME=/usr/local/lib/python3.6/site-packages/pyspark
ENV PYSPARK_PYTHON=python3

# Install libraries for interacting with cloud storage.
# NOTE: this is only necessary when running outside of dataproc to use GCS
# directly. A similar approach would need to be done to acommodate s3a. This
# may be more appropriate to add to the image build instead of fetching at
# runtime.
# https://cloud.google.com/dataproc/docs/concepts/connectors/cloud-storage
RUN gsutil cp gs://hadoop-lib/gcs/gcs-connector-hadoop3-latest.jar "${SPARK_HOME}/jars"
RUN wget --directory-prefix $SPARK_HOME/jars/ https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.2.0/hadoop-aws-3.2.0.jar
RUN wget --directory-prefix $SPARK_HOME/jars/ https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.11.375/aws-java-sdk-bundle-1.11.375.jar

# Use the MinIO client for cross platform behavior, even with self-hosting
RUN wget --directory-prefix /usr/local/bin https://dl.min.io/client/mc/release/linux-amd64/mc
RUN chmod +x /usr/local/bin/mc

ADD . /app

# Symlink the spark config into SPARK_HOME so it can be updated via volume mounts
RUN ln -s /app/config/spark ${SPARK_HOME}/conf

# build the binary egg for distribution on Spark clusters
RUN python3 setup.py bdist_egg && pip3 install -e .
RUN chown -R app:app /app

USER app
CMD pytest -v tests && \
        scripts/test-cli-integration && \
        prio --help && \
        prio-processor --help
