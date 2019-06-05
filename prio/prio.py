# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from . import libprio
from array import array

# re-export enums
PRIO_SERVER_A = libprio.PRIO_SERVER_A
PRIO_SERVER_B = libprio.PRIO_SERVER_B

# Serializable
class PRGSeed:
    def __init__(self):
        self.instance = libprio.PrioPRGSeed_randomize()


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
        self.server_a = server_a
        self.server_b = server_b
        self.instance = libprio.PrioConfig_new(
            n_fields, server_a.instance, server_b.instance, batch_id
        )
        self.batch_id = batch_id

    def num_data_fields(self):
        return libprio.PrioConfig_numDataFields(self.instance)


class TestConfig(Config):
    def __init__(self, n_fields):
        self.instance = libprio.PrioConfig_newTest(n_fields)


class PublicKey:
    def __init__(self, instance=None):
        self.instance = instance

    def import_bin(self, data):
        """Import a curve25519 key from a raw byte string.

        :param data: a bytestring of length `CURVE25519_KEY_LEN`
        """
        self.instance = libprio.PublicKey_import(data)
        return self

    def import_hex(self, data):
        """Import a curve25519 key from a case-insenstive hex string.

        :param data: a hex bytestring of length `CURVE25519_KEY_LEN_HEX`
        """
        self.instance = libprio.PublicKey_import_hex(data)
        return self

    def export_bin(self):
        """Export a curve25519 public key as a bytestring."""
        if not self.instance:
            return None
        return libprio.PublicKey_export(self.instance)

    def export_hex(self):
        """Export a curve25519 public key as a NULL-terminated hex bytestring."""
        if not self.instance:
            return None
        return libprio.PublicKey_export_hex(self.instance)


class PrivateKey:
    def __init__(self, instance=None):
        self.instance = instance

    def import_bin(self, pvtdata, pubdata):
        """Import a curve25519 key from a raw byte string.

        :param pvtdata: a bytestring of length `CURVE25519_KEY_LEN`
        :param pubdata: a bytestring of length `CURVE25519_KEY_LEN`
        """
        self.instance = libprio.PrivateKey_import(pvtdata, pubdata)
        return self

    def import_hex(self, pvtdata, pubdata):
        """Import a curve25519 key from a case-insenstive hex string.

        :param pvtdata: a hex bytestring of length `CURVE25519_KEY_LEN_HEX`
        :param pubdata: a hex bytestring of length `CURVE25519_KEY_LEN_HEX`
        """
        self.instance = libprio.PrivateKey_import_hex(pvtdata, pubdata)
        return self

    def export_bin(self):
        """Export a curve25519 public key as a bytestring."""
        if not self.instance:
            return None
        return libprio.PrivateKey_export(self.instance)

    def export_hex(self):
        """Export a curve25519 public key as a NULL-terminated hex bytestring."""
        if not self.instance:
            return None
        return libprio.PrivateKey_export_hex(self.instance)[:-1]


class Client:
    """Encodes measurements into two shares.

    :param config: An instance of the config
    """

    def __init__(self, config):
        self.config = config

    def encode(self, data):
        return libprio.PrioClient_encode(self.config.instance, data)


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
        self.instance = libprio.PrioServer_new(
            config.instance, server_id, private_key.instance, secret.instance
        )

    def create_verifier(self, data):
        return Verifier(self, data)

    def aggregate(self, verifier):
        libprio.PrioServer_aggregate(self.instance, verifier.instance)

    def total_shares(self):
        return TotalShare(self)


class Verifier:
    """The verifier is not serializable because of the reference to the
    server. The verification packets are.
    """

    def __init__(self, server, data):
        self.server = server
        self.instance = libprio.PrioVerifier_new(server.instance)
        libprio.PrioVerifier_set_data(self.instance, data)

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
            libprio.PrioVerifier_isValid(
                self.instance, verify2A.instance, verify2B.instance
            )
            return True
        except RuntimeError:
            return False


# Serializable
class PacketVerify1:
    def __init__(self, verifier):
        self.instance = libprio.PrioPacketVerify1_new()
        libprio.PrioPacketVerify1_set_data(self.instance, verifier.instance)
        self._serial_data = None

    def deserialize(self, config):
        if self._serial_data:
            libprio.PrioPacketVerify1_read(
                self.instance, self._serial_data, config.instance
            )
        self._serial_data = None

    def __getstate__(self):
        return libprio.PrioPacketVerify1_write(self.instance)

    def __setstate__(self, state):
        self.instance = libprio.PrioPacketVerify1_new()
        self._serial_data = state


# Serializable
class PacketVerify2:
    def __init__(self, verifier, A, B):
        self.instance = libprio.PrioPacketVerify2_new()
        libprio.PrioPacketVerify2_set_data(
            self.instance, verifier.instance, A.instance, B.instance
        )
        self._serial_data = None

    def deserialize(self, config):
        if self._serial_data:
            libprio.PrioPacketVerify2_read(
                self.instance, self._serial_data, config.instance
            )
        self._serial_data = None

    def __getstate__(self):
        return libprio.PrioPacketVerify2_write(self.instance)

    def __setstate__(self, state):
        self.instance = libprio.PrioPacketVerify2_new()
        self._serial_data = state


# Serializable
class TotalShare:
    def __init__(self, server):
        self.instance = libprio.PrioTotalShare_new()
        libprio.PrioTotalShare_set_data(self.instance, server.instance)
        self._serial_data = None

    def deserialize(self, config):
        if self._serial_data:
            libprio.PrioTotalShare_read(
                self.instance, self._serial_data, config.instance
            )
        self._serial_data = None

    def __getstate__(self):
        return libprio.PrioTotalShare_write(self.instance)

    def __setstate__(self, state):
        self.instance = libprio.PrioTotalShare_new()
        self._serial_data = state


def create_keypair():
    secret, public = libprio.Keypair_new()
    return PrivateKey(secret), PublicKey(public)


def total_share_final(config, tA, tB):
    tA.deserialize(config)
    tB.deserialize(config)
    final = libprio.PrioTotalShare_final(config.instance, tA.instance, tB.instance)
    return array("L", final)
