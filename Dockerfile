FROM fedora:latest as development
MAINTAINER Anthony Miyaguchi <amiyaguchi@mozilla.com>

ENV LANG en_US.UTF-8

RUN dnf install -y \
    which \
    make \
    gcc \
    clang \
    scons \
    swig \
    python3-devel \
    python36 \
    nss-devel \
    msgpack-devel \
    jq

# symbolically link to name without version suffix to accomodate libprio includes
RUN ln -s /usr/include/nspr4 /usr/include/nspr \
    && ln -s /usr/include/nss3 /usr/include/nss

# prepare the environment for testing in development
ENV PATH="$PATH:~/.local/bin"
RUN pip3 install tox

# prepare the environment for building the production wheel
RUN python3.6 -m venv /tmp/venv
RUN /tmp/venv/bin/pip install setuptools wheel

# install the app
WORKDIR /app
ADD . /app

RUN make

# build the wheel with the python version on the production image
RUN /tmp/venv/bin/python setup.py bdist_wheel

# install the package into the current development image
RUN pip3 install .
CMD make test


# Define the production container
FROM centos:7 as production
ENV LANG en_US.utf8

RUN yum install -y epel-release \
    && yum install -y nss nspr msgpack jq python36 \
    && yum clean all \
    && rm -rf /var/cache/yum

WORKDIR /app
COPY --from=development /app .
RUN python3 -m ensurepip && pip3 install dist/prio-*.whl

CMD scripts/test-cli-integration


# References
# https://docs.docker.com/develop/develop-images/multistage-build/