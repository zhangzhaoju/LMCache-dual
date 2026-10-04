# SPDX-License-Identifier: Apache-2.0
"""Host regression for the public non-layerwise KV save boundary.

Execute the production wait_for_save and its implementation, with NumPy masks
and backend/fence doubles. No cache engine, device, tensors or service is loaded.
"""

# Standard
import ast
from pathlib import Path
from types import SimpleNamespace as NS
from typing import Any
from unittest.mock import Mock

# Third Party
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]


def adapter(request: NS, role: str = "kv_both") -> tuple[Any, dict[str, Mock]]:
    """Keep complete public save control flow; stub backend and fence boundaries."""
    path = ROOT / "lmcache/integration/vllm/vllm_v1_adapter.py"
    owner = next(
        node
        for node in ast.parse(path.read_text()).body
        if isinstance(node, ast.ClassDef) and node.name == "LMCacheConnectorV1Impl"
    )
    owner.body = [
        node
        for node in owner.body
        if getattr(node, "name", None) in {"wait_for_save", "_wait_for_save_impl"}
    ]
    namespace = {
        "_lmcache_nvtx_annotate": lambda method: method,
        "LMCacheConnectorMetadata": NS,
        "torch": NS(ones=np.ones, bool=np.bool_),
        "get_pp_group": lambda: NS(is_last_rank=True),
        "logger": Mock(),
    }
    future = ast.ImportFrom(
        module="__future__", names=[ast.alias(name="annotations")], level=0
    )
    module = ast.fix_missing_locations(
        ast.Module(body=[future, owner], type_ignores=[])
    )
    exec(compile(module, str(path), "exec"), namespace)
    result = namespace[owner.name]()
    observers = {
        name: Mock(name=name)
        for name in (
            "unpin",
            "mark_ready",
            "group_completed",
            "committed",
            "finish",
            "complete",
            "abort",
            "store",
        )
    }
    # Private production dependencies are replaced only to isolate this public
    # method's save contract from cache engines, streams and request coordinators.
    result.__dict__.update(
        _parent=NS(_get_connector_metadata=lambda: NS(requests=[request])),
        kv_role=role,
        use_layerwise=False,
        kv_caches={"layer": object()},
        lmcache_engine=NS(store=observers["store"]),
        _lmcache_chunk_size=4,
        _maybe_lookup_unpin_for_request=observers["unpin"],
        _mark_initial_sparse_release_ready=observers["mark_ready"],
        _effective_skip_leading_tokens=lambda _, spec: spec.skip_leading_tokens,
        _prepare_direct_store_inputs=lambda _, slots, __: (slots, {}),
        _record_decode_window_save_group_completed=observers["group_completed"],
        _is_decode_window_save_request=lambda _: False,
        _mark_prefill_committed=observers["committed"],
        _handle_save_request_error=lambda *_: False,
        _finish_save_batch=observers["finish"],
        _complete_worker_save_step=observers["complete"],
        _abort_save_step=observers["abort"],
    )
    return result, observers


def save_request(tokens: int, last: bool, disaggregated: bool, skip: int = 0) -> NS:
    """Describe a local or P/D request without model- or device-specific state."""
    return NS(
        req_id="save-fixture",
        token_ids=list(range(tokens)),
        slot_mapping=[np.arange(tokens)],
        is_sparse_decode=False,
        is_last_prefill=last,
        disagg_spec=NS(is_last_prefill=False, num_transferred_tokens=0)
        if disaggregated
        else None,
        request_configs={},
        save_spec=NS(can_save=True, skip_leading_tokens=skip),
    )


@pytest.mark.parametrize("tokens", [3, 4, 6, 8])
@pytest.mark.parametrize("last", [False, True])
@pytest.mark.parametrize("disaggregated", [False, True])
def test_final_prefill_keeps_tail_partial_prefill_aligns(
    tokens: int, last: bool, disaggregated: bool
) -> None:
    """Only nonfinal prefill may drop an incomplete chunk before store."""
    request = save_request(tokens, last, disaggregated)
    runner, observers = adapter(request)
    runner.wait_for_save()
    saved = tokens if last else tokens // 4 * 4
    observers["store"].assert_called_once()
    call = observers["store"].call_args
    assert call.args[0] == list(range(saved))
    np.testing.assert_array_equal(call.kwargs["slot_mapping"], np.arange(saved))
    np.testing.assert_array_equal(call.kwargs["mask"], np.ones(saved, dtype=np.bool_))
    observers["committed"].assert_called_once_with(request, saved)
    assert request.save_spec.skip_leading_tokens == saved
    if disaggregated:
        assert request.disagg_spec.is_last_prefill is last
        assert request.disagg_spec.num_transferred_tokens == saved
    observers["finish"].assert_called_once()
    observers["complete"].assert_called_once()
    observers["abort"].assert_not_called()


@pytest.mark.parametrize("last", [False, True])
def test_cached_prefix_mask_and_commit_length_remain_consistent(last: bool) -> None:
    """Prefix alignment must not remove the final prompt tail."""
    request = save_request(10, last, True, skip=5)
    runner, observers = adapter(request)
    runner.wait_for_save()
    saved = 10 if last else 8
    call = observers["store"].call_args
    assert call.kwargs["offset"] == 4
    assert call.args[0] == list(range(saved))
    np.testing.assert_array_equal(call.kwargs["mask"], np.arange(saved) >= 4)
    assert request.disagg_spec.num_transferred_tokens == saved


def test_consumer_does_not_store() -> None:
    """The role guard still unpins requests without entering the save path."""
    request = save_request(6, True, True)
    runner, observers = adapter(request, "kv_consumer")
    runner.wait_for_save()
    observers["unpin"].assert_called_once_with(request)
    observers["store"].assert_not_called()
    assert request.save_spec.skip_leading_tokens == 0
