import asyncio
import aioamqp
import logging

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


async def main():
    queue_name = "test"

    transport, protocol = await aioamqp.connect("rabbitmq", 5672, "guest", "guest")
    channel = await protocol.channel()
    await channel.queue_declare(queue_name=queue_name)
    await channel.basic_publish(
        payload="Hello World",
        exchange_name="",
        routing_key=queue_name
    )
    await protocol.close()
    transport.close()
    logger.info("Client done!")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()