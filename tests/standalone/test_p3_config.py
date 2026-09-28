# SPDX-License-Identifier: Apache-2.0
"""P3-01 native configuration contracts, without torch/CANN or plugin imports.

Run directly: python -B tests/standalone/test_p3_config.py -v
The real config implementation is used; only environment values are isolated.
"""

from __future__ import annotations

# Standard
import ast
from dataclasses import fields
import importlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# First Party
from lmcache.v1.config import LMCacheEngineConfig  # noqa: E402

# All 23 fields formerly injected by the P2 Ascend package. Eight shared-CPU
# fields already existed in the core schema; their definitions remain unique.
ASCEND_DEFAULTS = {
    "enable_shared_cpu_cache": False,
    "shared_cpu_cache_strict": True,
    "shared_cpu_cache_name": None,
    "shared_cpu_cache_size_gb": None,
    "shared_cpu_cache_numa_policy": "first_touch",
    "shared_cpu_cache_numa_nodes": None,
    "shared_cpu_materialize_index_on_decode_cold": True,
    "shared_cpu_cache_passive_writable": None,
    "p2p_use_npu": False,
    "p2p_npu_buffer_size": 1024**3,
    "p2p_pull_mode": False,
    "p2p_delay_pull": False,
    "p2p_pull_pending_ttl": 360.0,
    "pd_pull_mode": False,
    "pd_delay_pull": False,
    "pd_pull_done_port": None,
    "pd_use_cpu_offload": False,
    "pd_cpu_buffer_size": None,
    "pd_alloc_fail_backoff_ttl": 2.0,
    "pd_pull_pending_ttl": 360.0,
    "pd_pull_backpressure_reserve_pct": 2.0,
    "store_async": False,
    "store_async_max_queue_size": 0,
}


