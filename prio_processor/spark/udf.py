import logging
from collections import Counter
import array

import pandas as pd
from prio import PrioContext, libprio
from prio_processor.prio.commands import import_keys, import_public_keys, match_server

logger = logging.getLogger(__name__)


def encode_single(
    batch_id: str,
    n_data: int,
    public_key_hex_internal: bytearray,
    public_key_hex_external: bytearray,
    payload: list,
):
    libprio.Prio_init()
    public_key_internal, public_key_external = import_public_keys(
        bytes(public_key_hex_internal), bytes(public_key_hex_external)
    )
    config = libprio.PrioConfig_new(
        n_data, public_key_internal, public_key_external, batch_id.encode()
    )
    try:
        a, b = libprio.PrioClient_encode(config, bytes(list(map(int, payload))))
    except:
        a, b = None, None
    libprio.Prio_clear()
    return dict(a=a, b=b)


def encode(
    batch_id: bytes,
    n_data: int,
    public_key_hex_internal: bytes,
    public_key_hex_external: bytes,
    payload: pd.Series,
) -> pd.DataFrame:
    libprio.Prio_init()
    public_key_internal, public_key_external = import_public_keys(
        public_key_hex_internal, public_key_hex_external
    )
    config = libprio.PrioConfig_new(
        n_data, public_key_internal, public_key_external, batch_id
    )
    results = []
    for data in payload:
        # trying to encode the integer into a bit array
        try:
            a, b = libprio.PrioClient_encode(config, bytes(list(map(int, data))))
        except:
            a, b = None, None
        results.append(dict(a=a, b=b))
    libprio.Prio_clear()
    return pd.DataFrame(results)


def verify1(
    batch_id: bytes,
    n_data: int,
    server_id: str,
    private_key_hex: bytes,
    shared_secret: bytes,
    public_key_hex_internal: bytes,
    public_key_hex_external: bytes,
    shares: pd.Series,
) -> pd.Series:
    # NOTE: there is an initialization call without the corresponding clear
    # function because clearing the NSS context before the work is done causes
    # issues when working across threads and processes. Initialization is
    # idempotent, and it shouldn't matter if it's being called more than once.
    # Not entirely sure why it's necessary here, but not in other grouped map
    # functions.
    libprio.Prio_init()

    def _process(share):
        private_key, public_key_internal, public_key_external = import_keys(
            private_key_hex, public_key_hex_internal, public_key_hex_external
        )
        config = libprio.PrioConfig_new(
            n_data, public_key_internal, public_key_external, batch_id
        )
        server = libprio.PrioServer_new(
            config, match_server(server_id), private_key, shared_secret
        )
        verifier = libprio.PrioVerifier_new(server)
        packet = libprio.PrioPacketVerify1_new()
        try:
            # share is actually a bytearray, so convert it into bytes
            libprio.PrioVerifier_set_data(verifier, bytes(share))
            libprio.PrioPacketVerify1_set_data(packet, verifier)
            data = libprio.PrioPacketVerify1_write(packet)
        except:
            data = None
        return data

    results = [_process(share) for share in shares]
    libprio.Prio_clear()
    return pd.Series(results, name="payload")


def verify2(
    batch_id: bytes,
    n_data: int,
    server_id: str,
    private_key_hex: bytes,
    shared_secret: bytes,
    public_key_hex_internal: bytes,
    public_key_hex_external: bytes,
    shares: pd.Series,
    internal: pd.Series,
    external: pd.Series,
) -> pd.Series:
    libprio.Prio_init()

    def _process(share, internal, external):
        private_key, public_key_internal, public_key_external = import_keys(
            private_key_hex, public_key_hex_internal, public_key_hex_external
        )

        config = libprio.PrioConfig_new(
            n_data, public_key_internal, public_key_external, batch_id
        )
        server = libprio.PrioServer_new(
            config, match_server(server_id), private_key, shared_secret
        )
        verifier = libprio.PrioVerifier_new(server)

        packet1_internal = libprio.PrioPacketVerify1_new()
        packet1_external = libprio.PrioPacketVerify1_new()
        packet = libprio.PrioPacketVerify2_new()
        try:
            libprio.PrioVerifier_set_data(verifier, bytes(share))
            libprio.PrioPacketVerify1_read(packet1_internal, bytes(internal), config)
            libprio.PrioPacketVerify1_read(packet1_external, bytes(external), config)
            libprio.PrioPacketVerify2_set_data(
                packet, verifier, packet1_internal, packet1_external
            )
            data = libprio.PrioPacketVerify2_write(packet)
        except:
            data = None
        return data

    results = [_process(share, x, y) for share, x, y in zip(shares, internal, external)]
    libprio.Prio_clear()
    return pd.Series(results, name="payload")


