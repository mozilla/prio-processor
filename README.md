# python-libprio

A python wrapper around libprio.

This library provides low-level bindings to the reference C implementation of the [Prio system](https://github.com/mozilla/libprio) and a high-level Python interface.


## Build

```
$ cd libprio
$ CFLAGS='-fPIC' scons
$ cd ..
$ make
```

### Notes
* The statically linked libraries must be compiled with `-fPIC` since Python build a shared library.
* The `libprio/mpi/SConscript` file must be modified directly to add the `fPIC` flag.


## Test

```bash
$ pipenv shell
$ make test
$ make coverage
```

To run the tests directly:
```bash
$ pipenv run python -m pytest
```

## Running examples

The `wrapper_example.py` includes an example of the full pipeline.

To drop into a REPL with state already set up:
```bash
$ pipenv run python -i wrapper_example.py
```
