# python-prio

A python wrapper for libprio.

The goal is to provide a high level wrapper around the low-level API so it can be used in data processing tools like Pandas and Spark.

## Build

```
$ cd libprio
$ CFLAGS='-fPIC' scons
$ cd ..
$ make
```

## Notes

* The statically linked libraries must be compiled with `-fPIC` since Python build a shared library.
* The `libprio/mpi/SConscript` file must be modified directly to add the `fPIC` flag.
* The opaque pointers requires writing hints for SWIG. Typemaps can help translate functions with side-effects into (relatively) pure functions. See the `OPAQUE_POINTER` macro and SWIG documentation.
* Functions and data-structures outside of the scope of the main header are not available for use by default. Unwrapping the `SECStatus` enum in `nss/lib/util/seccomon.h` is not available by default.