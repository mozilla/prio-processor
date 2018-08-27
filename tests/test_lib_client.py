# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
from prio.lib import prio
import array


@pytest.mark.parametrize("n_clients", [1, 2, 10])
def test_client_agg(n_clients):
    prio.Prio_init()

    seed = prio.PrioPRGSeed_new()
    seed = prio.PrioPRGSeed_randomize(seed)

    skA, pkA = prio.Keypair_new(0, 0)
    skB, pkB = prio.Keypair_new(0, 0)
    cfg = prio.PrioConfig_new(133, pkA, pkB, b"test_batch")
    sA = prio.PrioServer_new(cfg, prio.PRIO_SERVER_A, skA, seed)
    sB = prio.PrioServer_new(cfg, prio.PRIO_SERVER_B, skB, seed)
    vA = prio.PrioVerifier_new(sA)
    vB = prio.PrioVerifier_new(sB)
    tA = prio.PrioTotalShare_new()
    tB = prio.PrioTotalShare_new()

    n_data = prio.PrioConfig_numDataFields(cfg)
    data_items = bytearray([(i % 3 == 1) or (i % 5 == 1) for i in range(n_data)])

    for i in range(n_clients):
        for_server_a, for_server_b = prio.PrioClient_encode(cfg, data_items)

        prio.PrioVerifier_set_data(vA, for_server_a)
        prio.PrioVerifier_set_data(vB, for_server_b)

        prio.PrioServer_aggregate(sA, vA)
        prio.PrioServer_aggregate(sB, vB)

    prio.PrioTotalShare_set_data(tA, sA)
    prio.PrioTotalShare_set_data(tB, sB)

    output = array.array('L', prio.PrioTotalShare_final(cfg, tA, tB))

    expected = [item*n_clients for item in list(data_items)]
    assert(list(output) == expected)

    prio.PublicKey_clear(pkA)
    prio.PublicKey_clear(pkB)
    prio.PrivateKey_clear(skA)
    prio.PrivateKey_clear(skB)

    prio.PrioVerifier_clear(vA)
    prio.PrioVerifier_clear(vB)

    prio.PrioTotalShare_clear(tA)
    prio.PrioTotalShare_clear(tB)

    prio.PrioServer_clear(sA)
    prio.PrioServer_clear(sB)
    prio.PrioConfig_clear(cfg)
