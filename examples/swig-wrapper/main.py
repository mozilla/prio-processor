# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from prio import libprio as prio
from array import array

skA, pkA = prio.Keypair_new()
skB, pkB = prio.Keypair_new()

n_data = 133
batch_id = b"test_batch"
cfg = prio.PrioConfig_new(n_data, pkA, pkB, batch_id)

server_secret = prio.PrioPRGSeed_randomize()

sA = prio.PrioServer_new(cfg, prio.PRIO_SERVER_A, skA, server_secret)
sB = prio.PrioServer_new(cfg, prio.PRIO_SERVER_B, skB, server_secret)

vA = prio.PrioVerifier_new(sA)
vB = prio.PrioVerifier_new(sB)

tA = prio.PrioTotalShare_new()
tB = prio.PrioTotalShare_new()

p1A = prio.PrioPacketVerify1_new()
p1B = prio.PrioPacketVerify1_new()
p2A = prio.PrioPacketVerify2_new()
p2B = prio.PrioPacketVerify2_new()

data_items = bytes([(i % 3 == 1) or (i % 5 == 1) for i in range(n_data)])
for_server_a, for_server_b = prio.PrioClient_encode(cfg, data_items)

# Setup verification
prio.PrioVerifier_set_data(vA, for_server_a)
prio.PrioVerifier_set_data(vB, for_server_b)

# Produce a packet1 and send to the other party
prio.PrioPacketVerify1_set_data(p1A, vA)
prio.PrioPacketVerify1_set_data(p1B, vB)

# Produce packet2 and send to the other party
prio.PrioPacketVerify2_set_data(p2A, vA, p1A, p1B)
prio.PrioPacketVerify2_set_data(p2B, vB, p1A, p1B)

# Check validity of the request
prio.PrioVerifier_isValid(vA, p2A, p2B)
prio.PrioVerifier_isValid(vB, p2A, p2B)

prio.PrioServer_aggregate(sA, vA)
prio.PrioServer_aggregate(sB, vB)

# Collect from many clients and share data
prio.PrioTotalShare_set_data(tA, sA)
prio.PrioTotalShare_set_data(tB, sB)

output = prio.PrioTotalShare_final(cfg, tA, tB)
output = array("L", output)

# check the output
assert list(data_items) == list(output), "results do not match"
print(f"{list(output)}")
