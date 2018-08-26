from prio.lib import prio
from array import array
from pprint import pformat

print(pformat(dir(prio)))

# TODO: return type
_ = prio.Prio_init()

_, skA, pkA = prio.Keypair_new(0, 0)
_, skB, pkB = prio.Keypair_new(0, 0)

# TODO: export hex data into a string
## pk_hexA = prio.buffer.create(CURVE25519_KEY_LEN+1)
# pk_hexA = prio.PublicKey_export_hex(pkA)
# pk_hexB = prio.PublicKey_export_hex(pkB)

# n_clients = 10
n_data = 133
batch_id = b"test_batch"
cfg = prio.PrioConfig_new(n_data, pkA, pkB, batch_id)

server_secret = prio.PrioPRGSeed_new()
_, server_secret = prio.PrioPRGSeed_randomize(server_secret)

sA = prio.PrioServer_new(cfg, prio.PRIO_SERVER_A, skA, server_secret)
sB = prio.PrioServer_new(cfg, prio.PRIO_SERVER_B, skA, server_secret)

vA = prio.PrioVerifier_new(sA)
vB = prio.PrioVerifier_new(sB)

tA = prio.PrioTotalShare_new()
tB = prio.PrioTotalShare_new()

p1A = prio.PrioPacketVerify1_new()
p1B = prio.PrioPacketVerify2_new()
p2A = prio.PrioPacketVerify1_new()
p2B = prio.PrioPacketVerify2_new()

data_items = bytearray([(i % 3 == 1) or (i % 5 == 1) for i in range(n_data)])
_, for_server_a, for_server_b = prio.PrioClient_encode(cfg, data_items)

# Setup verification
_ = prio.PrioVerifier_set_data(vA, for_server_a)
_ = prio.PrioVerifier_set_data(vB, for_server_b)

# Produce a packet1 and send to the other party
_ = prio.PrioPacketVerify1_set_data(p1A, vA)
_ = prio.PrioPacketVerify1_set_data(p1A, vB)

# Produce packet2 and send to the other party
_ = prio.PrioPacketVerify2_set_data(p2A, vA, p1A, p1B)
_ = prio.PrioPacketVerify2_set_data(p2B, vB, p1A, p1B)

# Check validity of the request
_ = prio.PrioVerifier_isValid (vA, p2A, p2B)
_ = prio.PrioVerifier_isValid (vB, p2A, p2B)

_ = prio.PrioServer_aggregate(sA, vA)
_ = prio.PrioServer_aggregate(sB, vB)

# Collect from many clients and share data
_ = prio.PrioTotalShare_set_data(tA, sA)
_ = prio.PrioTotalShare_set_data(tB, sB)

_, output = prio.PrioTotalShare_final(cfg, tA, tB)
output = array('L', output)

# check the output
print(list(data_items) == list(output))