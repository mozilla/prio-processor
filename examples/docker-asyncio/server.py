import asyncio
import aio_pika
import logging
import os
import sys
import pickle
from functools import partial

import click
from prio import prio

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

DEFAULT_SHARED_SEED = b"vY\xc1\t\x93\xfb\xc6\x97*\x07j\xd63i+\x86"


def get_other_server(server_id):
    mapping = {
        prio.PRIO_SERVER_A: prio.PRIO_SERVER_B,
        prio.PRIO_SERVER_B: prio.PRIO_SERVER_A,
    }
    return mapping[server_id]


async def run_server(
    pubkey, pvtkey, pubkey_other, server_id, n_fields, batch_id, shared_seed
):
    connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq:5672/")
    channel = await connection.channel()
    queue = await channel.declare_queue(f"prio.{server_id}")

    pk = prio.PublicKey().import_hex(pubkey)
    sk = prio.PrivateKey().import_hex(pvtkey, pubkey)
    pk_other = prio.PublicKey().import_hex(pubkey_other)

    seed = prio.PRGSeed()
    seed.instance = shared_seed

    config = prio.Config(n_fields, pk, pk_other, batch_id)
    server = prio.Server(config, server_id, sk, seed)

    cache = {}

    async for message in queue:
        with message.process():
            pid = message.message_id
            v, p1, p2 = cache.get(pid, (None, None, None))

            def log(line):
                logger.info("Message {}: {}".format(pid, line))

            ptype = message.type
            routing_key = "prio.{}".format(get_other_server(server_id))

            if (ptype == "verify1" and not p1) or (ptype == "verify2" and not p2):
                log("Re-queuing message!")
                await channel.default_exchange.publish(
                    aio_pika.Message(
                        body=message.body,
                        message_id=message.message_id,
                        type=message.type,
                    ),
                    routing_key="prio.{}".format(server_id),
                )
            elif ptype == "data":
                log("Generating verify packet 1")
                v = server.create_verifier(message.body)
                p1 = v.create_verify1()
                await channel.default_exchange.publish(
                    aio_pika.Message(
                        body=pickle.dumps(p1),
                        message_id=message.message_id,
                        type="verify1",
                    ),
                    routing_key=routing_key,
                )
            elif ptype == "verify1":
                log("Generating verify packet 2")
                p2 = v.create_verify2(p1, pickle.loads(message.body))
                await channel.default_exchange.publish(
                    aio_pika.Message(
                        body=pickle.dumps(p2),
                        message_id=message.message_id,
                        type="verify2",
                    ),
                    routing_key=routing_key,
                )
            elif ptype == "verify2":
                if v.is_valid(p2, pickle.loads(message.body)):
                    log("Aggregate data")
                    server.aggregate(v)
                else:
                    log("Invalid data")
                del cache[pid]
            else:
                log("Bad message type {}".format(ptype))

            cache[pid] = (v, p1, p2)


@click.command()
@click.option("--pubkey", type=str)
@click.option("--pvtkey", type=str)
@click.option("--pubkey-other", type=str)
@click.option("--server-id", type=click.Choice(["a", "b"]), required=True)
@click.option("--n-fields", type=int, required=True)
@click.option("--batch-id", type=str, default="test_batch")
def main(pubkey, pvtkey, pubkey_other, server_id, n_fields, batch_id):
    loop = asyncio.get_event_loop()
    server_id = prio.PRIO_SERVER_A if server_id == "a" else prio.PRIO_SERVER_B
    loop.run_until_complete(
        run_server(
            bytes(pubkey, "utf-8"),
            bytes(pvtkey, "utf-8"),
            bytes(pubkey_other, "utf-8"),
            server_id,
            n_fields,
            bytes(batch_id, "utf-8"),
            DEFAULT_SHARED_SEED,
        )
    )
    loop.run_forever()


if __name__ == "__main__":
    main()
