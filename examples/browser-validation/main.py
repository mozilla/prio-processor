import code
import logging
import json
import os
from functools import partial

import click
import s3fs
import pyarrow.parquet as pq
import pandas as pd
import numpy as np

from prio import prio

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def extract(date, bucket, prefix, cache=False):
    cache_file = f".cache/{date}.parquet"
    if cache and os.path.exists(cache_file):
        logger.info(f"Using cached dataframe at {cache_file}")
        df = pd.read_parquet(cache_file)
        return df

    logger.info(f"Loading data for submission date {date} from s3://{bucket}/{prefix}")
    fs = s3fs.S3FileSystem()
    files = fs.glob(f"s3://{bucket}/{prefix}/submission_date={date}/*.parquet")
    df = pq.ParquetDataset(files, filesystem=fs).read().to_pandas()

    # NOTE: 20181005220146 is the first valid build_id
    # see: https://hg.mozilla.org/mozilla-central/rev/3e1d1b6a529e
    min_build_id = "20181005220146"
    filtered = df.loc[df["build_id"] >= min_build_id]

    if cache:
        logging.info(f"Caching dataframe at {cache_file}")
        if not os.path.exists(".cache"):
            os.mkdir(".cache")
        filtered.to_parquet(cache_file)

    return filtered


def get_values_sorted(d):
    tuples = [(int(k), int(v)) for k, v in d.items()]
    return [x[1] for x in sorted(tuples)]


def extract_ping(f):
    data = []
    for line in f.readlines():
        ping = json.loads(line)
        payload = ping["payload"]
        row = {}

        row["build_id"] = ping["environment"]["build"]["buildId"]

        names = ["browser_is_user_default", "newtab_page_enabled", "pdf_viewer_used"]
        for name in names:
            hist = payload["histograms"].get(name.upper())
            bucket_sum = (hist or {}).get("sum", 0)
            row[name] = int(bool(bucket_sum))

        prio_data = payload["prio"]
        row["prio_data_a"] = np.array(get_values_sorted(prio_data["a"]))
        row["prio_data_b"] = np.array(get_values_sorted(prio_data["b"]))

        data.append(row)

    return pd.DataFrame(data)


def prio_aggregate(init_func, group):
    batch_id = group.name if isinstance(group.name, str) else group.name[0]
    config, server_a, server_b = init_func(batch_id)

    prio_null_data = 0
    prio_invalid = 0

    def compact(x):
        return bytes(x.astype("uint8"))

    data = zip(group.prio_data_a.apply(compact), group.prio_data_b.apply(compact))
    for data_a, data_b in data:
        if not data_a or not data_b:
            prio_null_data += 1
            continue

        vA = server_a.create_verifier(data_a)
        vB = server_b.create_verifier(data_b)
        p1A = vA.create_verify1()
        p1B = vB.create_verify1()
        p2A = vA.create_verify2(p1A, p1B)
        p2B = vB.create_verify2(p1A, p1B)

        if not (vA.is_valid(p2A, p2B) and vB.is_valid(p2A, p2B)):
            prio_invalid += 1
            continue

        server_a.aggregate(vA)
        server_b.aggregate(vB)

    tA = server_a.total_shares()
    tB = server_b.total_shares()
    total = np.array(prio.total_share_final(config, tA, tB))

    # control values
    default = group.browser_is_user_default.sum()
    pdf = group.pdf_viewer_used.sum()
    newtab = group.newtab_page_enabled.sum()
    control = np.array([default, newtab, pdf])

    d = {
        "prio_control": control,
        "prio_observed": total,
        "prio_diff": (control - total).astype("int"),
        "prio_null_data": prio_null_data,
        "prio_invalid": prio_invalid,
        "count": len(group.index),
    }
    return pd.Series(d, index=d.keys())


@click.command()
@click.option("--date")
@click.option("--pubkey-A", required=True)
@click.option("--pvtkey-A", required=True)
@click.option("--pubkey-B", required=True)
@click.option("--pvtkey-B", required=True)
@click.option("--groupby", type=str, help="comma-delimited groupby keys")
@click.option("--interactive/--no-interactive", default=False)
@click.option("--cache/--no-cache", default=False)
@click.option("--pings", type=click.File("r"))
@click.option("--bucket", default="net-mozaws-prod-us-west-2-pipeline-analysis")
@click.option("--prefix", default="amiyaguchi/prio/v1")
def main(
    date,
    pubkey_a,
    pvtkey_a,
    pubkey_b,
    pvtkey_b,
    groupby,
    interactive,
    cache,
    pings,
    bucket,
    prefix,
):
    if not (date or pings):
        raise click.BadOptionUsage(
            "date", "Specify either a submission-date or a local ping-set!"
        )

    pubkey_a = bytes(pubkey_a, "utf-8")
    pvtkey_a = bytes(pvtkey_a, "utf-8")
    pubkey_b = bytes(pubkey_b, "utf-8")
    pvtkey_b = bytes(pvtkey_b, "utf-8")

    pkA = prio.PublicKey().import_hex(pubkey_a)
    skA = prio.PrivateKey().import_hex(pvtkey_a, pubkey_a)
    pkB = prio.PublicKey().import_hex(pubkey_b)
    skB = prio.PrivateKey().import_hex(pvtkey_b, pubkey_b)

    server_secret = prio.PRGSeed()

    # use lexical closure to create an initialization callback
    def init_servers(build_id):
        # The pilot includes 3 boolean histograms
        config = prio.Config(3, pkA, pkB, bytes(build_id, "utf-8"))
        server_a = prio.Server(config, prio.PRIO_SERVER_A, skA, server_secret)
        server_b = prio.Server(config, prio.PRIO_SERVER_B, skB, server_secret)
        return config, server_a, server_b

    input_df = extract_ping(pings) if pings else extract(date, bucket, prefix, cache)

    keys = [key.strip() for key in groupby.split()] if groupby else []
    df = (
        input_df.groupby(["build_id"] + keys)
        .apply(partial(prio_aggregate, init_servers))
        .sort_values("build_id", ascending=False)
    )
    print(df.to_string())
    if interactive:
        code.interact(local=locals())


if __name__ == "__main__":
    main(auto_envvar_prefix="PRIO")
