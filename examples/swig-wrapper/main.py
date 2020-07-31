# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from prio.libprio import *
from array import array

Prio_init()
skA, pkA = Keypair_new()
skB, pkB = Keypair_new()

n_data = 133
batch_id = b"test_batch"
cfg = PrioConfig_new(n_data, pkA, pkB, batch_id)

server_secret = PrioPRGSeed_randomize()

sA = PrioServer_new(cfg, PRIO_SERVER_A, skA, server_secret)
sB = PrioServer_new(cfg, PRIO_SERVER_B, skB, server_secret)

vA = PrioVerifier_new(sA)
vB = PrioVerifier_new(sB)

tA = PrioTotalShare_new()
tB = PrioTotalShare_new()

p1A = PrioPacketVerify1_new()
p1B = PrioPacketVerify1_new()
p2A = PrioPacketVerify2_new()
p2B = PrioPacketVerify2_new()

data_items = bytes([(i % 3 == 1) or (i % 5 == 1) for i in range(n_data)])
for_server_a, for_server_b = PrioClient_encode(cfg, data_items)

# Setup verification
PrioVerifier_set_data(vA, for_server_a)
PrioVerifier_set_data(vB, for_server_b)

# Produce a packet1 and send to the other party
PrioPacketVerify1_set_data(p1A, vA)
PrioPacketVerify1_set_data(p1B, vB)

# Produce packet2 and send to the other party
PrioPacketVerify2_set_data(p2A, vA, p1A, p1B)
PrioPacketVerify2_set_data(p2B, vB, p1A, p1B)

# Check validity of the request
PrioVerifier_isValid(vA, p2A, p2B)
PrioVerifier_isValid(vB, p2A, p2B)

PrioServer_aggregate(sA, vA)
PrioServer_aggregate(sB, vB)

# Collect from many clients and share data
PrioTotalShare_set_data(tA, sA)
PrioTotalShare_set_data(tB, sB)

output = PrioTotalShare_final(cfg, tA, tB)
output = array("L", output)

# check the output
assert list(data_items) == list(output), "results do not match"
print(f"{list(output)}")
Prio_clear()
