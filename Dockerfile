FROM fedora:latest
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
    nss-devel \
    msgpack-devel

# symbolically link to name without version suffix to accomodate libprio includes
RUN ln -s /usr/include/nspr4 /usr/include/nspr
RUN ln -s /usr/include/nss3 /usr/include/nss

# install pipenv for dependency management
RUN pip install pipenv
ENV PATH="$PATH:~/.local/bin"

# inst
WORKDIR /app
ADD . /app

RUN make
RUN pipenv sync --dev
CMD make test
