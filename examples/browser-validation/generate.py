import json
from itertools import product

import click
from prio import prio


# cardinality of the input vector
N_DATA = 3


def construct(build_id, user_default, newtab, pdf, data_a, data_b):
    ping = {
        "environment": {"build": {"buildId": build_id}},
        "payload": {
            "histograms": {
                "BROWSER_IS_USER_DEFAULT": {"sum": user_default},
                "NEWTAB_PAGE_ENABLED": {"sum": newtab},
                "PDF_VIEWER_USED": {"sum": pdf},
            },
            "prio": {
                "a": {k: int(v) for k, v in enumerate(data_a)},
                "b": {k: int(v) for k, v in enumerate(data_b)},
            },
        },
    }
    return ping


def generate(build_id, client):
    data = []
    for vector in product([0, 1], [0, 1], [0, 1]):
        args = list(vector) + client.encode(bytes(vector))
        ping = construct(build_id, *args)
        data.append(ping)
    return data


def write(fp, data):
    fp.write("\n".join(map(json.dumps, data)))


@click.command()
@click.option("--path", type=click.Path(exists=False), required=True)
@click.option("--batch-id", type=str, default="test-batch")
def main(path, batch_id):
    # create the encryption keys
    skA, pkA = prio.create_keypair()
    skB, pkB = prio.create_keypair()

    # create the client
    cfg = prio.Config(N_DATA, pkA, pkB, bytes(batch_id, "utf-8"))
    client = prio.Client(cfg)

    # generate test data
    data = generate(batch_id, client)
    with open(path, "w") as f:
        write(f, data)

    # print a command to use
    def clean(s):
        return s[:-1].decode("utf-8")

    args = {
        "--pings": path,
        "--pubkey-A": clean(pkA.export_hex()),
        "--pvtkey-A": clean(skA.export_hex()),
        "--pubkey-B": clean(pkB.export_hex()),
        "--pvtkey-B": clean(skB.export_hex()),
    }
    argstr = " \\".join([f"\n\t{k} {v}" for k, v in args.items()])
    print(f"python main.py \\{argstr}")


if __name__ == "__main__":
    main()
