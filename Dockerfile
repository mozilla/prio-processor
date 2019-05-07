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

ENV PATH="$PATH:~/.local/bin"
RUN pip3 install tox

# install wait-for for docker-compose services
RUN curl -o /usr/local/bin/wait-for-it https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh
RUN chmod +x /usr/local/bin/wait-for-it

# install the app
WORKDIR /app
ADD . /app

RUN make
CMD make test
