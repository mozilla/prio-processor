# docker-asyncio

This example demonstrates an example service running the prio pipeline in docker.

The servers do not handle the public-key exchange, nor does it handle the timing of publishing aggregates. 
It will communicate over an amqp channel as an alternative to RPC.

## Running the example

```bash
make build
make run
make clean
```

Results in:

```bash
Starting docker-asyncio_rabbitmq_1 ... done
Starting docker-asyncio_server_b_1 ... done
Starting docker-asyncio_server_a_1 ... done
Starting docker-asyncio_client_1   ... done
Attaching to docker-asyncio_rabbitmq_1, docker-asyncio_server_a_1, docker-asyncio_server_b_1, docker-asyncio_client_1
server_a_1  | Installing dependencies from Pipfile.lock (d4c931)…
server_b_1  | Installing dependencies from Pipfile.lock (d4c931)…
client_1    | Installing dependencies from Pipfile.lock (d4c931)…
rabbitmq_1  | 2018-11-13 22:03:50.317 [info] <0.33.0> Application lager started on node rabbit@4b0a6750965d
server_a_1  | To activate this project's virtualenv, run pipenv shell.
server_a_1  | Alternatively, run a command inside the virtualenv with pipenv run.
server_a_1  | All dependencies are now up-to-date!
server_a_1  | wait-for-it: waiting 15 seconds for rabbitmq:5672
rabbitmq_1  | 2018-11-13 22:04:01.043 [info] <0.33.0> Application crypto started on node rabbit@4b0a6750965d
rabbitmq_1  | 2018-11-13 22:04:01.044 [info] <0.33.0> Application inets started on node rabbit@4b0a6750965d
rabbitmq_1  | 2018-11-13 22:04:01.044 [info] <0.33.0> Application os_mon started on node rabbit@4b0a6750965d
rabbitmq_1  | 2018-11-13 22:04:01.044 [info] <0.33.0> Application jsx started on node rabbit@4b0a6750965d
rabbitmq_1  | 2018-11-13 22:04:01.089 [info] <0.33.0> Application mnesia started on node rabbit@4b0a6750965d
rabbitmq_1  | 2018-11-13 22:04:01.089 [info] <0.33.0> Application recon started on node rabbit@4b0a6750965d
rabbitmq_1  | 2018-11-13 22:04:01.097 [info] <0.33.0> Application xmerl started on node rabbit@4b0a6750965d
rabbitmq_1  | 2018-11-13 22:04:01.097 [info] <0.33.0> Application asn1 started on node rabbit@4b0a6750965d
rabbitmq_1  | 2018-11-13 22:04:01.098 [info] <0.33.0> Application public_key started on node rabbit@4b0a6750965d
rabbitmq_1  | 2018-11-13 22:04:01.098 [info] <0.33.0> Application ssl started on node rabbit@4b0a6750965d
rabbitmq_1  | 2018-11-13 22:04:01.098 [info] <0.33.0> Application ranch started on node rabbit@4b0a6750965d
rabbitmq_1  | 2018-11-13 22:04:01.098 [info] <0.33.0> Application ranch_proxy_protocol started on node rabbit@4b0a6750965d
rabbitmq_1  | 2018-11-13 22:04:01.098 [info] <0.33.0> Application rabbit_common started on node rabbit@4b0a6750965d
rabbitmq_1  | 2018-11-13 22:04:01.099 [info] <0.220.0>
rabbitmq_1  |  Starting RabbitMQ 3.7.8 on Erlang 20.3.8.5
rabbitmq_1  |  Copyright (C) 2007-2018 Pivotal Software, Inc.
rabbitmq_1  |  Licensed under the MPL.  See http://www.rabbitmq.com/
rabbitmq_1  |
rabbitmq_1  |   ##  ##
rabbitmq_1  |   ##  ##      RabbitMQ 3.7.8. Copyright (C) 2007-2018 Pivotal Software, Inc.
rabbitmq_1  |   ##########  Licensed under the MPL.  See http://www.rabbitmq.com/
rabbitmq_1  |   ######  ##
rabbitmq_1  |   ##########  Logs: <stdout>
rabbitmq_1  |
rabbitmq_1  |               Starting broker...
rabbitmq_1  | 2018-11-13 22:04:01.100 [info] <0.220.0>
rabbitmq_1  |  node           : rabbit@4b0a6750965d
rabbitmq_1  |  home dir       : /var/lib/rabbitmq
rabbitmq_1  |  config file(s) : /etc/rabbitmq/rabbitmq.conf
rabbitmq_1  |  cookie hash    : f3YwGZE502cLdedXb/gAhg==
rabbitmq_1  |  log(s)         : <stdout>
rabbitmq_1  |  database dir   : /var/lib/rabbitmq/mnesia/rabbit@4b0a6750965d
rabbitmq_1  | 2018-11-13 22:04:01.171 [info] <0.258.0> Memory high watermark set to 6363 MiB (6672126771 bytes) of 15907 MiB (16680316928 bytes) total
rabbitmq_1  | 2018-11-13 22:04:01.182 [info] <0.260.0> Enabling free disk space monitoring
rabbitmq_1  | 2018-11-13 22:04:01.182 [info] <0.260.0> Disk free limit set to 50MB
rabbitmq_1  | 2018-11-13 22:04:01.190 [info] <0.263.0> Limiting to approx 924 file handles (829 sockets)
rabbitmq_1  | 2018-11-13 22:04:01.190 [info] <0.264.0> FHC read buffering:  OFF
rabbitmq_1  | 2018-11-13 22:04:01.190 [info] <0.264.0> FHC write buffering: ON
rabbitmq_1  | 2018-11-13 22:04:01.218 [info] <0.220.0> Waiting for Mnesia tables for 30000 ms, 9 retries left
rabbitmq_1  | 2018-11-13 22:04:01.307 [info] <0.220.0> Waiting for Mnesia tables for 30000 ms, 9 retries left
rabbitmq_1  | 2018-11-13 22:04:01.307 [info] <0.220.0> Peer discovery backend rabbit_peer_discovery_classic_config does not support registration, skipping registration.
rabbitmq_1  | 2018-11-13 22:04:01.309 [info] <0.220.0> Priority queues enabled, real BQ is rabbit_variable_queue
rabbitmq_1  | 2018-11-13 22:04:01.344 [info] <0.286.0> Starting rabbit_node_monitor
rabbitmq_1  | 2018-11-13 22:04:01.433 [info] <0.314.0> Making sure data directory '/var/lib/rabbitmq/mnesia/rabbit@4b0a6750965d/msg_stores/vhosts/628WB79CIFDYO9LJI6DKMI09L' for vhost '/' exists
rabbitmq_1  | 2018-11-13 22:04:01.494 [info] <0.314.0> Starting message stores for vhost '/'
rabbitmq_1  | 2018-11-13 22:04:01.495 [info] <0.318.0> Message store "628WB79CIFDYO9LJI6DKMI09L/msg_store_transient": using rabbit_msg_store_ets_index to provide index
rabbitmq_1  | 2018-11-13 22:04:01.538 [info] <0.314.0> Started message store of type transient for vhost '/'
rabbitmq_1  | 2018-11-13 22:04:01.538 [info] <0.321.0> Message store "628WB79CIFDYO9LJI6DKMI09L/msg_store_persistent": using rabbit_msg_store_ets_index to provide index
rabbitmq_1  | 2018-11-13 22:04:01.572 [info] <0.314.0> Started message store of type persistent for vhost '/'
rabbitmq_1  | 2018-11-13 22:04:01.591 [info] <0.356.0> started TCP Listener on [::]:5672
rabbitmq_1  | 2018-11-13 22:04:01.592 [info] <0.220.0> Setting up a table for connection tracking on this node: tracked_connection_on_node_rabbit@4b0a6750965d
rabbitmq_1  | 2018-11-13 22:04:01.594 [info] <0.220.0> Setting up a table for per-vhost connection counting on this node: tracked_connection_per_vhost_on_node_rabbit@4b0a6750965d
rabbitmq_1  | 2018-11-13 22:04:01.594 [info] <0.33.0> Application rabbit started on node rabbit@4b0a6750965d
rabbitmq_1  | 2018-11-13 22:04:01.917 [info] <0.5.0> Server startup complete; 0 plugins started.
rabbitmq_1  |  completed with 0 plugins.
rabbitmq_1  | 2018-11-13 22:04:02.040 [info] <0.362.0> accepting AMQP connection <0.362.0> (172.19.0.3:38540 -> 172.19.0.2:5672)
rabbitmq_1  | 2018-11-13 22:04:02.040 [warning] <0.362.0> closing AMQP connection <0.362.0> (172.19.0.3:38540 -> 172.19.0.2:5672):
rabbitmq_1  | client unexpectedly closed TCP connection
server_a_1  | wait-for-it: rabbitmq:5672 is available after 2 seconds
server_b_1  | To activate this project's virtualenv, run pipenv shell.
server_b_1  | Alternatively, run a command inside the virtualenv with pipenv run.
server_b_1  | All dependencies are now up-to-date!
server_b_1  | wait-for-it: waiting 15 seconds for rabbitmq:5672
server_b_1  | wait-for-it: rabbitmq:5672 is available after 0 seconds
rabbitmq_1  | 2018-11-13 22:04:02.250 [info] <0.367.0> accepting AMQP connection <0.367.0> (172.19.0.4:47160 -> 172.19.0.2:5672)
rabbitmq_1  | 2018-11-13 22:04:02.250 [warning] <0.367.0> closing AMQP connection <0.367.0> (172.19.0.4:47160 -> 172.19.0.2:5672):
rabbitmq_1  | client unexpectedly closed TCP connection
client_1    | To activate this project's virtualenv, run pipenv shell.
client_1    | Alternatively, run a command inside the virtualenv with pipenv run.
client_1    | All dependencies are now up-to-date!
client_1    | wait-for-it: waiting 15 seconds for rabbitmq:5672
rabbitmq_1  | 2018-11-13 22:04:02.637 [info] <0.371.0> accepting AMQP connection <0.371.0> (172.19.0.5:38078 -> 172.19.0.2:5672)
rabbitmq_1  | 2018-11-13 22:04:02.638 [warning] <0.371.0> closing AMQP connection <0.371.0> (172.19.0.5:38078 -> 172.19.0.2:5672):
rabbitmq_1  | client unexpectedly closed TCP connection
client_1    | wait-for-it: rabbitmq:5672 is available after 0 seconds
server_a_1  | INFO:aio_pika.pika.adapters.base_connection:Connecting to 172.19.0.2:5672
rabbitmq_1  | 2018-11-13 22:04:03.594 [info] <0.375.0> accepting AMQP connection <0.375.0> (172.19.0.3:38546 -> 172.19.0.2:5672)
rabbitmq_1  | 2018-11-13 22:04:03.598 [info] <0.375.0> connection <0.375.0> (172.19.0.3:38546 -> 172.19.0.2:5672): user 'guest' authenticated and granted access to vhost '/'
server_b_1  | INFO:aio_pika.pika.adapters.base_connection:Connecting to 172.19.0.2:5672
rabbitmq_1  | 2018-11-13 22:04:03.689 [info] <0.391.0> accepting AMQP connection <0.391.0> (172.19.0.4:47166 -> 172.19.0.2:5672)
rabbitmq_1  | 2018-11-13 22:04:03.706 [info] <0.391.0> connection <0.391.0> (172.19.0.4:47166 -> 172.19.0.2:5672): user 'guest' authenticated and granted access to vhost '/'
client_1    | INFO:aio_pika.pika.adapters.base_connection:Connecting to 172.19.0.2:5672
rabbitmq_1  | 2018-11-13 22:04:03.892 [info] <0.407.0> accepting AMQP connection <0.407.0> (172.19.0.5:38084 -> 172.19.0.2:5672)
rabbitmq_1  | 2018-11-13 22:04:03.894 [info] <0.407.0> connection <0.407.0> (172.19.0.5:38084 -> 172.19.0.2:5672): user 'guest' authenticated and granted access to vhost '/'
client_1    | INFO:root:Client 0: Generated shares
client_1    | INFO:root:Client 1: Generated shares
server_a_1  | INFO:root:Message 0: Generating verify packet 1
server_a_1  | INFO:root:Message 0: Generating verify packet 2
server_b_1  | INFO:root:Message 0: Generating verify packet 1
server_b_1  | INFO:root:Message 0: Generating verify packet 2
server_b_1  | INFO:root:Message 0: Aggregate data
server_b_1  | INFO:root:Message 1: Generating verify packet 1
client_1    | INFO:root:Client 2: Generated shares
server_a_1  | INFO:root:Message 1: Generating verify packet 1
server_b_1  | INFO:root:Message 1: Generating verify packet 2
server_a_1  | INFO:root:Message 0: Aggregate data
server_a_1  | INFO:root:Message 1: Generating verify packet 2
server_a_1  | INFO:root:Message 2: Generating verify packet 1
client_1    | INFO:root:Client 3: Generated shares
server_b_1  | INFO:root:Message 1: Aggregate data
server_b_1  | INFO:root:Message 2: Generating verify packet 1
server_a_1  | INFO:root:Message 1: Aggregate data
server_a_1  | INFO:root:Message 2: Generating verify packet 2
server_b_1  | INFO:root:Message 2: Generating verify packet 2
client_1    | INFO:root:Client 4: Generated shares
server_a_1  | INFO:root:Message 3: Generating verify packet 1
server_b_1  | INFO:root:Message 3: Generating verify packet 1
server_a_1  | INFO:root:Message 2: Aggregate data
server_b_1  | INFO:root:Message 2: Aggregate data
server_b_1  | INFO:root:Message 3: Generating verify packet 2
server_a_1  | INFO:root:Message 3: Generating verify packet 2
server_a_1  | INFO:root:Message 4: Generating verify packet 1
server_b_1  | INFO:root:Message 3: Aggregate data
server_b_1  | INFO:root:Message 4: Generating verify packet 1
client_1    | INFO:root:Client 5: Generated shares
server_a_1  | INFO:root:Message 3: Aggregate data
server_a_1  | INFO:root:Message 4: Generating verify packet 2
server_b_1  | INFO:root:Message 4: Generating verify packet 2
server_b_1  | INFO:root:Message 4: Aggregate data
server_a_1  | INFO:root:Message 4: Aggregate data
server_a_1  | INFO:root:Message 5: Generating verify packet 1
client_1    | INFO:root:Client 6: Generated shares
server_b_1  | INFO:root:Message 5: Generating verify packet 1
server_b_1  | INFO:root:Message 5: Generating verify packet 2
server_a_1  | INFO:root:Message 5: Generating verify packet 2
server_b_1  | INFO:root:Message 5: Aggregate data
client_1    | INFO:root:Client 7: Generated shares
server_a_1  | INFO:root:Message 5: Aggregate data
server_a_1  | INFO:root:Message 6: Generating verify packet 1
server_b_1  | INFO:root:Message 6: Generating verify packet 1
server_a_1  | INFO:root:Message 7: Generating verify packet 1
client_1    | INFO:root:Client 8: Generated shares
server_b_1  | INFO:root:Message 6: Generating verify packet 2
server_b_1  | INFO:root:Message 7: Generating verify packet 1
server_a_1  | INFO:root:Message 6: Generating verify packet 2
server_a_1  | INFO:root:Message 6: Aggregate data
server_a_1  | INFO:root:Message 8: Generating verify packet 1
client_1    | INFO:root:Client 9: Generated shares
server_b_1  | INFO:root:Message 7: Generating verify packet 2
server_b_1  | INFO:root:Message 6: Aggregate data
server_b_1  | INFO:root:Message 8: Generating verify packet 1
server_a_1  | INFO:root:Message 7: Generating verify packet 2
server_a_1  | INFO:root:Message 7: Aggregate data
server_a_1  | INFO:root:Message 9: Generating verify packet 1
server_b_1  | INFO:root:Message 8: Generating verify packet 2
client_1    | INFO:aio_pika.pika.channel:Channel.close(200, Normal shutdown)
client_1    | INFO:aio_pika.pika.connection:Closing connection (200): Normal shutdown
server_b_1  | INFO:root:Message 7: Aggregate data
server_b_1  | INFO:root:Message 9: Generating verify packet 1
client_1    | WARNING:aio_pika.pika.connection:Disconnected from RabbitMQ at rabbitmq:5672 (200): Normal shutdown
client_1    | INFO:root:Client done!
rabbitmq_1  | 2018-11-13 22:04:07.276 [info] <0.407.0> closing AMQP connection <0.407.0> (172.19.0.5:38084 -> 172.19.0.2:5672, vhost: '/', user: 'guest')
server_a_1  | INFO:root:Message 8: Generating verify packet 2
server_b_1  | INFO:root:Message 9: Generating verify packet 2
server_a_1  | INFO:root:Message 8: Aggregate data
server_a_1  | INFO:root:Message 9: Generating verify packet 2
server_a_1  | INFO:root:Message 9: Aggregate data
server_b_1  | INFO:root:Message 8: Aggregate data
server_b_1  | INFO:root:Message 9: Aggregate data
docker-asyncio_client_1 exited with code 0
````