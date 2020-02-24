import timeit

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from prio import prio
from tqdm import tqdm


def bench_encrypted_sizes(path):
    _, pubkey = prio.create_keypair()

    def size(n):
        cfg = prio.Config(n, pubkey, pubkey, b"test")
        a, b = prio.Client(cfg).encode(bytes([1] * k))
        return [k, len(a), len(b)]

    sizes = []
    for k in tqdm(range(0, 10000, 100)):
        try:
            sizes.append(size(k))
        except:
            print(f"Prio excepted at {k} items")
            break

    fig, ax = plt.subplots()
    ax.set_xscale("log", basex=2)
    ax.set_yscale("log", basey=2)
    ax.xaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.yaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
    plt.title("Prio measurement size vs payload size")
    plt.xlabel("measurement size (bits)")
    plt.ylabel("payload size (bytes)")
    plt.plot(*np.array(sizes).T[:2])
    plt.savefig(path)


def bench_client_encoding(path):
    runs = 10 ** 2
    timings = []
    for k in tqdm([8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]):
        _, pubkey = prio.create_keypair()
        cfg = prio.Config(k, pubkey, pubkey, b"test_batch")
        client = prio.Client(cfg)
        data = bytes([1] * k)
        timing = timeit.timeit("client.encode(data)", number=runs, globals=locals())
        timings.append([k, timing])

    data = np.array(timings)
    y = data[:, 1] / runs
    x = data[:, 0]

    fig, ax = plt.subplots()
    plt.title(f"measurement size vs encoding time (n={runs})")
    plt.xlabel("measurement size (bits)")
    plt.ylabel("encoding time (seconds)")
    ax.set_xscale("log", basex=2)
    ax.set_yscale("log", basey=2)
    ax.xaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.yaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
    plt.plot(x, y)
    plt.savefig(path)


def main():
    print("running benchmark for encrypted sizes")
    bench_encrypted_sizes("encrypted_sizes.png")
    print("running benchmark for client encoding time")
    bench_client_encoding("client_encoding_time.png")


if __name__ == "__main__":
    main()
