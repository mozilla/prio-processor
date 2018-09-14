# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from .lib import prio
from array import array

# Serializable
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
        self.instance = prio.PrioConfig_new(n_fields, server_a, server_b, batch_id)

    def num_data_fields(self):
        return prio.PrioConfig_numDataFields(self.instance)

    def __del__(self):
        prio.PrioConfig_clear(self.instance)


class TestConfig(Config):
    def __init__(self, n_fields):
        self.instance = prio.PrioConfig_newTest(n_fields)


class PublicKey:
    def __init__(self):
        pass

    def import_key(self, data):
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
    def __init__(self, config):
        self.config = config

    def encode(self, data):
        return prio.PrioClient_encode(self.config.instance, data)


class Server:
    def __init__(self, config, server_id, private_key, secret):
        """Run the verification and aggregation routines.

        :param config: An instance of the config
        :param server_id: The enumeration of valid servers
        :param private_key: The server's private key used for decryption
        :param secret: The shared random seed
        """
        self.instance = prio.PrioServer_new(config.instance, server_id, private_key, secret)

    def __del__(self):
        prio.PrioServer_clear(self.instance)

    def create_verifier(self, data):
        return Verifier(self, data)

    def aggregate(self, verifier):
        prio.PrioServer_aggregate(self.instance, verifier.instance)

    def total_shares(self):
        return TotalShare(self)


class Verifier:
    """The verifier is not serializable because of the reference to the
    server. The verification packets are.
    """
    def __init__(self, server, data):
        self.instance = prio.PrioVerifier_new(server.instance)
        prio.PrioVerifier_set_data(self.instance, data)

    def __del__(self):
        prio.PrioVerifier_clear(self.instance)

    def create_verify1(self):
        return PacketVerify1(self)

    def create_verify2(self, verify1A, verify1B):
        return PacketVerify2(self, verify1A, verify1B)

    def is_valid(self, verify2A, verify2B):
        # TODO: replace try except block by wrapping function in swig typemap
        try:
            prio.PrioVerifier_isValid(self.instance, verify2A.instance, verify2B.instance)
            return True
        except RuntimeError:
            return False


# Serializable
class PacketVerify1:
    def __init__(self, verifier):
        self.instance = prio.PrioPacketVerify1_new()
        prio.PrioPacketVerify1_set_data(self.instance, verifier.instance)

    def __del__(self):
        prio.PrioPacketVerify1_clear(self.instance)

# Serializable
class PacketVerify2:
    def __init__(self, verifier, A, B):
        self.instance = prio.PrioPacketVerify2_new()
        prio.PrioPacketVerify2_set_data(self.instance, verifier.instance, A.instance, B.instance)

    def __del__(self):
        prio.PrioPacketVerify2_clear(self.instance)

# Serializable
class TotalShare:
    def __init__(self, server):
        self.instance = prio.PrioTotalShare_new()
        prio.PrioTotalShare_set_data(self.instance, server.instance)

    def __del__(self):
        prio.PrioTotalShare_clear(self.instance)


def total_share_final(config, tA, tB):
    final = prio.PrioTotalShare_final(config.instance, tA.instance, tB.instance)
    return array('L', final)