# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from prio import prio
from prio.lib import prio as libprio
import sys

skA, pkA = prio.create_keypair()
skB, pkB = prio.create_keypair()

n_data = 133
batch_id = b"test_batch"
cfg = prio.Config(n_data, pkA, pkB, batch_id)

server_secret = libprio.PrioPRGSeed_new()
server_secret = libprio.PrioPRGSeed_randomize(server_secret)

sA = prio.Server(cfg, libprio.PRIO_SERVER_A, skA, server_secret)
sB = prio.Server(cfg, libprio.PRIO_SERVER_B, skB, server_secret)

client = prio.Client(cfg)

data_items = bytearray([(i % 3 == 1) or (i % 5 == 1) for i in range(n_data)])
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

# Check validity of the request
if not vA.is_valid(p2A, p2B):
    print("data for server A is not valid!")
    sys.exit(1)
if not vB.is_valid(p2A, p2B):
    print("data for server A is not valid!")
    sys.exit(1)

sA.aggregate(vA)
sB.aggregate(vB)

# Collect from many clients and share data
tA = sA.total_shares()
tB = sB.total_shares()

output = prio.total_share_final(cfg, tA, tB)

# check the output
assert(list(data_items) == list(output))
