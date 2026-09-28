# SPDX-License-Identifier: Apache-2.0
"""Types and custom encoders/decoders for inter-process communication.

IPCCacheEngineKey carries token IDs, start, end and request ID, and is converted
to storage ObjectKey instances by ipc_key_to_object_keys().
"""

# Standard
from dataclasses import dataclass, field
from typing import Any, Callable
import pickle
import re
import subprocess
import threading

# Third Party
import msgspec
import torch
import torch_npu  # noqa: F401


class NPUIPCWrapper:
    _discovered_device_mapping: dict[str, int] = {}

    _device_mapping_lock = threading.Lock()

    def __eq__(self, other):
        if not isinstance(other, NPUIPCWrapper):
            return False
        return (
            self.handle == other.handle
            and self.dtype == other.dtype
            and self.shape == other.shape
            and self.stride == other.stride
            and self.storage_offset == other.storage_offset
            and self.device_uuid == other.device_uuid
        )

    @staticmethod
    def Serialize(obj: "NPUIPCWrapper") -> bytes:
        return pickle.dumps(obj)

    @staticmethod
    def Deserialize(data: bytes) -> "NPUIPCWrapper":
        return pickle.loads(data)

    def __init__(self, tensor: torch.Tensor) -> None:
        storage = tensor.untyped_storage()
        handle = storage._share_npu_()

        self.handle = handle
        self.dtype = tensor.dtype
        self.shape = tuple(tensor.shape)
        self.stride = tuple(tensor.stride())
        self.storage_offset = int(tensor.storage_offset())
        device_index = tensor.device.index
        self.device_uuid = NPUIPCWrapper._get_device_uuid(device_index)

    @staticmethod
    def _get_device_uuid(device_index: int) -> str:
        """
        Ascend does not support uuid from the get_device_properties.
        Retrieves the VDie ID (Silicon ID) for Ascend device.
        Falls back to PCIe Bus ID if VDie ID is unavailable.
        """
        device_name = torch.npu.get_device_name()

        try:
            # Run the npu-smi command
            cmd = ["npu-smi", "info", "-t", "board", "-i", str(device_index), "-c", "0"]
            result = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode(
                "utf-8"
            )

            # 1. Try to find VDie ID
            # Matches: "VDie ID : XXXXX XXXX..."
            vdie_match = re.search(r"VDie ID\s*:\s*([0-9A-F ]+)", result)
            if vdie_match:
                raw_id = vdie_match.group(1).replace(" ", "")
                if raw_id and not all(c == "0" for c in raw_id):
                    return f"{device_name}-{raw_id}"

            # 2. Fallback to PCIe Bus Info (Best Local ID)
            # Matches: "PCIe Bus Info : 0000:C1:00.0"
            pci_match = re.search(r"PCIe Bus Info\s*:\s*([0-9A-Fa-f:.]+)", result)
            if pci_match:
                return f"{device_name}-{pci_match.group(1)}"

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            raise RuntimeError("Failed to retrieve device UUID from npu-smi.") from e

        # 3. Final Fallback (Unlikely to be unique globally)
        return f"{device_name}-{device_index}"

    @staticmethod
    def _discover_gpu_devices():
        """Discover all available GPU devices and map their UUIDs to
        the physical device ordinals.
        """
        if not torch.npu.is_available():
            return

        num_devices = torch.npu.device_count()
        with NPUIPCWrapper._device_mapping_lock:
            if NPUIPCWrapper._discovered_device_mapping:
                return  # Already discovered

            for i in range(num_devices):
                device_uuid = NPUIPCWrapper._get_device_uuid(i)
                NPUIPCWrapper._discovered_device_mapping[device_uuid] = i

    @staticmethod
    def _get_device_index_from_uuid(device_uuid: str) -> int:
        """Get the physical device ordinal from its UUID."""
        NPUIPCWrapper._discover_gpu_devices()

        with NPUIPCWrapper._device_mapping_lock:
            device_index = NPUIPCWrapper._discovered_device_mapping.get(
                device_uuid, None
            )

        if device_index is None:
            raise RuntimeError(
                f"Device UUID {device_uuid} not found in the discovered devices."
                " Please make sure the process can see all the GPU devices."
            )
        return device_index

    def to_tensor(self):
        """
        Note:
            This function may break if torch npu is not initialized.
            We should call `torch.npu.init()` before using this function.
        """
        device = NPUIPCWrapper._get_device_index_from_uuid(self.device_uuid)
        storage = torch.UntypedStorage._new_shared_npu(device, *self.handle[1:])
        t = torch.empty((), device=f"npu:{device}", dtype=self.dtype)
        t.set_(storage, self.storage_offset, self.shape, self.stride)
        return t


