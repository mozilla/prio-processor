import asyncio
import aioamqp
import logging
import os
import sys
import pickle

import click
from prio import prio
import rpc

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

DEFAULT_SHARED_SEED=b'vY\xc1\t\x93\xfb\xc6\x97*\x07j\xd63i+\x86'


def get_other_server(server_id):
    mapping = {
        prio.PRIO_SERVER_A: prio.PRIO_SERVER_B,
        prio.PRIO_SERVER_B: prio.PRIO_SERVER_A
    }
    return mapping[server_id]


class PrioHandler:
    def __init__(self, protocol, server):
        # A cache when waiting for the other server's packets. In the case where the
        # message handler is threaded, the built-in python types are inherently thread-safe.
        # However, asyncio runs on a single thread by default.
        self.cache = {}

        # prio data structures
        self.server = server

        # amqp setup
        self.protocol = protocol
        self.channel = None

    async def connect(self):
        self.channel = await self.protocol.channel()
        queue_name = "prio.{}".format(self.server.server_id)
        await self.channel.queue_declare(queue_name=queue_name)
        await self.channel.basic_consume(self.on_message, queue_name=queue_name)

    async def on_message(self, channel, body, envelope, properties):
        pid = properties.message_id
        v, p1, p2 = self.cache.get(pid, (None, None, None))

        def log(line):
            logger.info("Message {}: {}".format(pid, line))

        log(len(body))
        if self.server.server_id == 1:
            log(body)

        ptype = properties.type
        routing_key = "prio.{}".format(get_other_server(self.server.server_id))

        if (ptype == 'verify1' and not p1) or (ptype == 'verify2' and not p2):
            log("Re-queuing message!")
            await self.channel.basic_publish(
                payload=body,
                exchange=envelope.exchange,
                routing_key=envelope.routing_key,
                properties=properties
            )
        elif ptype == 'data':
            log("Generating verify packet 1")
            v = self.server.create_verifier(body)
            p1 = v.create_verify1()
            await self.channel.basic_publish(
                payload=pickle.dumps(p1),
                exchange=envelope.exchange,
                routing_key=routing_key,
                properties={
                    'message_id': properties.message_id,
                    'type': 'verify1'
                }
            )
        elif ptype == 'verify1':
            log("Generating verify packet 2")
            p2 = v.create_verify2(p1, pickle.loads(body))
            await self.channel.basic_publish(
                payload=pickle.dumps(p2),
                exchange=envelope.exchange,
                routing_key=routing_key,
                properties={
                    'message_id': properties.message_id,
                    'type': 'verify2'
                }
            )
        elif ptype == 'verify2':
            if v.is_valid(p2, pickle.loads(body)):
                log("Aggregate data")
                self.server.aggregate(v)
            else:
                log("Invalid data")
            del self.cache[pid]
        else:
            log("Bad message type {}".format(ptype))

        await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)
        self.cache[pid] = (v, p1, p2)


async def run_server(server_id, n_fields, batch_id, shared_seed):
    other_server_id = get_other_server(server_id)
    pvtkey, pubkey = prio.create_keypair()

    logger.info("Starting server {}".format(server_id))
    transport, protocol = await aioamqp.connect("rabbitmq", 5672, "guest", "guest")

    await rpc.Server(protocol, lambda: pubkey.export_hex()[:-1], server_id).connect()
    # wait for the other server to come online
    await asyncio.sleep(3)

    # get the other pubkey to start the process
    data = await rpc.Client(protocol).call(other_server_id)
    logger.info("Fetched key for server {}: {}".format(other_server_id, data))
    other_pubkey = prio.PublicKey().import_hex(data)

    seed = prio.PRGSeed()
    seed.instance = shared_seed

    # does the order of private keys really matter?
    if server_id == prio.PRIO_SERVER_A:
        server_a_pubkey = pubkey
        server_b_pubkey = other_pubkey
    else:
        server_a_pubkey = other_pubkey
        server_b_pubkey = pubkey

    config = prio.Config(n_fields, server_a_pubkey, server_b_pubkey, batch_id)
    server = prio.Server(config, server_id, pvtkey, seed)

    await PrioHandler(protocol, server).connect()


@click.command()
@click.option('--server-id', type=click.Choice(['a', 'b']), required=True)
@click.option('--n-fields', type=int, required=True)
@click.option('--batch-id', type=str, default='test_batch')
def main(server_id, n_fields, batch_id):
    loop = asyncio.get_event_loop()
    server_id = prio.PRIO_SERVER_A if server_id == 'a' else prio.PRIO_SERVER_B
    loop.run_until_complete(run_server(server_id, n_fields, bytes(batch_id, "utf-8"), DEFAULT_SHARED_SEED))
    loop.run_forever()

if __name__ == "__main__":
    main()
