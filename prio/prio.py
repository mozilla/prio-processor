# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from .lib import prio
from array import array

# re-export enums
PRIO_SERVER_A = prio.PRIO_SERVER_A
PRIO_SERVER_B = prio.PRIO_SERVER_B

# Serializable
class PRGSeed:
    def __init__(self):
        self.instance = prio.PrioPRGSeed_randomize()

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
        self.instance = prio.PrioConfig_new(
            n_fields,
            server_a.instance,
            server_b.instance,
            batch_id)

    def num_data_fields(self):
        return prio.PrioConfig_numDataFields(self.instance)


class TestConfig(Config):
    def __init__(self, n_fields):
        self.instance = prio.PrioConfig_newTest(n_fields)


class PublicKey:
    def __init__(self, instance=None):
        self.instance = instance

    def import_bin(self, data):
        """Import a curve25519 key from a raw byte string.

        :param data: a bytestring of length `CURVE25519_KEY_LEN`
        """
        self.instance = prio.PublicKey_import(data)
        return self

    def import_hex(self, data):
        """Import a curve25519 key from a case-insenstive hex string.

        :param data: a hex bytestring of length `CURVE25519_KEY_LEN_HEX`
        """
        self.instance = prio.PublicKey_import_hex(data)
        return self

    def export_bin(self):
        """Export a curve25519 public key as a bytestring."""
        if not self.instance:
            return None
        return prio.PublicKey_export(self.instance)

    def export_hex(self):
        """Export a curve25519 public key as a NULL-terminated hex bytestring."""
        if not self.instance:
            return None
        return prio.PublicKey_export_hex(self.instance)


class PrivateKey:
    def __init__(self, instance=None):
        self.instance = instance

    def import_bin(self, pvtdata, pubdata):
        """Import a curve25519 key from a raw byte string.

        :param pvtdata: a bytestring of length `CURVE25519_KEY_LEN`
        :param pubdata: a bytestring of length `CURVE25519_KEY_LEN`
        """
        self.instance = prio.PrivateKey_import(pvtdata, pubdata)
        return self

    def import_hex(self, pvtdata, pubdata):
        """Import a curve25519 key from a case-insenstive hex string.

        :param pvtdata: a hex bytestring of length `CURVE25519_KEY_LEN_HEX`
        :param pubdata: a hex bytestring of length `CURVE25519_KEY_LEN_HEX`
        """
        self.instance = prio.PrivateKey_import_hex(pvtdata, pubdata)

    def export_bin(self):
        """Export a curve25519 public key as a bytestring."""
        if not self.instance:
            return None
        return prio.PrivateKey_export(self.instance)

    def export_hex(self):
        """Export a curve25519 public key as a NULL-terminated hex bytestring."""
        if not self.instance:
            return None
        return prio.PrivateKey_export_hex(self.instance)


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
        self.config = config
        self.server_id = server_id
        self.instance = prio.PrioServer_new(
            config.instance,
            server_id,
            private_key.instance,
            secret.instance)

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
        self.server = server
        self.instance = prio.PrioVerifier_new(server.instance)
        prio.PrioVerifier_set_data(self.instance, data)

    def create_verify1(self):
        return PacketVerify1(self)

    def create_verify2(self, verify1A, verify1B):
        # Deserialization requires context from the shared config. It would be nice
        # to isolate this behavior to the class, but serializing the entire config
        # is probably not a good idea.
        verify1A.deserialize(self.server.config)
        verify1B.deserialize(self.server.config)

        return PacketVerify2(self, verify1A, verify1B)

    def is_valid(self, verify2A, verify2B):
        verify2A.deserialize(self.server.config)
        verify2B.deserialize(self.server.config)

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
        self._serial_data = None

    def deserialize(self, config):
        if self._serial_data:
            prio.PrioPacketVerify1_read(self.instance, self._serial_data, config.instance)
        self._serial_data = None

    def __getstate__(self):
        return prio.PrioPacketVerify1_write(self.instance)

    def __setstate__(self, state):
        self.instance = prio.PrioPacketVerify1_new()
        self._serial_data = state


# Serializable
class PacketVerify2:
    def __init__(self, verifier, A, B):
        self.instance = prio.PrioPacketVerify2_new()
        prio.PrioPacketVerify2_set_data(self.instance, verifier.instance, A.instance, B.instance)
        self._serial_data = None

    def deserialize(self, config):
        if self._serial_data:
            prio.PrioPacketVerify2_read(self.instance, self._serial_data, config.instance)
        self._serial_data = None

    def __getstate__(self):
        return prio.PrioPacketVerify2_write(self.instance)

    def __setstate__(self, state):
        self.instance = prio.PrioPacketVerify2_new()
        self._serial_data = state


# Serializable
class TotalShare:
    def __init__(self, server):
        self.instance = prio.PrioTotalShare_new()
        prio.PrioTotalShare_set_data(self.instance, server.instance)
        self._serial_data = None

    def deserialize(self, config):
        if self._serial_data:
            prio.PrioTotalShare_read(self.instance, self._serial_data, config.instance)
        self._serial_data = None

    def __getstate__(self):
        return prio.PrioTotalShare_write(self.instance)

    def __setstate__(self, state):
        self.instance = prio.PrioTotalShare_new()
        self._serial_data = state


def create_keypair():
    secret, public = prio.Keypair_new()
    return PrivateKey(secret), PublicKey(public)


def total_share_final(config, tA, tB):
    tA.deserialize(config)
    tB.deserialize(config)
    final = prio.PrioTotalShare_final(config.instance, tA.instance, tB.instance)
    return array('L', final)
