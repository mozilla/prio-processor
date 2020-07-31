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

ADD . /app
USER app
CMD pytest -v tests && \
        scripts/test-cli-integration && \
        prio --help && \
        prio-processor --help

# References
# https://docs.docker.com/develop/develop-images/multistage-build/
