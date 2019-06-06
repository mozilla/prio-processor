# Multiprocessing

This example demonstrates multiprocessing support using the python bindings. The
application must be aware of the underlying NSS context and properly reference
count all pointers. Functions must be serializable, which means every process
should bring up it's own prio context.

The following context manager is useful for Prio functions:

```python
class PrioContext:
    def __enter__(self):
        libprio.Prio_init()

    def __exit__(self, *exc):
        libprio.Prio_clear()
```

When structured this way, libprio can be run in a process-safe way. However,
this is not thread-safe and will fail on trying to initialize the NSS context.

```bash
b'1EFB6C7C36AD6AADE469997E57A187229BF3409EEB17B9050D0298E8657D036E'
b'5E80B51148FD3FAC1C3522150736F41B6A7DBA5CFDECADAD4F9406B34E3ABA5A'
processing 20 elements
1 processes took 2.351 seconds at 0.118 per element
2 processes took 1.389 seconds at 0.069 per element
3 processes took 1.055 seconds at 0.053 per element
4 processes took 0.850 seconds at 0.043 per element
```

## Quickstart

```python
python main.py
```
