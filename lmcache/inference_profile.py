# SPDX-License-Identifier: Apache-2.0
"""Dependency-free P4 guards; CPU storage is not a CPU inference backend."""

# Standard
from typing import Any


def validate_device_name(name: str) -> None:
    """Require the paired Ascend910B3 SoC before allocating transfer buffers."""
    if name.lower().replace(" ", "").replace("_", "") != "ascend910b3":
        raise RuntimeError(f"Ascend P4 requires Ascend910B3; detected {name!r}")


def validate_config(config: Any) -> None:
    """Reject retired providers before worker resources or cache mutations."""
    for name in (
        "enable_blending",
        "enable_lazy_memory_allocator",
        "use_gpu_connector_v3",
        "gds_path",
        "cufile_buffer_size",
        "nixl_backends",
        "nixl_buffer_size",
        "nixl_buffer_device",
        "maru_path",
        "runtime_plugin_locations",
        "storage_plugins",
        "remote_storage_plugins",
    ):
        if getattr(config, name, None):
            raise ValueError(f"Ascend P4 does not support {name}")
    if getattr(config, "remote_serde", "naive") != "naive":
        raise ValueError("Ascend P4 supports only remote_serde=naive")
    channel = getattr(config, "transfer_channel", None)
    if channel not in (None, "hccl", "hixl", "hcomm_onesided"):
        raise ValueError(f"Unsupported Ascend transfer_channel: {channel}")
