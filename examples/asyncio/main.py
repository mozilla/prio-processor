# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import logging
import random
import sys
from collections import namedtuple

from prio import prio

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

PACKET_DATA = 0
PACKET_VERIFY_1 = 1
PACKET_VERIFY_2 = 2

Packet = namedtuple("Packet", ["id", "type", "data"])

async def server_consume(server, read_queue, write_queue):
    # maintain state of the server's shares in the verifier, along with the
    # generated verification packets
    cache = {}

    while True:
        # add random jitter to simulate io
        await asyncio.sleep(random.random())

        packet = await read_queue.get()
        pid = packet.id
        v, p1, p2 = cache.get(pid, (None, None, None))

        def log(line):
             logger.info("Server {}, PID {}: {}".format(server.server_id, pid, line))

        
        # out of order packet execution is dealt with by pushing data back
        # into the queue

        if packet.type == PACKET_DATA:
            log("Generate verify packet 1")
            v = server.create_verifier(packet.data)
            p1 = v.create_verify1()
            await write_queue.put(Packet(id=pid, type=PACKET_VERIFY_1, data=p1))
        elif packet.type == PACKET_VERIFY_1:
            if not p1:
                await read_queue.put(packet)
                read_queue.task_done()
                continue
            log("Generate verify packet 2")
            p2 = v.create_verify2(p1, packet.data)
            await write_queue.put(Packet(id=pid, type=PACKET_VERIFY_2, data=p2))
        elif packet.type == PACKET_VERIFY_2:
            if not p2:
                await read_queue.put(packet)
                read_queue.task_done()
                continue
            if v.is_valid(p2, packet.data):
                log("Aggregate data")
                server.aggregate(v)
            else:
                log("Invalid data")
            del cache[pid]

        read_queue.task_done()
        cache[pid] = (v, p1, p2)


async def client_produce(client, data_items, queue_a, queue_b, n_clients):
    for i in range(n_clients):
        logger.info("Client {}: Generate shares".format(i))
        for_server_a, for_server_b = client.encode(data_items)
        await queue_a.put(Packet(id=i, type=PACKET_DATA, data=for_server_a))
        await queue_b.put(Packet(id=i, type=PACKET_DATA, data=for_server_b))


async def main():
    n_clients = 10
    n_data = 133
    server_secret = prio.PRGSeed()
    skA, pkA = prio.create_keypair()
    skB, pkB = prio.create_keypair()
    
    cfg = prio.Config(n_data, pkA, pkB, b"test_batch")
    sA = prio.Server(cfg, prio.PRIO_SERVER_A, skA, server_secret)
    sB = prio.Server(cfg, prio.PRIO_SERVER_B, skB, server_secret)

    data_items = bytearray([(i % 3 == 1) or (i % 5 == 1) for i in range(n_data)])

    logger.info("Starting asyncio prio pipeline.")
    client = prio.Client(cfg)
    queue_a = asyncio.Queue()
    queue_b = asyncio.Queue()

    await client_produce(client, data_items, queue_a, queue_b, n_clients)

    consumers = asyncio.ensure_future(
        asyncio.gather(
            server_consume(sA, queue_a, queue_b),
            server_consume(sB, queue_b, queue_a),
        )
    )

    await asyncio.gather(queue_a.join(), queue_b.join())

    t_a = sA.total_shares()
    t_b = sB.total_shares()

    output = prio.total_share_final(cfg, t_a, t_b)

    expected = [item*n_clients for item in list(data_items)]
    assert(list(output) == expected)

    consumers.cancel()
    logger.info("Done!")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
