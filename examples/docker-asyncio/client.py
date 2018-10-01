import asyncio
import aioamqp
import logging
import click

from prio import prio
import rpc

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


async def run_client(n_clients, n_fields, batch_id):
    transport, protocol = await aioamqp.connect("rabbitmq", 5672, "guest", "guest")

    await asyncio.sleep(5)
    logging.info("Collecting public keys")
    server_a_data = await rpc.Client(protocol).call(prio.PRIO_SERVER_A)
    server_b_data = await rpc.Client(protocol).call(prio.PRIO_SERVER_B)
    logging.info(
        "Public keys:\n Server A: {}\nServer B: {}"
        .format(server_a_data, server_b_data))
    server_a_pubkey = prio.PublicKey()
    server_a_pubkey.import_hex(server_a_data[:-1])
    server_b_pubkey = prio.PublicKey()
    server_b_pubkey.import_hex(server_b_data[:-1])

    config = prio.Config(n_fields, server_a_pubkey, server_b_pubkey, batch_id)
    client = prio.Client(config)

    data_items = bytes([(i % 3 == 1) or (i % 5 == 1) for i in range(n_fields)])

    channel = await protocol.channel()
    # send messages along the main prio queues
    await channel.queue_declare(queue_name="prio.0")
    await channel.queue_declare(queue_name="prio.1")
    for i in range(n_clients):
        logger.info("Client {}: Generated shares".format(i))
        for_server_a, for_server_b = client.encode(data_items)
        logger.info("A: {} B: {}".format(len(for_server_a), len(for_server_b)))
        await channel.basic_publish(
            payload=for_server_a,
            exchange_name='',
            routing_key="prio.0",
            properties={
                'message_id': str(i),
                'type': 'data'
            }
        )
        await channel.basic_publish(
            payload=for_server_b,
            exchange_name='',
            routing_key="prio.1",
            properties={
                'message_id': str(i),
                'type': 'data'
            }
        )

    await protocol.close()
    transport.close()
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
