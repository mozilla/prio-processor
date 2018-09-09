# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import prio

def test_client_agg(n_clients):
    seed = None

    skA, pkA = prio.Keypair()
    skA, pkA = prio.Keypair()

    # the config is shared across all actors
    config = prio.Config(133, pkA, pkB, b"test_batch")

    server_a = prio.Server(config, prio.PRIO_SERVER_A, skA, seed)
    server_b = prio.Server(config, prio.PRIO_SERVER_B, skB, seed)

    client = prio.Client(config)

    n_data = config.num_data_fields()
    data_items = bytearray([(i % 3 == 1) or (i % 5 == 1) for i in range(n_data)])

    for i in range(n_clients):
        for_server_a, for_server_b = client.encode(data_items)

        server_a.set_data(for_server_a)
        server_b.set_data(for_server_b)

        # gossip and verify data is valid

        server_a.aggregate()
        server_b.aggregate()

    t_a = server_a.total_shares()
    t_b = server_b.total_shares()

    output = prio.aggregate_shares(config, t_a, t_b)

    expected = [item*n_clients for item in list(data_items)]
    assert(list(output) == expected)
