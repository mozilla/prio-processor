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

# install spark as the non-root user
ARG SPARK_VERSION="3.0.1"
ENV SPARK_DOWNLOAD_MIRROR="http://www.gtlib.gatech.edu/pub"
ENV SPARK_DOWNLOAD_URL=${SPARK_DOWNLOAD_MIRROR}/apache/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop2.7.tgz
ENV SPARK_HOME="/opt/spark"
ENV PYSPARK_PYTHON="python3"

WORKDIR /opt
RUN curl ${SPARK_DOWNLOAD_URL} | tar xz
RUN ln -s /opt/spark-${SPARK_VERSION}-bin-hadoop2.7 ${SPARK_HOME}
RUN chown -R app:app /opt
ENV PATH=${PATH}:${SPARK_HOME}/sbin
# spark UI
EXPOSE 8080

WORKDIR /app
COPY requirements.txt requirements-dev.txt ./

ENV PATH="$PATH:~/.local/bin"
RUN python3 -m ensurepip && \
        pip3 install --upgrade pip && \
        pip3 install -r requirements.txt -r requirements-dev.txt

ADD . /app
# build the binary egg for distribution on Spark clusters
RUN python3 setup.py bdist_egg && pip3 install -e .
RUN chown -R app:app /app

USER app
CMD pytest -v tests && \
        scripts/test-cli-integration && \
        prio --help && \
        prio-processor --help