@dataclass(order=True, frozen=True)
class IPCCacheEngineKey:
    """Cache key for the IPC (multiprocess) protocol.

    This key type is sent by the client over ZMQ (serialized via msgspec).

    The client sends token_ids, start, end, and request_id (all required).
    The server computes chunk hashes via TokenHasher and converts to
    ObjectKey for storage operations using ipc_key_to_object_keys().

    The request_id field is for session tracking and is NOT included
    in equality/hash comparisons (two keys with same content but different
    request_ids are considered equal for cache purposes).
    """

    model_name: str
    world_size: int
    worker_id: int | None

    token_ids: tuple[int, ...]  # frozen tuple for hashability
    start: int
    end: int

    # === Session tracking (not part of cache identity) ===
    request_id: str = field(compare=False)

    # Helper function for unit tests only
    @classmethod
    def from_token_ids(
        cls,
        model_name: str,
        world_size: int,
        worker_id: int | None,
        token_ids: list[int],
        start: int = 0,
        end: int = 0,
        request_id: str = "",
    ) -> "IPCCacheEngineKey":
        """Create a key from token ids. Only used by the tests."""
        return cls(
            model_name=model_name,
            world_size=world_size,
            worker_id=worker_id,
            token_ids=tuple(token_ids),
            start=start,
            end=end,
            request_id=request_id,
        )

    def no_worker_id_version(self) -> "IPCCacheEngineKey":
        """Create a copy with worker_id=None for lookup requests."""
        return IPCCacheEngineKey(
            model_name=self.model_name,
            world_size=self.world_size,
            worker_id=None,
            token_ids=self.token_ids,
            start=self.start,
            end=self.end,
            request_id=self.request_id,
        )


# Type exports
KVCache = list[NPUIPCWrapper]


@dataclass
class CustomizedSerdeConfig:
    serializer: Callable[[Any], bytes]
    deserializer: Callable[[bytes], Any]
    code: int


_CUSTOMERIZED_SERIALIZERS = {
    NPUIPCWrapper: CustomizedSerdeConfig(
        serializer=NPUIPCWrapper.Serialize,
        deserializer=NPUIPCWrapper.Deserialize,
        code=1,
    ),
}


def get_customized_encoder(type: Any) -> msgspec.msgpack.Encoder:
    # TODO: `type` is not used here
    def enc_hook(obj: Any) -> Any:
        for supported_type, cfg in _CUSTOMERIZED_SERIALIZERS.items():
            if isinstance(obj, supported_type):
                data = cfg.serializer(obj)
                return msgspec.msgpack.Ext(cfg.code, data)
        raise TypeError(f"Unsupported type for serialization: {type(obj)}")

    return msgspec.msgpack.Encoder(enc_hook=enc_hook)


def get_customized_decoder(type: Any) -> msgspec.msgpack.Decoder:
    def ext_hook(code: int, data: bytes) -> Any:
        for cfg in _CUSTOMERIZED_SERIALIZERS.values():
            if cfg.code == code:
                return cfg.deserializer(data)
        raise TypeError(f"Unsupported ext code for deserialization: {code}")

    return msgspec.msgpack.Decoder(ext_hook=ext_hook, type=type)


@dataclass
class BlockAllocationRecord:
    """A single per-request GPU block allocation delta from vLLM."""

    req_id: str
    new_block_ids: list[int]
    new_token_ids: list[int]


@dataclass
class CBMatchResult:
    """Result of a sub-sequence match from BlendTokenRangeMatcher.

    Attributes:
        old_st: Start position in the originally registered (stored) sequence.
        old_ed: End position in the originally registered (stored) sequence.
        cur_st: Start position in the query sequence where the match was found.
        cur_ed: End position in the query sequence where the match was found.
        hash: Token hash bytes (from registration) used as the storage key.
    """

    old_st: int
    old_ed: int
    cur_st: int
    cur_ed: int
    hash: bytes
