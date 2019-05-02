# python-libprio
[![CircleCI](https://circleci.com/gh/acmiyaguchi/python-libprio.svg?style=svg)](https://circleci.com/gh/acmiyaguchi/python-libprio)

A python wrapper around libprio.

This library provides low-level bindings to the reference C implementation of
the [Prio system](https://github.com/mozilla/libprio) and a high-level Python
interface.


## Build

The `libprio` submodule must be initialized before building. Run the following
command to initialize the modules.

```bash
git submodule update --init
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
```

### Local

Refer to the Dockerfile and the `libprio` submodule for dependencies. If you are
running on macOS, the packages can be installed via homebrew.

```bash
brew install nss nspr scons msgpack swig
```

```bash
make
make test
```

### Notes

`libprio` is compiled with position-independent code (`fPIC`).
This is required for the python foreign-function interface.


## Test

```bash
docker build -t prio . && docker run -it prio
```
You can avoid rebuilds by mounting your working directory and testing directly within the container.

If you want to avoid the Makefile for tests, the project uses pytest.
```bash
pipenv sync --dev
pipenv run pytest
```

## Running examples

The `wrapper_example.py` includes an example of the full pipeline.
