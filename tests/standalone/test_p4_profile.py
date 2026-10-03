# SPDX-License-Identifier: Apache-2.0
"""P4 public configuration guard tests, with no hardware import."""

# Standard
from pathlib import Path
import runpy
from types import SimpleNamespace as NS

# Third Party
import pytest

api = NS(
    **runpy.run_path(
        str(Path(__file__).resolve().parents[2] / "lmcache/inference_profile.py")
    )
)


def test_native_defaults_and_cpu_cache_remain_valid() -> None:
    """CPU KV storage is allowed, despite CPU inference being removed."""
    api.validate_config(NS(local_cpu=True, shared_cpu_memory=True))
    for channel in (None, "hccl", "hixl", "hcomm_onesided"):
        api.validate_config(NS(transfer_channel=channel, remote_serde="naive"))
    api.validate_device_name("Ascend910B3")


@pytest.mark.parametrize(
    "option",
    [
        "enable_blending",
        "enable_lazy_memory_allocator",
        "use_gpu_connector_v3",
        "gds_path",
        "nixl_backends",
        "maru_path",
        "runtime_plugin_locations",
        "storage_plugins",
    ],
)
def test_removed_provider_rejected(option: str) -> None:
    """Removed providers fail before allocation or dynamic import."""
    with pytest.raises(ValueError):
        api.validate_config(NS(**{option: True}))


@pytest.mark.parametrize("name", ["Ascend910B2", "Ascend310P3", "cuda", "cpu"])
def test_wrong_hardware_rejected(name: str) -> None:
    """Other hardware must never fall back to a generic provider."""
    with pytest.raises(RuntimeError):
        api.validate_device_name(name)


def test_unsupported_serde_and_channel_rejected() -> None:
    """CacheGen and NIXL are not enabled implicitly."""
    with pytest.raises(ValueError):
        api.validate_config(NS(remote_serde="cachegen"))
    with pytest.raises(ValueError):
        api.validate_config(NS(transfer_channel="nixl"))


def test_310p_native_execution_and_cuda_pointer_paths_removed() -> None:
    """Removed hardware has no public binding or retained connector methods."""
    root = Path(__file__).resolve().parents[2]
    for relative in (
        "ascend/csrc/mem_kernels.h",
        "ascend/csrc/mem_kernels.cpp",
        "ascend/csrc/pybind.cpp",
        "lmcache/v1/npu_connector/npu_connectors.py",
    ):
        source = (root / relative).read_text()
        assert "multi_layer_kv_transfer_310p" not in source
        assert "to_gpu_310p" not in source
        assert "from_gpu_310p" not in source
    assert "device.is_cuda()" not in (root / "ascend/csrc/utils.h").read_text()
