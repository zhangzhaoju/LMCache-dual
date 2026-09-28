P3 native Ascend integration
============================

The ``p3`` branch includes the complete P2 input
``cfe8a1754db743d41c8bb63f8d02ad7c3051948c``. The retained ``p2``, ``p1`` and
``main`` branches are unchanged. P2/P3 runtime validation is planned together
in the prepared intranet environment; no phase is accepted by branch creation.

P3-01: configuration ownership
------------------------------

``lmcache.v1.config.LMCacheEngineConfig`` is created once with all 23 Ascend
fields previously installed by the plugin (eight existing shared-CPU fields
and fifteen transport/asynchronous-store fields). RemoteFill normalization runs
before validation, preserving sender async store, receiver strict shared-CPU
publication, two-group DSA and direct-HBM metadata restrictions. No plugin
import is needed to parse or validate these settings::

   from lmcache.v1.config import LMCacheEngineConfig

   config = LMCacheEngineConfig.from_defaults(
       enable_remote_lmcache_store=True,
       pd_role="sender",
       remote_url="mooncakestore://metadata",
   )
   config.validate()
   assert config.store_async_max_queue_size == 2

The plugin no longer regenerates the config class or repairs already imported
references. The canonical ``update_config_from_env()`` retains validation;
factory readers retain their existing parsing API, so callers still invoke
``validate()`` as appropriate. No cache key, payload, transport protocol or
recovery algorithm changes in this batch.

Packaging and development
-------------------------

Pair ``lmcache==0.4.3+ascend.p3`` with ``vllm==0.18.0+ascend.p3`` from the same
delivery. The existing ``p1_dev.py`` interfaces remain available::

   python -B p1_dev.py editable --isolated-env --output /path/to/new-report
   python -B p1_dev.py verify --mode editable --output /path/to/new-paths.json

Use a dedicated prepared environment, not the retained P2 runtime. The flag
does not create isolation or bypass conflicting-version checks. First install
compiles native artifacts; existing Python edits require process restart,
while new files or native/dependency/resource changes require reinstallation.
Keep the source checkout and strict editable link/native directories in place.
Run installed-package validation outside the source checkout. Detailed paired
commands and manifest are in the workspace ``design/p3/`` directory.

Remaining work and validation
--------------------------------

P3-01 is **not** full LMCache native integration. Engine, NPU connector,
extension/IPC/transport ownership and remaining runtime/install patches still
await migration. ``lmcache_ascend`` remains an internal package in this batch;
do not import it merely to configure LMCache, or claim import-order independence
for the complete runtime yet. Old PD/P2P layerwise restrictions remain.

Configuration and packaging host tests do not compile or install native code.
ABI, NPU, CPU KV offload, cross-instance cache, 2P2D, checkpoint/RemoteFill and
recovery acceptance remains pending. P4 pruning has not started. Keep paired
P2/P3 artifacts, input/config identities, reports and cache namespaces separate
within the unified validation campaign.