def aggregate(
    batch_id: bytes,
    n_data: int,
    server_id: str,
    private_key_hex: bytes,
    shared_secret: bytes,
    public_key_hex_internal: bytes,
    public_key_hex_external: bytes,
    pdf: pd.DataFrame,
) -> pd.DataFrame:
    """This method is unique from the others because it relies on the use of a
    grouped map. This requires the use of Dataframe.applyInPandas which takes
    two parameters.

    schema: payload binary, error int, total int
    """
    libprio.Prio_init()
    private_key, public_key_internal, public_key_external = import_keys(
        private_key_hex, public_key_hex_internal, public_key_hex_external
    )

    config = libprio.PrioConfig_new(
        n_data, public_key_internal, public_key_external, batch_id
    )
    server = libprio.PrioServer_new(
        config, match_server(server_id), private_key, shared_secret
    )
    verifier = libprio.PrioVerifier_new(server)
    packet2_internal = libprio.PrioPacketVerify2_new()
    packet2_external = libprio.PrioPacketVerify2_new()
    # assumes each row in the iterator contains the literal information
    # necessary for processing the data. It should have a input, input_internal,
    # and input_external row
    total, error = 0, 0
    error_counter = Counter()
    for share, internal, external in zip(pdf.shares, pdf.internal, pdf.external):
        total += 1
        try:
            libprio.PrioVerifier_set_data(verifier, share)
            libprio.PrioPacketVerify2_read(packet2_internal, internal, config)
            libprio.PrioPacketVerify2_read(packet2_external, external, config)
            libprio.PrioVerifier_isValid(verifier, packet2_internal, packet2_external)
            libprio.PrioServer_aggregate(server, verifier)
        except Exception as e:
            error += 1
            error_counter.update([f"server {server_id}: {e}"])
    logger.warning(error_counter)
    result = [dict(payload=libprio.PrioServer_write(server), error=error, total=total)]
    libprio.Prio_clear()
    return pd.DataFrame(result)


def total_share(
    batch_id: bytes,
    n_data: int,
    server_id: str,
    private_key_hex: bytes,
    shared_secret: bytes,
    public_key_hex_internal: bytes,
    public_key_hex_external: bytes,
    pdf: pd.DataFrame,
) -> pd.DataFrame:
    """schema: payload binary, error int, total int"""
    libprio.Prio_init()
    private_key, public_key_internal, public_key_external = import_keys(
        private_key_hex, public_key_hex_internal, public_key_hex_external
    )
    config = libprio.PrioConfig_new(
        n_data, public_key_internal, public_key_external, batch_id
    )
    server = libprio.PrioServer_new(
        config, match_server(server_id), private_key, shared_secret
    )
    server_i = libprio.PrioServer_new(
        config, match_server(server_id), private_key, shared_secret
    )
    # NOTE: this breaks expectations from other udfs, which expects shares,
    # internal, external etc.
    for aggregates in pdf["payload"]:
        libprio.PrioServer_read(server_i, aggregates, config)
        libprio.PrioServer_merge(server, server_i)

    total_share = libprio.PrioTotalShare_new()
    libprio.PrioTotalShare_set_data(total_share, server)
    result = [
        dict(
            payload=libprio.PrioTotalShare_write(total_share),
            error=pdf.error.sum(),
            total=pdf.total.sum(),
        )
    ]
    libprio.Prio_clear()
    return pd.DataFrame(result)


def publish(
    batch_id: bytes,
    n_data: int,
    server_id: str,
    private_key_hex: bytes,
    shared_secret: bytes,
    public_key_hex_internal: bytes,
    public_key_hex_external: bytes,
    data_internal: pd.Series,
    data_external: pd.Series,
) -> pd.Series:
    libprio.Prio_init()

    def _process(internal, external):
        _, public_key_internal, public_key_external = import_keys(
            private_key_hex, public_key_hex_internal, public_key_hex_external
        )
        config = libprio.PrioConfig_new(
            n_data, public_key_internal, public_key_external, batch_id
        )
        share_internal = libprio.PrioTotalShare_new()
        share_external = libprio.PrioTotalShare_new()
        libprio.PrioTotalShare_read(share_internal, internal, config)
        libprio.PrioTotalShare_read(share_external, external, config)

        # ordering matters
        if match_server(server_id) == libprio.PRIO_SERVER_B:
            share_internal, share_external = share_external, share_internal

        total_share = libprio.PrioTotalShare_final(
            config, share_internal, share_external
        )
        return list(array.array("L", total_share))

    results = [
        _process(internal, external)
        for internal, external in zip(data_internal, data_external)
    ]
    libprio.Prio_clear()
    return pd.Series(results, name="payload")
