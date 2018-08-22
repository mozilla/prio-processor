# python-prio

A python wrapper for libprio.

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