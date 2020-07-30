import asyncio
import aio_pika
import logging
import click

from prio_processor.prio import wrapper as prio
from prio import PrioContext

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


async def run_client(pubkey_a, pubkey_b, n_clients, n_fields, batch_id):
    connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq:5672/")
    channel = await connection.channel()
    await channel.declare_queue("prio.0")
    await channel.declare_queue("prio.1")

    # delay for server setup
    await asyncio.sleep(3)

    pkA = prio.PublicKey().import_hex(pubkey_a)
    pkB = prio.PublicKey().import_hex(pubkey_b)

    config = prio.Config(n_fields, pkA, pkB, batch_id)
    client = prio.Client(config)

    data_items = bytes([(i % 3 == 1) or (i % 5 == 1) for i in range(n_fields)])

    for i in range(n_clients):

        logger.info("Client {}: Generated shares".format(i))
        for_server_a, for_server_b = client.encode(data_items)

        await channel.default_exchange.publish(
            aio_pika.Message(body=for_server_a, message_id=str(i), type="data"),
            routing_key="prio.0",
        )
        await channel.default_exchange.publish(
            aio_pika.Message(body=for_server_b, message_id=str(i), type="data"),
            routing_key="prio.1",
        )
    await connection.close()
    logger.info("Client done!")


@click.command()
@click.option("--pubkey-A", type=str)
@click.option("--pubkey-B", type=str)
@click.option("--n-clients", type=int, default=10)
@click.option("--n-fields", type=int, required=True)
@click.option("--batch-id", type=str, default="test_batch")
@PrioContext()
def main(pubkey_a, pubkey_b, n_clients, n_fields, batch_id):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        run_client(
            bytes(pubkey_a, "utf-8"),
            bytes(pubkey_b, "utf-8"),
            n_clients,
            n_fields,
            bytes(batch_id, "utf-8"),
        )
    )
    loop.close()


if __name__ == "__main__":
    main()
