import asyncio
import aioamqp
import logging

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


async def on_message(channel, body, envelope, properties):
    logger.info(body)


async def main():
    queue_name = "test"
    logger.info("Starting server")

    transport, protocol = await aioamqp.connect("rabbitmq", 5672, "guest", "guest")
    channel = await protocol.channel()
    await channel.queue_declare(queue_name=queue_name)
    await channel.basic_consume(on_message, queue_name=queue_name, no_ack=True)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()