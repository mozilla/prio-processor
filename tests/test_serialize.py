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
    data_items = bytes([(i % 3 == 1) or (i % 5 == 1) for i in range(n_data)])

    for_server_a, for_server_b = client.encode(data_items)

    vA = pickle.loads(pickle.dumps(serverA.create_verifier(for_server_a)))
    vB = serverB.create_verifier(for_server_b)

    p1A = vA.create_verify1()
    p1B = vB.create_verify1()

    p2A = vA.create_verify2(p1A, p1B)
    p2B = vB.create_verify2(p1A, p1B)

    assert vA.is_valid(p2A, p2B)
    assert vB.is_valid(p2A, p2B)


def test_serialize_verify1(config, client, serverA, serverB):
    n_data = config.num_data_fields()
    data_items = bytes([(i % 3 == 1) or (i % 5 == 1) for i in range(n_data)])

    for_server_a, for_server_b = client.encode(data_items)

    vA = serverA.create_verifier(for_server_a)
    vB = serverB.create_verifier(for_server_b)

    p1A = pickle.loads(pickle.dumps(vA.create_verify1()))
    p1B = vB.create_verify1()

    p2A = vA.create_verify2(p1A, p1B)
    p2B = vB.create_verify2(p1A, p1B)

    assert vA.is_valid(p2A, p2B)
    assert vB.is_valid(p2A, p2B)


def test_serialize_verify2(config, client, serverA, serverB):
    n_data = config.num_data_fields()
    data_items = bytes([(i % 3 == 1) or (i % 5 == 1) for i in range(n_data)])

    for_server_a, for_server_b = client.encode(data_items)

    vA = serverA.create_verifier(for_server_a)
    vB = serverB.create_verifier(for_server_b)

    p1A = vA.create_verify1()
    p1B = vB.create_verify1()

    p2A = pickle.loads(pickle.dumps(vA.create_verify2(p1A, p1B)))
    p2B = vB.create_verify2(p1A, p1B)

    assert vA.is_valid(p2A, p2B)
    assert vB.is_valid(p2A, p2B)


def test_serialize_total_shares(config, client, serverA, serverB):
    n_data = config.num_data_fields()
    data_items = bytes([(i % 3 == 1) or (i % 5 == 1) for i in range(n_data)])

    for_server_a, for_server_b = client.encode(data_items)

    vA = serverA.create_verifier(for_server_a)
    vB = serverB.create_verifier(for_server_b)

    p1A = vA.create_verify1()
    p1B = vB.create_verify1()

    p2A = vA.create_verify2(p1A, p1B)
    p2B = vB.create_verify2(p1A, p1B)

    assert vA.is_valid(p2A, p2B)
    assert vB.is_valid(p2A, p2B)

    serverA.aggregate(vA)
    serverB.aggregate(vB)

    t_a = pickle.loads(pickle.dumps(serverA.total_shares()))
    t_b = serverB.total_shares()
    output = prio.total_share_final(config, t_a, t_b)
    assert list(output) == list(data_items)
