# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pickle
import pytest
from prio import prio


@pytest.fixture
def seed():
    return prio.PRGSeed()

@pytest.fixture
def serverA_keypair():
    return prio.create_keypair()

@pytest.fixture
def serverB_keypair():
    return prio.create_keypair()

@pytest.fixture
def config(serverA_keypair, serverB_keypair):
    _, pkA = serverA_keypair
    _, pkB = serverB_keypair
    return prio.Config(133, pkA, pkB, b"test_batch")

@pytest.fixture
def serverA(seed, config, serverA_keypair):
    sk, _ = serverA_keypair
    return prio.Server(config, prio.PRIO_SERVER_A, sk, seed)

@pytest.fixture
def serverB(seed, config, serverB_keypair):
    sk, _ = serverB_keypair
    return prio.Server(config, prio.PRIO_SERVER_B, sk, seed)

@pytest.fixture
def client(config):
    return prio.Client(config)

@pytest.mark.skip
def test_serialize_verifier(config, client, serverA, serverB):
    n_data = config.num_data_fields()
    data_items = bytearray([(i % 3 == 1) or (i % 5 == 1) for i in range(n_data)])

    for_server_a, for_server_b = client.encode(data_items)

    def is_valid(vA):
        vB = serverB.create_verifier(for_server_b)

        p1A = vA.create_verify1()
        p1B = vB.create_verify1()

        p2A = vA.create_verify2(p1A, p1B)
        p2B = vB.create_verify2(p1A, p1B)

        return vA.is_valid(p2A, p2B) and vB.is_valid(p2A, p2B)

    vA = serverA.create_verifier(for_server_a)
    assert is_valid(vA)

    vA_ser = pickle.loads(pickle.dumps(vA))
    assert vA is not vA_ser

    # free the pointer instance and double check that the verifier is
    # actually being serialized
    del vA
    assert is_valid(vA_ser)


def test_serialize_verify1(config, client, serverA, serverB):
    n_data = config.num_data_fields()
    data_items = bytearray([(i % 3 == 1) or (i % 5 == 1) for i in range(n_data)])

    for_server_a, for_server_b = client.encode(data_items)

    vA = serverA.create_verifier(for_server_a)
    vB = serverB.create_verifier(for_server_b)

    def is_valid(p1A):
        p1B = vB.create_verify1()

        p2A = vA.create_verify2(p1A, p1B)
        p2B = vB.create_verify2(p1A, p1B)

        return vA.is_valid(p2A, p2B) and vB.is_valid(p2A, p2B)

    p1A = vA.create_verify1()
    assert is_valid(p1A)

    p1A_ser = pickle.loads(pickle.dumps(p1A))
    del p1A
    assert is_valid(p1A_ser)


def test_serialize_verify2(config, client, serverA, serverB):
    n_data = config.num_data_fields()
    data_items = bytearray([(i % 3 == 1) or (i % 5 == 1) for i in range(n_data)])

    for_server_a, for_server_b = client.encode(data_items)

    vA = serverA.create_verifier(for_server_a)
    vB = serverB.create_verifier(for_server_b)

    p1A = vA.create_verify1()
    p1B = vB.create_verify1()

    def is_valid(p2A):
        p2B = vB.create_verify2(p1A, p1B)
        return vA.is_valid(p2A, p2B) and vB.is_valid(p2A, p2B)

    p2A = vA.create_verify2(p1A, p1B)
    assert is_valid(p2A)

    p2A_ser = pickle.loads(pickle.dumps(p2A))
    del p2A
    assert is_valid(p2A_ser)


def test_serialize_total_shares(config, client, serverA, serverB):
    n_data = config.num_data_fields()
    data_items = bytearray([(i % 3 == 1) or (i % 5 == 1) for i in range(n_data)])

    for_server_a, for_server_b = client.encode(data_items)

    vA = serverA.create_verifier(for_server_a)
    vB = serverB.create_verifier(for_server_b)

    p1A = vA.create_verify1()
    p1B = vB.create_verify1()

    p2A = vA.create_verify2(p1A, p1B)
    p2B = vB.create_verify2(p1A, p1B)

    assert vA.is_valid(p2A, p2B) and vB.is_valid(p2A, p2B)

    serverA.aggregate(vA)
    serverB.aggregate(vB)

    def is_expected(t_a):
        t_b = serverB.total_shares()
        output = prio.total_share_final(config, t_a, t_b)
        return list(output) == list(data_items)

    t_a = serverA.total_shares()
    assert is_expected(t_a)

    t_a_ser = pickle.loads(pickle.dumps(t_a))
    del t_a
    assert is_expected(t_a_ser)
