# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from lib import prio

class Config:
    def __init__(self, n_fields, server_a, server_b, batch_id):
        self.config = prio.PrioConfig_new(n_fields, server_a, server_b, batch_id, len(batch_id))

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


class PrivateKey:
    def __init__(self):
        pass


class Keypair:
    def __init__(self):
        pass


class Client:
    def __init__(self):
        pass


class Server:
    def __init__(self):
        pass


class Verifier:
    def __init__(self):
        pass


class PacketVerify1:
    def __init__(self):
        pass


class PacketVerify2:
    def __init__(self):
        pass


class TotalShare:
    def __init__(self):
        pass
