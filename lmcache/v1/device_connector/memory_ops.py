# SPDX-License-Identifier: Apache-2.0
"""Async tensor copies for native registered host allocators.

Host buffers are registered by lmcache.c_ops at allocation time. The caller
retains both buffers until its current-stream completion fence fires. CUDA
lazy-registration allocators are not an Ascend allocation path.
"""

# Third Party
import torch

# First Party
from lmcache.v1.memory_management import MemoryObj


def lmcache_memcpy_async_h2d(memory_obj: MemoryObj, gpu_buffer: torch.Tensor) -> None:
    """Copy registered host data on the current device stream, without waiting.

    Raises:
        AssertionError: If the memory object has no tensor or sizes differ.
    """
    assert memory_obj.tensor is not None
    assert memory_obj.tensor.numel() == gpu_buffer.numel()
    gpu_buffer.copy_(memory_obj.tensor, non_blocking=True)


def lmcache_memcpy_async_d2h(gpu_buffer: torch.Tensor, memory_obj: MemoryObj) -> None:
    """Copy device data into registered host memory without synchronizing.

    Raises:
        AssertionError: If the memory object has no tensor or sizes differ.
    """
    assert memory_obj.tensor is not None
    assert memory_obj.tensor.numel() == gpu_buffer.numel()
    memory_obj.tensor.copy_(gpu_buffer, non_blocking=True)
