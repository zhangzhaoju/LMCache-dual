# SPDX-License-Identifier: Apache-2.0
"""Unquantized KV serialization for the paired Ascend engine."""

from lmcache.v1.config import LMCacheEngineConfig
from lmcache.v1.metadata import LMCacheMetadata
from lmcache.v1.storage_backend.naive_serde.naive_serde import (
    NaiveDeserializer,
    NaiveSerializer,
)
from lmcache.v1.storage_backend.naive_serde.serde import Deserializer, Serializer


def CreateSerde(
    serde_type: str, metadata: LMCacheMetadata, config: LMCacheEngineConfig
) -> tuple[Serializer, Deserializer]:
    """Reject removed CUDA CacheGen/KIVI providers before any allocation."""
    if serde_type != "naive":
        raise ValueError("Ascend P4 supports only remote_serde=naive")
    return NaiveSerializer(), NaiveDeserializer()


__all__ = ["Serializer", "Deserializer", "CreateSerde"]
