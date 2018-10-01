import asyncio
import aioamqp
import logging
import os

from prio import prio
import rpc

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

server_id = int(os.environ['SERVER_ID'])
assert server_id in (prio.PRIO_SERVER_A, prio.PRIO_SERVER_B)
other_server_id = 0 if server_id == 1 else 1
private_key, public_key = prio.create_keypair()

async def main():
    queue_name = "test"
    logger.info("Starting server")

    transport, protocol = await aioamqp.connect("rabbitmq", 5672, "guest", "guest")
    await rpc.Server(protocol, lambda: public_key.export_hex(), server_id).connect()
    await asyncio.sleep(1)
    other_key = await rpc.Client(protocol).call(other_server_id)
    logger.info(other_key)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()