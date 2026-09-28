# SPDX-License-Identifier: Apache-2.0
"""Device-neutral KV transfer contract; no accelerator implementation import."""

import abc
from typing import List, Optional, Union
import torch
from lmcache.v1.memory_management import MemoryObj
from lmcache.v1.device_connector.utils import permute_kv_caches_to_contiguous


class DeviceConnectorInterface(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def to_gpu(self, memory_obj: MemoryObj, start: int, end: int, **kwargs):
        # FIXME (Yihua): We shouldn't put start and end here since
        # it's not the responsibility of the GPUConnector to know
        # the token-sequence-related information.
        """Store the data in the memory object into a GPU buffer.
        Sub-classes should define the format of the kwargs.

        :param MemoryObj memory_obj: The memory object to be copied into GPU.
        :param int start: The starting index of the data in the corresponding
            token sequence.
        :param int end: The ending index of the data in the corresponding
            token sequence.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def from_gpu(self, memory_obj: MemoryObj, start: int, end: int, **kwargs):
        # FIXME (Yihua): We shouldn't put start and end here since
        # it's not the responsibility of the GPUConnector to know
        # the token-sequence-related information.
        """Load the data from a GPU buffer into the memory object.
        Sub-classes should define the format of the kwargs.

        :param MemoryObj memory_obj: The memory object to store the data from
            GPU.
        :param int start: The starting index of the data in the corresponding
            token sequence.
        :param int end: The ending index of the data in the corresponding
            token sequence.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def batched_from_gpu(
        self,
        memory_objs: Union[List[List[MemoryObj]], List[MemoryObj]],
        starts: List[int],
        ends: List[int],
        **kwargs,
    ):
        """
        Batched load the data from a GPU memory into the memory objects.
        Sub-classes should define the format of the kwargs.

        :param Union[List[List[MemoryObj]], List[MemoryObj]] memory_obj:
            The memory objects to store the data from GPU.
        :param List[int] starts: The starting indices of the data in the corresponding
            token sequence.
        :param List[int] ends: The ending indices of the data in the corresponding
            token sequence.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def batched_to_gpu(
        self,
        memory_objs: Union[
            List[List[MemoryObj]], List[MemoryObj], List[int], None
        ] = None,
        starts: Optional[List[int]] = None,
        ends: Optional[List[int]] = None,
        **kwargs,
    ):
        """
        Batched store the data from the memory objects to GPU kv cache.
        Sub-classes should define the format of the kwargs.

        For non-layerwise connectors:
        :param Union[List[List[MemoryObj]], List[MemoryObj]] memory_obj:
            The memory objects to store the data to GPU.
        :param List[int] starts: The starting indices of the data in the corresponding
            token sequence.
        :param List[int] ends: The ending indices of the data in the corresponding
            token sequence.

        For layerwise connectors (generator pattern):
        :param List[int] memory_objs: Actually the starts list
        (positional compatibility)
        :param List[int] starts: Actually the ends list
        (positional compatibility)
        Note: Layerwise connectors receive memory objects
        via generator.send()
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_shape(self, num_tokens: int) -> torch.Size:
        """Get the shape of the data given the number of tokens."""
        raise NotImplementedError

    def initialize_kvcaches_ptr(self, **kwargs):
        """Initialize the kvcaches pointers if not already initialized."""
        if "kvcaches" in kwargs:
            self.kvcaches = kwargs["kvcaches"]
            # Ensure contiguity on every call.  HND tensors from vLLM have a
            # non-contiguous logical view (NHD) that must be permuted back to
            # the physical (HND) shape for correct kernel indexing.
            # permute_kv_caches_to_contiguous is a no-op when already contiguous.
            self.kvcaches = permute_kv_caches_to_contiguous(self.kvcaches)
            # Layerwise store/retrieve passes a per-group list with one entry
            # per layer. Keep the transfer loop aligned with that list length.
            if isinstance(self.kvcaches, list) and self.kvcaches:
                self.num_layers = len(self.kvcaches)

    def supports_dense_sparse_cache_retention(self) -> bool:
        """Return whether dense loads populate complete sparse pointer caches.

        Connectors must return ``True`` only when a dense layerwise retrieve
        fills both the host and device pointer rows passed in its keyword
        arguments without an additional pointer-resolution pass.
        """
        return False
