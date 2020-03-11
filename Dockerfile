FROM centos:7 as development
LABEL maintainer="amiyaguchi@mozilla.com"

ENV LANG en_US.utf8

RUN yum install -y epel-release \
        && yum install -y \
                which \
                make \
                gcc \
                clang \
                scons \
                swig \
                python36-devel \
                python36 \
                nss-devel \
                msgpack-devel \
                jq \
                java-1.8.0-openjdk \
                parallel \
                tree \
        && yum clean all \
        && rm -rf /var/cache/yum

# symbolically link to name without version suffix for libprio
RUN ln -s /usr/include/nspr4 /usr/include/nspr \
    && ln -s /usr/include/nss3 /usr/include/nss

# prepare the environment for testing in development
ENV PATH="$PATH:~/.local/bin"
RUN python3 -m ensurepip && pip3 install tox setuptools wheel black

RUN curl https://sdk.cloud.google.com | bash
ENV PATH="$PATH:~/google-cloud-sdk/bin"
RUN gcloud config set disable_usage_reporting true

# install the app
WORKDIR /app
ADD . /app

# Build the prio wrapper
WORKDIR /app/prio
RUN make

WORKDIR /app
RUN pip3 install -r requirements.txt

ENV SPARK_HOME=/usr/local/lib/python3.6/site-packages/pyspark
ENV PYSPARK_PYTHON=python3

WORKDIR /app
CMD cd prio && tox && cd .. && \
        cd processor && tox && cd .. \
        prio/scripts/test-cli-integration && \
        prio --help && \
        prio-processor --help


# Define the production container
FROM centos:7 as production
ENV LANG en_US.utf8

RUN yum install -y epel-release \
    && yum install -y which nss nspr msgpack jq python36 parallel java-1.8.0-openjdk \
    && yum clean all \
    && rm -rf /var/cache/yum

RUN groupadd --gid 10001 app && \
    useradd -g app --uid 10001 --shell /usr/sbin/nologin --create-home \
        --home-dir /app app

WORKDIR /app
COPY --from=development /app .
RUN chown -R 10001:10001 /app

ENV PATH="$PATH:~/.local/bin"
RUN python3 -m ensurepip && pip3 install -r requirements.txt

ENV SPARK_HOME=/usr/local/lib/python3.6/site-packages/pyspark
ENV PYSPARK_PYTHON=python3

USER app
RUN curl https://sdk.cloud.google.com | bash
ENV PATH="$PATH:~/google-cloud-sdk/bin"
RUN gcloud config set disable_usage_reporting true

CMD pytest prio && \
        prio/scripts/test-cli-integration && \
        prio --help && \
        prio-processor --help

# References
# https://docs.docker.com/develop/develop-images/multistage-build/
