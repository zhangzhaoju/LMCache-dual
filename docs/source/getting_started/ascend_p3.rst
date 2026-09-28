P3 native Ascend integration
============================

The P3 source implementation includes the complete retained P2 input
``cfe8a1754db743d41c8bb63f8d02ad7c3051948c``. Configuration, engine, adapter,
NPU connector, memory, IPC and transport now have canonical LMCache owners.
Source delivery is not native-build or inference acceptance.

Native ownership
----------------

* ``lmcache.v1.config`` defines all 23 former plugin fields once.
* ``lmcache.v1.cache_engine.LMCacheEngine`` and
  ``lmcache.integration.vllm.vllm_v1_adapter.LMCacheConnectorV1Impl``
  incorporate the effective Ascend methods. Explicit ``_common_*`` delegation
  retains shared checkpoint, key/group, async-store and cleanup behavior.
* ``lmcache.v1.device_connector.DeviceConnectorInterface`` is the neutral
  transfer contract. Native NPU classes implement it directly, not through
  GPU connector inheritance. Existing transfer method and layout-tag names
  remain unchanged for protocol compatibility.
* ``lmcache.c_ops`` owns Ascend kernels and registered host memory. HCCL/HIXL
  extensions and libraries are installed alongside it in ``lmcache``.
* Storage factories, PD/P2P, token hashing, lookup normalization, NUMA discovery,
  RPC naming and ``NPUIPCWrapper`` no longer require import-time patches.

The original plugin and GPU connector sources are reference-only under
``ascend/legacy-p3`` and excluded from distributions. There is no importable
``lmcache_ascend`` compatibility shell. Importing the native runtime does not
use ``transfer_to_npu`` or replace modules in ``sys.modules``.

Build and development
---------------------

Pair ``lmcache==0.4.3+ascend.p3`` with ``vllm==0.18.0+ascend.p3`` from the
same delivery. The historical helper filename remains::

   python -B p1_dev.py doctor --output /path/to/new-doctor.json
   python -B p1_dev.py editable --isolated-env --output /path/to/new-editable
   python -B p1_dev.py verify --mode editable --output /path/to/new-paths.json

Use a dedicated prepared environment, not the retained P2 service environment.
The isolation flag does not create an environment or waive conflicting
distributions. First install compiles native artifacts. Restart processes
after Python edits; reinstall after new/moved files, native code, dependencies
or resources change. Preserve the source, strict link tree and retained native
build directory. Ordinary wheels and independent sdist rebuilds remain
required acceptance artifacts.

Run installed checks outside source checkouts with no source PYTHONPATH::

   python -B /path/to/LMCache/tools/p3_runtime_smoke.py --output /new/report

This checks import orders, spawn, native identities and absence of global
CUDA API/constructor replacement. Optional ``--npu`` tests a small registered
host-memory copy on an explicitly selected idle test NPU, not model inference.

Serving configuration migration
-------------------------------

The recommended vLLM entry is the built-in ``LMCacheConnectorV1``; remove the
old ``kv_connector_module_path`` pointing at the retired package. A custom
loader can instead select ``LMCacheConnectorV1Dynamic`` from
``lmcache.integration.vllm.lmcache_connector_v1``. Keep engine IDs, roles,
transport, TP/DP, DSA/MTP and cache settings unchanged.

Validation boundary
-------------------

The workspace ``design/p3/intranet-validation.md`` provides exact paired
build/install commands and the joint P2/P3 matrix. Preserve CPU KV offload,
cross-instance cache, destination sealing/first prepared load, checkpoint,
RemoteFill cancellation/timeouts and paired restart. Old PD/P2P layerwise
restrictions are unchanged.

Host tests and normalized method comparisons do not establish ABI, IPC/NPU,
GLM-5.2 2P2D or performance correctness. P4 broad device/model pruning remains
separate. The previously unimplemented Ascend multiprocess GPU cache server
and non-target CacheBlend models are not new supported entry points. Keep
P2/P3 environments, reports and cache namespaces separate.
