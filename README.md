# python-libprio
[![CircleCI](https://circleci.com/gh/mozilla/python-libprio.svg?style=svg)](https://circleci.com/gh/mozilla/python-libprio)

A set of tools for aggregating data in a privacy preserving way. This repository
includes a Python wrapper around mozilla/libprio and is designed for
implementing server-side components.

The library provides low-level bindings to the reference C implementation of the
[Prio system](https://github.com/mozilla/libprio), a Python wrapper, and a
command-line interface.

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

First, the static libraries for prio and big numbers are generated in the git
submodule. Then, SWIG generates C files from the SWIG interface file. This
contains the code for sharing data between the static library and Python
objects. Finally, the library is made available to the Python package as an
extension module.

```bash
make
make test
```

### Docker (recommended)

This project contains a pre-configured build and test environment through
docker.

```bash
docker build -t prio .
docker run -it prio
```
This will build the package and run the tests. You can mount your working
directory and shell into the container for development work.

```bash
docker run -v `pwd`:/app -it prio bash
make
make test
```

### Notes

`libprio` is compiled with position-independent code (`fPIC`).
This is required for the python foreign-function interface.

## Running examples

There are various examples included in the repository that demonstrate small
applications that can be built from the library.

* `swig-wrapper` - A simple application demonstrating the full prio pipeline.
* `python-wrapper` - A usage of the object-oriented based Python wrapper.
* `benchmarks` - Various benchmarks in a jupyter notebook.
* `browser-validation` - The validation code used to verify existing Firefox measurements for this [blog post](https://hacks.mozilla.org/2018/10/testing-privacy-preserving-telemetry-with-prio/).
* `asyncio` - An asynchronous pipeline.
* `docker-asyncio` - An asynchronous pipeline using a publish-subscribe architecture.
