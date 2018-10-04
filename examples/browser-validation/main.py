import logging
import json

import click
import s3fs
import pyarrow.parquet as pq
import pandas as pd
import numpy as np

from prio import prio

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def extract(submission_date, bucket, prefix):
    fs = s3fs.S3FileSystem()
    globs = f"submission_date={submission_date}/*.parquet"
    files = fs.glob(f"s3://{bucket}/{prefix}/{globs}")

    logger.info(f"Loading data for {submission_date} from s3://{bucket}/{prefix}")
    df = (
        pq
        .ParquetDataset(files, filesystem=fs)
        .read()
        .to_pandas()
    )
    return df


def get_values_sorted(d):
  tuples = [(int(k), int(v)) for k, v in d.items()]
  return [x[1] for x in sorted(tuples)]


def extract_ping(f):
    ping = json.load(f)
    prio_data = ping['payload']['prio']

    # Spark stores arrays using numpy
    data = {
        'prio_data_a': np.array(get_values_sorted(prio_data['a'])),
        'prio_data_b': np.array(get_values_sorted(prio_data['b'])),
    }
    return pd.DataFrame([data])


def prio_pipeline(df, config, server_a, server_b):
    error_count = 0
    for _, row in df.iterrows():
        vA = server_a.create_verifier(bytes(row.prio_data_a.astype('uint8')))
        vB = server_b.create_verifier(bytes(row.prio_data_b.astype('uint8')))

        p1A = vA.create_verify1()
        p1B = vB.create_verify1()
        p2A = vA.create_verify2(p1A, p1B)
        p2B = vB.create_verify2(p1A, p1B)

        if not (vA.is_valid(p2A, p2B) and vB.is_valid(p2A, p2B)):
            error_count += 1
            continue

        server_a.aggregate(vA)
        server_b.aggregate(vB)

    tA = server_a.total_shares()
    tB = server_b.total_shares()
    output = prio.total_share_final(config, tA, tB)
    return output


@click.command()
@click.option("--date", required=True)
@click.option("--pubkey-A", required=True)
@click.option("--pvtkey-A", required=True)
@click.option("--pubkey-B", required=True)
@click.option("--pvtkey-B", required=True)
@click.option("--ping", type=click.File('r'))
@click.option("--bucket", default="net-mozaws-prod-us-west-2-pipeline-analysis")
@click.option("--prefix", default="amiyaguchi/prio/v1")
def main(date, pubkey_a, pvtkey_a, pubkey_b, pvtkey_b, ping, bucket, prefix):
    pubkey_a = bytes(pubkey_a, "utf-8")
    pvtkey_a = bytes(pvtkey_a, "utf-8")
    pubkey_b = bytes(pubkey_b, "utf-8")
    pvtkey_b = bytes(pvtkey_b, "utf-8")

    pkA = prio.PublicKey().import_hex(pubkey_a)
    skA = prio.PrivateKey().import_hex(pvtkey_a, pubkey_a)
    pkB = prio.PublicKey().import_hex(pubkey_b)
    skB = prio.PrivateKey().import_hex(pvtkey_b, pubkey_b)

    # The pilot includes 3 boolean histograms
    config = prio.Config(3, pkA, pkB, bytes(date, "utf-8"))
    server_secret = prio.PRGSeed()
    server_a = prio.Server(config, prio.PRIO_SERVER_A, skA, server_secret)
    server_b = prio.Server(config, prio.PRIO_SERVER_B, skB, server_secret)

    if ping:
        df = extract_ping(ping)
    else:
        df = extract(date, bucket, prefix)

    output = prio_pipeline(df, config, server_a, server_b)
    logger.info(output)


if __name__ == '__main__':
    main()