class NativeConfigContracts(unittest.TestCase):
    """Check public configuration behavior and the single-definition contract."""

    def setUp(self) -> None:
        """Remove caller-specific LMCache variables for each host-only case."""
        clean = {k: v for k, v in os.environ.items() if not k.startswith("LMCACHE_")}
        self.enterContext(patch.dict(os.environ, clean, clear=True))

    def test_all_ascend_defaults_exist_without_loading_plugin(self) -> None:
        """Keep every former injected default in the public dataclass."""
        config = LMCacheEngineConfig.from_defaults()
        for name, expected in ASCEND_DEFAULTS.items():
            with self.subTest(field=name):
                self.assertEqual(getattr(config, name), expected)
        self.assertTrue(set(ASCEND_DEFAULTS) <= {f.name for f in fields(config)})
        self.assertIs(config.validate(), config)

    def test_dict_and_json_preserve_ascend_values(self) -> None:
        """Dictionary and JSON readers accept the same transport fields."""
        config = LMCacheEngineConfig.from_dict(
            {
                "p2p_use_npu": "true",
                "p2p_npu_buffer_size": "4096",
                "pd_pull_done_port": "18100,18101",
                "pd_pull_pending_ttl": "12.5",
                "pd_cpu_buffer_size": None,
                "store_async": True,
                "store_async_max_queue_size": "2",
            }
        )
        self.assertTrue(config.p2p_use_npu)
        self.assertEqual(config.p2p_npu_buffer_size, 4096)
        self.assertEqual(config.pd_pull_done_port, [18100, 18101])
        self.assertEqual(config.pd_pull_pending_ttl, 12.5)
        self.assertIsNone(config.pd_cpu_buffer_size)
        restored = LMCacheEngineConfig.from_json(config.to_json())
        self.assertEqual(restored.to_dict(), config.to_dict())

    def test_env_converters_and_nullable_defaults(self) -> None:
        """Environment conversion retains booleans, ports, numbers and None."""
        with patch.dict(
            os.environ,
            {
                "LMCACHE_P2P_USE_NPU": "true",
                "LMCACHE_PD_PULL_DONE_PORT": "18100,18101",
                "LMCACHE_P2P_NPU_BUFFER_SIZE": "2048",
                "LMCACHE_PD_PULL_PENDING_TTL": "30.5",
                "LMCACHE_SHARED_CPU_CACHE_PASSIVE_WRITABLE": "false",
            },
        ):
            config = LMCacheEngineConfig.from_env()
        self.assertTrue(config.p2p_use_npu)
        self.assertEqual(config.pd_pull_done_port, [18100, 18101])
        self.assertEqual(config.p2p_npu_buffer_size, 2048)
        self.assertEqual(config.pd_pull_pending_ttl, 30.5)
        self.assertFalse(config.shared_cpu_cache_passive_writable)
        self.assertIsNone(config.pd_cpu_buffer_size)

    def test_file_loading_uses_early_class_reference(self) -> None:
        """An early imported class accepts fields formerly added by the plugin."""
        early_reference = LMCacheEngineConfig
        with tempfile.TemporaryDirectory(prefix="p3-config-") as directory:
            config_path = Path(directory) / "config.yaml"
            config_path.write_text(
                "p2p_use_npu: true\npd_pull_done_port: [18100, 18101]\n"
                "store_async: true\nstore_async_max_queue_size: 3\n"
                "shared_cpu_cache_numa_nodes: [0, 1]\n",
                encoding="utf-8",
            )
            config = early_reference.from_file(str(config_path))
        self.assertIs(type(config), early_reference)
        self.assertTrue(config.p2p_use_npu)
        self.assertEqual(config.store_async_max_queue_size, 3)
        self.assertEqual(config.pd_pull_done_port, [18100, 18101])
        self.assertEqual(config.shared_cpu_cache_numa_nodes, [0, 1])
        self.assertIs(
            importlib.import_module("lmcache.v1.config").LMCacheEngineConfig,
            early_reference,
        )

    def test_update_env_keeps_canonical_validation_method(self) -> None:
        """The core update method still validates after applying env values."""
        config = LMCacheEngineConfig.from_defaults()
        with patch.dict(
            os.environ,
            {
                "LMCACHE_ENABLE_REMOTE_LMCACHE_STORE": "true",
                "LMCACHE_REMOTE_URL": "mooncakestore://metadata",
                "LMCACHE_PD_ROLE": "sender",
            },
        ):
            self.assertIs(config.update_config_from_env(), config)
        self.assertTrue(config.store_async)
        self.assertTrue(config.use_layerwise)
        self.assertEqual(config.store_async_max_queue_size, 2)
        with patch.dict(os.environ, {"LMCACHE_MIN_RETRIEVE_TOKENS": "-1"}):
            with self.assertRaisesRegex(ValueError, "min_retrieve_tokens"):
                config.update_config_from_env()

    def test_sender_normalization_preserves_direct_store_contract(self) -> None:
        """RemoteFill implies DSA groups, deterministic hash and async store."""
        config = LMCacheEngineConfig.from_defaults(
            enable_remote_lmcache_store=True,
            pd_role="sender",
            remote_url="mooncakestore://metadata",
            chunk_size=1024,
        )
        config.validate()
        for name in (
            "store_async",
            "use_layerwise",
            "dsa_two_groups",
            "enable_sparse_attention",
            "save_unfull_chunk",
        ):
            self.assertTrue(getattr(config, name))
        self.assertEqual(config.store_async_max_queue_size, 2)
        self.assertEqual(config.pre_caching_hash_algorithm, "sha256_cbor")
        for name in (
            "save_only_first_rank",
            "use_ascend_direct",
            "mooncake_page_first_multi_buffer",
            "mooncake_layer_merged_page_objects",
        ):
            self.assertIs(config.get_extra_config_value(name), True)
        self.assertIs(config.get_extra_config_value("save_chunk_meta"), False)

    def test_receiver_normalization_requires_strict_shared_publication(self) -> None:
        """Decoder shared-CPU settings exist before shared-CPU validation."""
        config = LMCacheEngineConfig.from_defaults(
            enable_remote_lmcache_store=True,
            pd_role="receiver",
            remote_url="mooncakestore://metadata",
            shared_cpu_cache_strict=False,
        )
        config.validate()
        self.assertTrue(config.enable_shared_cpu_cache)
        self.assertTrue(config.shared_cpu_cache_strict)
        self.assertFalse(config.store_async)
        self.assertIsNone(config.get_extra_config_value("use_ascend_direct"))

    def test_receiver_without_cpu_cache_fails_before_runtime(self) -> None:
        """The migration must not postpone shared-memory safety checks."""
        for options, error in (
            ({"local_cpu": False}, "local_cpu=true"),
            ({"max_local_cpu_size": 0}, "max_local_cpu_size > 0"),
            ({"shared_cpu_cache_size_gb": 0}, "must be positive"),
        ):
            with self.subTest(options=options):
                config = LMCacheEngineConfig.from_defaults(
                    enable_remote_lmcache_store=True,
                    pd_role="receiver",
                    remote_url="mooncakestore://metadata",
                    **options,
                )
                with self.assertRaisesRegex(ValueError, error):
                    config.validate()

    def test_normalization_is_idempotent_and_does_not_mutate_input_dict(self) -> None:
        """Preserve unrelated extra settings and repeated validation semantics."""
        extra = {"custom_setting": "keep", "save_only_first_rank": False}
        config = LMCacheEngineConfig.from_defaults(
            enable_remote_lmcache_store=True,
            pd_role="sender",
            remote_url="mooncakestore://metadata",
            extra_config=extra,
        )
        config.validate()
        snapshot = config.to_dict()
        config.validate()
        self.assertEqual(config.to_dict(), snapshot)
        self.assertEqual(
            extra, {"custom_setting": "keep", "save_only_first_rank": False}
        )
        self.assertEqual(config.get_extra_config_value("custom_setting"), "keep")

    def test_disabled_remote_fill_preserves_existing_choices(self) -> None:
        """Non-RemoteFill PD/P2P options are not silently normalized."""
        config = LMCacheEngineConfig.from_defaults(
            enable_remote_lmcache_store=False,
            pd_pull_mode=True,
            store_async=True,
            store_async_max_queue_size=7,
            extra_config={"save_chunk_meta": True},
        )
        config.validate()
        self.assertTrue(config.pd_pull_mode)
        self.assertEqual(config.store_async_max_queue_size, 7)
        self.assertFalse(config.use_layerwise)
        self.assertFalse(config.enable_shared_cpu_cache)
        self.assertIs(config.get_extra_config_value("save_chunk_meta"), True)

    def test_direct_hbm_rejects_explicit_metadata_before_normalizing(self) -> None:
        """Do not mask an invalid Group-1 layout by overwriting its setting."""
        config = LMCacheEngineConfig.from_defaults(
            enable_remote_lmcache_store=True,
            pd_role="sender",
            dsa_group1_load_mode="persistent_direct_hbm",
            remote_url="mooncakestore://metadata",
            extra_config={"save_chunk_meta": True},
        )
        with self.assertRaisesRegex(ValueError, "save_chunk_meta=false"):
            config.validate()

    def test_direct_hbm_sender_does_not_require_decoder_slab(self) -> None:
        """Preserve the producer/decoder asymmetry from the approved branch."""
        config = LMCacheEngineConfig.from_defaults(
            enable_remote_lmcache_store=True,
            pd_role="sender",
            dsa_group1_load_mode="persistent_direct_hbm",
            remote_url="mooncakestore://metadata",
        )
        config.validate()
        self.assertFalse(config.enable_dsa_cold_compact_load)
        self.assertFalse(config.enable_shared_cpu_cache)

    def test_existing_remote_fill_bounds_and_scheme_checks_remain(self) -> None:
        """Keep invalid transport, window and timeout inputs fail-closed."""
        for options, error in (
            ({"remote_url": "redis://metadata"}, "remote_url=mooncakestore"),
            ({"remote_fill_window_tokens": 1}, "positive multiple"),
            ({"remote_fill_min_free_ratio": 1}, "remote_fill_min_free_ratio"),
            ({"pin_timeout_sec": 1}, "pin_timeout_sec"),
        ):
            with self.subTest(options=options):
                values = {
                    "enable_remote_lmcache_store": True,
                    "pd_role": "sender",
                    "remote_url": "mooncakestore://metadata",
                    **options,
                }
                config = LMCacheEngineConfig.from_defaults(**values)
                with self.assertRaisesRegex(ValueError, error):
                    config.validate()

    def test_dsa_requires_layerwise_without_remote_fill(self) -> None:
        """Do not relax DSA restrictions for callers outside RemoteFill."""
        config = LMCacheEngineConfig.from_defaults(dsa_two_groups=True)
        with self.assertRaisesRegex(ValueError, "requires use_layerwise=true"):
            config.validate()

    def test_schema_has_unique_keys_and_one_config_class_factory(self) -> None:
        """Source-level ownership check, without accessing private runtime state."""
        source = (ROOT / "lmcache/v1/config.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        schema = next(
            node.value
            for node in tree.body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "_CONFIG_DEFINITIONS"
        )
        keys = [ast.literal_eval(key) for key in schema.keys]
        self.assertEqual(len(keys), len(set(keys)))
        factories = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "create_config_class"
        ]
        self.assertEqual(len(factories), 1)
        plugin = (ROOT / "ascend/lmcache_ascend/__init__.py").read_text(
            encoding="utf-8"
        )
        for retired in ("_patch_config", "create_config_class", "_CONFIG_DEFINITIONS"):
            self.assertNotIn(retired, plugin)

    def test_fresh_process_config_import_does_not_load_inference_packages(self) -> None:
        """Config-only tools must not initialize torch, vLLM or the old plugin."""
        script = (
            "import sys; from lmcache.v1.config import LMCacheEngineConfig; "
            "c = LMCacheEngineConfig.from_defaults(p2p_use_npu=True); "
            "assert c.p2p_use_npu; "
            "assert not any(name.split('.')[0] in "
            "{'torch', 'torch_npu', 'vllm', 'lmcache_ascend'} "
            "for name in sys.modules)"
        )
        done = subprocess.run(
            [sys.executable, "-B", "-c", script],
            cwd=ROOT,
            env={**os.environ, "PYTHONPATH": str(ROOT)},
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)


if __name__ == "__main__":
    unittest.main()
