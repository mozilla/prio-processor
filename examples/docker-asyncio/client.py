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

    await asyncio.sleep(3)
    pkey_a = b'F63F2FB9B823B7B672684A526AC467DCFC110D4BB242F6DF0D3EA9F09CE14B51'
    pkey_b = b'15DC84D87C73A36120E0389D4ABCD433EDC5147DC71A4093E2A5952968D51F07'
    pkA = prio.PublicKey().import_hex(pkey_a)
    pkB = prio.PublicKey().import_hex(pkey_b)

    config = prio.Config(n_fields, pkA, pkB, batch_id)
    client = prio.Client(config)

    data_items = bytes([(i % 3 == 1) or (i % 5 == 1) for i in range(n_fields)])

    seed = prio.PRGSeed()
    seed.instance = b'vY\xc1\t\x93\xfb\xc6\x97*\x07j\xd63i+\x86'
    skey_a = b'7A0AA608C08CB74A86409F5026865435B2F17F40B20636CEFD2656585097FBE0'
    skey_b = b'50C7329DE18DE3087A0DE963D5585A4DB7A156C7A29FA854760373B053D86919'
    skA = prio.PrivateKey().import_hex(skey_a, pkey_a)
    skB = prio.PrivateKey().import_hex(skey_b, pkey_b)
    server_a = prio.Server(config, prio.PRIO_SERVER_A, skA, seed)
    server_b = prio.Server(config, prio.PRIO_SERVER_B, skB, seed)

    channel = await protocol.channel()
    # send messages along the main prio queues
    await channel.queue_declare(queue_name="prio.0")
    await channel.queue_declare(queue_name="prio.1")
    for i in range(n_clients):
        logger.info("Client {}: Generated shares".format(i))
        for_server_a, for_server_b = client.encode(data_items)
        logger.info("A: {} B: {}".format(len(for_server_a), len(for_server_b)))
        server_a.create_verifier(for_server_a).create_verify1()
        server_b.create_verifier(for_server_b).create_verify1()
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
