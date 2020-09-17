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
        pip3 install --upgrade pip && \
        pip3 install -r requirements.txt -r requirements-dev.txt

ENV SPARK_HOME=/usr/local/lib/python3.6/site-packages/pyspark
ENV PYSPARK_PYTHON=python3

# Install libraries for interacting with cloud storage.
# NOTE: this is only necessary when running outside of dataproc to use GCS
# directly. A similar approach would need to be done to acommodate s3a. This
# may be more appropriate to add to the image build instead of fetching at
# runtime.
# https://cloud.google.com/dataproc/docs/concepts/connectors/cloud-storage
RUN gsutil cp gs://hadoop-lib/gcs/gcs-connector-hadoop2-latest.jar "${SPARK_HOME}/jars"

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
