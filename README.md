# python-libprio

[![CircleCI](https://circleci.com/gh/mozilla/python-libprio.svg?style=svg)](https://circleci.com/gh/mozilla/python-libprio)

Prio is a system for aggregating data in a privacy-preserving way. This
repository includes a Python wrapper around [libprio](https://github.com/mozilla/libprio) 
and a command-line tool for batch processing in Prio's multi-server architecture.

For more information about Prio, see [this blog
post](https://hacks.mozilla.org/2018/10/testing-privacy-preserving-telemetry-with-prio/).

## Build and Development

The `libprio` submodule must be initialized before building. Run the following
command to initialize the modules.

```bash
git submodule update --init
```

### Local

Refer to the Dockerfile and the `libprio` submodule for dependencies. If you are
running on macOS, the packages can be installed via homebrew.

```bash
brew install nss nspr scons msgpack swig
```

First, the static libraries for Prio and big numbers are generated in the git
submodule. Then, SWIG generates C files from the SWIG interface file. This
contains the code for sharing data between the static library and Python
objects. Finally, the library is made available to the Python package in an
extension module.

```bash
make
make test
```

### Docker (recommended)

This project contains a pre-configured build and test environment through
docker.

```bash
make build

# or using docker directly by building the development stage
docker build --target development -t prio:dev .
```

`make build` will generate two containers in a multi-stage build. The `prio:dev`
image is suitable for development. The `prio:latest` image is the production
image that is suitable for server deployments.

You can mount your working directory and shell into the container for
development work.

```bash
docker run -v `pwd`:/app -it prio:dev bash
make
make test
```

If you need access to gdb or valgrind, the following command is useful:

```bash
docker run \
    --cap-add=SYS_PTRACE \
    --security-opt seccomp=unconfined \
    -v `pwd`:/app \
    -it prio:dev bash
```

### Notes

`libprio` is compiled with position-independent code (`fPIC`).
This is required for the python foreign-function interface.

## Running examples

There are various examples included in the repository that demonstrate small
applications that can be built using this set of tools.

* `swig-wrapper` - A simple application demonstrating the full Prio pipeline.
* `python-wrapper` - A usage of the object-oriented Python wrapper.
* `benchmarks` - Various benchmarks in a Jupyter notebook.
* `browser-validation` - The validation code used to verify existing Firefox
  measurements for this [blog
  post](https://hacks.mozilla.org/2018/10/testing-privacy-preserving-telemetry-with-prio/).
* `asyncio` - An asynchronous pipeline.
* `docker-asyncio` - An asynchronous pipeline using a publish-subscribe
  architecture.
