# SPDX-License-Identifier: Apache-2.0
"""Intranet-only installed P4 import/spawn and optional small NPU allocation gate.

No package installation, model loading, network service or serving-process changes.
Only this tool's own timed-out child processes may be terminated.
Run from outside source checkouts after installing both paired distributions.
"""

from __future__ import annotations

# Standard
import argparse
from importlib import import_module, metadata
import json
import multiprocessing
from pathlib import Path
import subprocess
import sys
import traceback

ORDERS = (
    (
        "lmcache.v1.config",
        "lmcache.v1.cache_engine",
        "vllm.platforms",
        "lmcache.integration.vllm.vllm_v1_adapter",
    ),
    (
        "vllm.platforms",
        "lmcache.integration.vllm.lmcache_connector_v1",
        "lmcache.v1.cache_engine",
    ),
    (
        "lmcache.v1.memory_management",
        "lmcache.v1.npu_connector",
        "lmcache.integration.vllm.vllm_v1_adapter",
    ),
)


def inspect_runtime(order: int, npu: bool = False) -> dict:
    """Import native owners and assert identities, without initializing a model."""
    import torch

    # Check the callable objects themselves, not only function names or strings.
    cuda_api = {
        name: getattr(torch.cuda, name)
        for name in ("Stream", "Event", "set_device", "is_available")
    }
    constructors = (torch.tensor, torch.empty, torch.Tensor.to, torch.Tensor.cuda)
    for module in ORDERS[order]:
        import_module(module)
    assert all(
        getattr(torch.cuda, name) is value for name, value in cuda_api.items()
    ), "CUDA API was globally patched"
    assert constructors == (
        torch.tensor,
        torch.empty,
        torch.Tensor.to,
        torch.Tensor.cuda,
    ), "Tensor constructors were globally patched"
    forbidden = [
        name
        for name in sys.modules
        if name.startswith(
            ("lmcache_ascend", "vllm_ascend", "torch_npu.contrib.transfer_to_npu")
        )
    ]
    assert not forbidden, f"Retired runtime imports: {forbidden}"
    expected = {"vllm": "0.18.0+ascend.p5p6rc1", "lmcache": "0.4.3+ascend.p5p6rc1"}
    for name, version in expected.items():
        assert metadata.version(name) == version, f"Wrong paired distribution: {name}"
    from lmcache import c_ops
    from lmcache.v1.cache_engine import LMCacheEngine
    from lmcache.v1.device_connector import DeviceConnectorInterface
    from lmcache.v1.npu_connector.npu_connectors import (
        VLLMPagedMemLayerwiseNPUConnector,
    )
    from lmcache.integration.vllm.vllm_v1_adapter import LMCacheConnectorV1Impl
    from vllm.distributed.kv_transfer.kv_connector.v1.lmcache_connector import (
        LMCacheConnectorV1,
    )

    assert LMCacheEngine.__module__ == "lmcache.v1.cache_engine"
    assert (
        LMCacheConnectorV1Impl.__module__ == "lmcache.integration.vllm.vllm_v1_adapter"
    )
    assert VLLMPagedMemLayerwiseNPUConnector.__bases__ == (DeviceConnectorInterface,)
    assert c_ops.__name__ == "lmcache.c_ops"
    assert LMCacheConnectorV1.supports_dsa_index_lmcache
    for member in (
        "seal_sparse_destination_layout",
        "capture_live_source_event_handoff",
        "remote_fill_requires_paired_restart",
        "handle_preemptions",
    ):
        assert callable(getattr(LMCacheConnectorV1, member))
    for index, name in enumerate(
        (
            "NB_NL_TWO_BS_NH_HS",
            "NL_X_TWO_NB_BS_NH_HS",
            "NL_X_NB_TWO_BS_NH_HS",
            "NL_X_NB_BS_HS",
            "TWO_X_NL_X_NBBS_NH_HS",
            "NL_X_NBBS_ONE_HS",
            "NL_X_TWO_NB_NH_BS_HS",
            "NL_X_NB_TWO_NH_BS_HS",
        )
    ):
        assert int(getattr(c_ops.GPUKVFormat, name)) == index
    if npu:
        # Only explicitly selected in an isolated test environment/device.
        import ctypes
        import torch_npu  # noqa: F401

        assert torch.npu.is_available()
        pointer = c_ops.alloc_pinned_ptr(4096, 0)
        try:
            assert c_ops.get_device_ptr(pointer, 4096)
            host = torch.frombuffer(
                (ctypes.c_uint8 * 4096).from_address(pointer), dtype=torch.uint8
            )
            host.fill_(7)
            device = host.to("npu")
            torch.npu.synchronize()
            assert torch.equal(device.cpu(), host)
            del device, host
        finally:
            torch.npu.synchronize()
            c_ops.free_pinned_ptr(pointer)
    return {
        "order": order,
        "native_extension": c_ops.__file__,
        "packages": expected,
        "npu_allocation_tested": npu,
        "passed": True,
    }


def spawn_child(connection) -> None:
    """Return a bounded spawned-process result through a pipe."""
    try:
        connection.send(inspect_runtime(0))
    except Exception:
        connection.send({"passed": False, "traceback": traceback.format_exc()})
    finally:
        connection.close()


def main() -> int:
    """Write a fresh smoke report; failed subprocesses remain failures."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--npu",
        action="store_true",
        help="explicitly test 4 KiB registered host/NPU copy",
    )
    parser.add_argument("--child-order", type=int, choices=range(len(ORDERS)))
    args = parser.parse_args()
    if args.child_order is not None:
        print(json.dumps(inspect_runtime(args.child_order, args.npu)))
        return 0
    if args.output is None:
        parser.error("--output is required")
    args.output.mkdir(parents=True, exist_ok=False)
    results = []
    for order in range(len(ORDERS)):
        cmd = [
            sys.executable,
            "-B",
            str(Path(__file__).resolve()),
            "--child-order",
            str(order),
        ]
        if args.npu:
            cmd.append("--npu")
        try:
            process = subprocess.run(
                cmd,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=120,
            )
            output, passed = process.stdout, process.returncode == 0
        except subprocess.TimeoutExpired as exc:
            output, passed = f"Timeout: {exc}", False
        (args.output / f"import-order-{order}.log").write_text(output)
        results.append({"test": f"import-order-{order}", "passed": passed})
    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe(duplex=False)
    process = context.Process(target=spawn_child, args=(child,))
    process.start()
    child.close()
    spawned = {"passed": False, "error": "spawn timed out"}
    if parent.poll(120):
        try:
            spawned = parent.recv()
        except EOFError:
            spawned = {"passed": False, "error": "spawn exited without a report"}
    process.join(timeout=5)
    if process.is_alive():
        process.terminate()  # Only our own timed-out child, never a serving worker.
        process.join(timeout=5)
    parent.close()
    spawned["passed"] = spawned["passed"] and process.exitcode == 0
    results.append({"test": "spawn-import", **spawned})
    report = {
        "scope": "installed_import_and_optional_small_copy_not_model_acceptance",
        "checks": results,
        "passed": all(result["passed"] for result in results),
    }
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
