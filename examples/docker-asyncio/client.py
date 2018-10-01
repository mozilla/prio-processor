import asyncio
import aioamqp
import logging

import rpc

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


async def main():
    queue_name = "test"

    transport, protocol = await aioamqp.connect("rabbitmq", 5672, "guest", "guest")

    await asyncio.sleep(5)
    logging.info("Collecting public keys")
    key = await rpc.Client(protocol).call(0)
    logging.info(key)

    key1 = await rpc.Client(protocol).call(1)
    logging.info(key1)

    await protocol.close()
    transport.close()
    logger.info("Client done!")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()