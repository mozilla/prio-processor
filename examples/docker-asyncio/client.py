import asyncio
import aio_pika
import logging
import click

from prio import prio

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


async def run_client(n_clients, n_fields, batch_id):
    await asyncio.sleep(3)
    pkey_a = b'F63F2FB9B823B7B672684A526AC467DCFC110D4BB242F6DF0D3EA9F09CE14B51'
    pkey_b = b'15DC84D87C73A36120E0389D4ABCD433EDC5147DC71A4093E2A5952968D51F07'
    pkA = prio.PublicKey().import_hex(pkey_a)
    pkB = prio.PublicKey().import_hex(pkey_b)

    config = prio.Config(n_fields, pkA, pkB, batch_id)
    client = prio.Client(config)

    data_items = bytes([(i % 3 == 1) or (i % 5 == 1) for i in range(n_fields)])

    connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq:5672/")
    channel = await connection.channel()
    await channel.declare_queue("prio.0")
    await channel.declare_queue("prio.1")

    for i in range(n_clients):

        logger.info("Client {}: Generated shares".format(i))
        for_server_a, for_server_b = client.encode(data_items)

        await channel.default_exchange.publish(
            aio_pika.Message(
                body=for_server_a,
                message_id=str(i),
                type='data'
            ),
            routing_key="prio.0"
        )
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=for_server_b,
                message_id=str(i),
                type='data'
            ),
            routing_key="prio.1"
        )
    await connection.close()
    logger.info("Client done!")


@click.command()
@click.option('--n-clients', type=int, default=10)
@click.option('--n-fields', type=int, required=True)
@click.option('--batch-id', type=str, default='test_batch')
def main(n_clients, n_fields, batch_id):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_client(n_clients, n_fields, bytes(batch_id, "utf-8")))
    loop.close()

if __name__ == "__main__":
    main()
