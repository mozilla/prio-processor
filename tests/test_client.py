# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
from prio import prio
from prio.lib import prio as libprio

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
    data_items = bytes([(i % 3 == 1) or (i % 5 == 1) for i in range(n_data)])

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


def test_publickey_export():
    raw_bytes = bytes((3*x + 7) % 0xFF for x in range(libprio.CURVE25519_KEY_LEN))
    pubkey = prio.PublicKey().import_bin(raw_bytes)
    raw_bytes2 = pubkey.export_bin()

    assert raw_bytes == raw_bytes2


@pytest.mark.parametrize("hex_bytes", [
    b"102030405060708090A0B0C0D0E0F00000FFEEDDCCBBAA998877665544332211",
    b"102030405060708090a0B0C0D0E0F00000FfeEddcCbBaa998877665544332211"
])
def test_publickey_import_hex(hex_bytes):
    expect = bytes([
        0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x80, 0x90, 0xA0, 0xB0,
        0xC0, 0xD0, 0xE0, 0xF0, 0x00, 0x00, 0xFF, 0xEE, 0xDD, 0xCC, 0xBB,
        0xAA, 0x99, 0x88, 0x77, 0x66, 0x55, 0x44, 0x33, 0x22, 0x11
    ])

    pubkey = prio.PublicKey().import_hex(hex_bytes)
    raw_bytes = pubkey.export_bin()

    assert raw_bytes == expect


def test_publickey_import_hex_bad_length_raises_exception():
    hex_bytes = b"102030405060708090A"
    pubkey = prio.PublicKey()
    with pytest.raises(RuntimeError):
        pubkey.import_hex(hex_bytes)


def test_publickey_export_hex():
    # the output includes the null-byte
    expect = b"102030405060708090A0B0C0D0E0F00000FFEEDDCCBBAA998877665544332211\0"
    raw_bytes = bytes([
        0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x80, 0x90, 0xA0, 0xB0,
        0xC0, 0xD0, 0xE0, 0xF0, 0x00, 0x00, 0xFF, 0xEE, 0xDD, 0xCC, 0xBB,
        0xAA, 0x99, 0x88, 0x77, 0x66, 0x55, 0x44, 0x33, 0x22, 0x11
    ])
    pubkey = prio.PublicKey().import_bin(raw_bytes)
    hex_bytes = pubkey.export_hex()
    assert bytes(hex_bytes) == expect


def test_publickey_export_missing_key():
    pubkey = prio.PublicKey()
    assert pubkey.export_bin() is None
    assert pubkey.export_hex() is None

def test_privatekey():
    pvtkey, pubkey = prio.create_keypair()
    pvtdata = pvtkey.export_bin()
    pubdata = pubkey.export_bin()
    new_pvtkey = prio.PrivateKey().import_bin(pvtdata, pubdata)
    assert pvtdata == new_pvtkey.export_bin()
