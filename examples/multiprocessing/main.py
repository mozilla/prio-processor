from prio import libprio
from base64 import b64encode
from random import getrandbits
from multiprocessing import Pool


class PrioContext:
    def __enter__(self):
        libprio.Prio_init()

    def __exit__(self, *exc):
        libprio.Prio_clear()


def encode(internal_hex, external_hex):
    n_data = 2000
    batch_id = b"test_batch"
    with PrioContext():
        # multiprocess environment runs in a forked process with a new process-id
        # initialize a new context for interacting with the swig wrapper
        pkA = libprio.PublicKey_import_hex(internal_hex)
        pkB = libprio.PublicKey_import_hex(external_hex)
        cfg = libprio.PrioConfig_new(n_data, pkA, pkB, batch_id)
        data_items = bytes([(i % 3 == 1) or (i % 5 == 1) for i in range(n_data)])
        for_server_a, for_server_b = libprio.PrioClient_encode(cfg, data_items)
    return b64encode(for_server_a), b64encode(for_server_b)


with PrioContext():
    _, pkA = libprio.Keypair_new()
    _, pkB = libprio.Keypair_new()
    # trailing null byte
    internal_hex = libprio.PublicKey_export_hex(pkA)[:-1]
    external_hex = libprio.PublicKey_export_hex(pkB)[:-1]

print(internal_hex)
print(external_hex)

if __name__ == "__main__":
    import time

    size = 20

    print(f"processing {size} elements")
    for i in range(1, 5):
        t0 = time.time()
        p = Pool(i)
        x = p.starmap(encode, [(internal_hex, external_hex)] * size)
        elapsed = time.time() - t0
        print(
            f"{i} processes took {elapsed:.3f} seconds at {elapsed/size:.3f} per element"
        )
