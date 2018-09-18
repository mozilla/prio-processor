# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
from prio import prio

@pytest.mark.parametrize("n_clients", [1, 2, 10])
def test_client_agg(n_clients):
    seed = prio.PRGSeed()

    skA, pkA = prio.create_keypair()
    skB, pkB = prio.create_keypair()

    # the config is shared across all actors
    config = prio.Config(133, pkA, pkB, b"test_batch")

    sA = prio.Server(config, prio.PRIO_SERVER_A, skA, seed)
    sB = prio.Server(config, prio.PRIO_SERVER_B, skB, seed)

    client = prio.Client(config)

    n_data = config.num_data_fields()
    data_items = bytearray([(i % 3 == 1) or (i % 5 == 1) for i in range(n_data)])

    for i in range(n_clients):
        for_server_a, for_server_b = client.encode(data_items)

        # Setup verification
        vA = sA.create_verifier(for_server_a)
        vB = sB.create_verifier(for_server_b)

        # Produce a packet1 and send to the other party
        p1A = vA.create_verify1()
        p1B = vB.create_verify1()

        # Produce packet2 and send to the other party
        p2A = vA.create_verify2(p1A, p1B)
        p2B = vB.create_verify2(p1A, p1B)

        assert vA.is_valid(p2A, p2B)
        assert vB.is_valid(p2A, p2B)

        sA.aggregate(vA)
        sB.aggregate(vB)

    t_a = sA.total_shares()
    t_b = sB.total_shares()

    output = prio.total_share_final(config, t_a, t_b)

    expected = [item*n_clients for item in list(data_items)]
    assert(list(output) == expected)
