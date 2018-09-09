# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from lib import prio

class Config:
    """An object that stores system parameters.

    The config object stores the number of data fields that are collected
    and the modulus for modular arithmetic. The default configuration uses
    an 87-bit modulus.

    :param n_fields: The number of fields that are collected.
    :param server_a: PublicKey of server A
    :param server_b: PublicKey of server B
    :param batch_id: Which batch of aggregate statistics we are computing.
    """
    def __init__(self, n_fields, server_a, server_b, batch_id):
        self.config = prio.PrioConfig_new(n_fields, server_a, server_b, batch_id)

    def num_data_fields(self):
        return prio.PrioConfig_numDataFields(self.config)

    def __del__(self):
        prio.PrioConfig_clear(self.config)


class TestConfig(Config):
    def __init__(self, n_fields):
        self.config = prio.PrioConfig_newTest(n_fields)


class PublicKey:
    def __init__(self):
        pass

    def import(self, data):
        # PublicKey_import
        pass

    def import_hex(self, data):
        # PublicKey_import_hex
        pass

    def export(self, data):
        # PublicKey_export
        pass

    def export_hex(self):
        # PublicKey_export_hex
        pass

    def __del__(self):
        # PublicKey_clear
        pass


class PrivateKey:
    def __init__(self):
        pass

    def __del__(self):
        # PrivateKey_clear
        pass


class Keypair:
    def __init__(self):
        # Keypair_new
        pass


class Client:
    def __init__(self):
        pass

    def encode(self, data):
        pass


class Server:
    def __init__(self):
        # PrioServer_new
        pass

    def __del__(self):
        # PrioServer_clear
        pass

class Verifier:
    def __init__(self, server):
        pass

    def __del__(self):
        # PrioVerifier_new
        pass

    def set_data(self, data):
        # PrioVerifier_set_data
        pass


class PacketVerify1:
    def __init__(self):
        # PrioPacketVerify1_new
        pass

    def __del__(self):
        # PrioPacketVerify2_clear
        pass


class PacketVerify2:
    def __init__(self):
        pass


class TotalShare:
    def __init__(self):
        pass
