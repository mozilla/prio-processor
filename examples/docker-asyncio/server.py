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
            v = self.server.create_verifier(bytes(body))
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
    skey_a = b'7A0AA608C08CB74A86409F5026865435B2F17F40B20636CEFD2656585097FBE0'
    pkey_a = b'F63F2FB9B823B7B672684A526AC467DCFC110D4BB242F6DF0D3EA9F09CE14B51'
    skey_b = b'50C7329DE18DE3087A0DE963D5585A4DB7A156C7A29FA854760373B053D86919'
    pkey_b = b'15DC84D87C73A36120E0389D4ABCD433EDC5147DC71A4093E2A5952968D51F07'
    pkA = prio.PublicKey().import_hex(pkey_a)
    pkB = prio.PublicKey().import_hex(pkey_b)
    skA = prio.PrivateKey().import_hex(skey_a, pkey_a)
    skB = prio.PrivateKey().import_hex(skey_b, pkey_b)

    seed = prio.PRGSeed()
    seed.instance = shared_seed

    config = prio.Config(n_fields, pkA, pkB, batch_id)
    pvtkey = skA if server_id == prio.PRIO_SERVER_A else skB
    server = prio.Server(config, server_id, pvtkey, seed)

    transport, protocol = await aioamqp.connect("rabbitmq", 5672, "guest", "guest")
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
