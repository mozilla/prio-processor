import asyncio
import aioamqp
import uuid


# The most straightforward way to handle the handshake between all of the parties
# is to use some sort of RPC. Here's one that's based on the aioamqp example.
# Even better is to just hardcode the configuration parameters across the system at
# build time, since they're immutable once the keys are generated.
# TODO: Remove this code once private key methods are available
class Client:
    def __init__(self, protocol):
        self.protocol = protocol
        self.channel = None
        self.callback_queue = None
        self.response = None
        self.waiter = asyncio.Event()

    async def connect(self):
        self.channel = await self.protocol.channel()
        result = await self.channel.queue_declare(queue_name='', exclusive=True)
        self.callback_queue = result['queue']
        await self.channel.basic_consume(
            self.on_response,
            no_ack=True,
            queue_name=self.callback_queue
        )
    
    async def on_response(self, chennel, body, envelope, properties):
        if self.corr_id == properties.correlation_id:
            self.response = bytes(body)
        self.waiter.set()
    
    async def call(self):
        self.corr_id = str(uuid.uuid4())
        self.response = None
        await self.channel.basic_publish(
            exchange_name='',
            routing_key='rpc_queue',
            properties={
                'reply_to': self.callback_queue,
                'correlation_id', self.corr_id,
            }
        )
        await self.waiter.wait()
        return self.response


class Server:
    def __init__(self, protocol, handler):
        self.protocol = protocol
        self.channel = None
        self.handler = handler
    
    async def connect(self):
        self.channel = self.protocol.channel()
        await self.channel.queue_declare(queue_name='rpc_queue')
        await self.channel.basic_qos(prefetch_count=1, prefetch_size=0, connection_global=False)
        await self.channel.basic_consume(self.on_request, queue_name='rpc_queue')
    
    async def on_request(self, channel, body, envelope, properties):
        response = self.handler()
        await self.channel.basic_publish(
            payload=bytes(response),
            exchange_name='',
            routing_key=properties.reply_to,
            properties={
                'correlation_id': properties.correlation_id,
            }
        )
        await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)
