P4: native Ascend910B3 / GLM-5.2 cache runtime
================================================

This is a source candidate, not intranet build/ABI/model acceptance.
Use ``lmcache==0.4.3+ascend.p4`` with ``vllm==0.18.0+ascend.p4``.
The immutable input tag is ``p3-frozen-20261003`` in both repositories.

Retained capabilities
---------------------

Native NPU IPC, CPU KV storage/sharing, P/D, cross-instance cache, DSA dual groups,
same-checkpoint MTP integration, RemoteFill, checkpoint and recovery remain.
The six audited merged native owners retain 663 method contracts; two 310P-only
methods have been explicitly retired. The retirement list is in
``docs/p4-retired-native-owners.json``.

CUDA/HIP/XPU implementations, SGLang, MindSpore, CacheBlend, legacy v0,
the separate GPU multiprocess server, GDS/NIXL/Maru providers and CacheGen/KIVI
serialization have been removed. Legacy configuration slots may remain only
to reject unsupported options; they are not working provider implementations.
Use native ``LMCacheConnectorV1`` in vLLM, never ``lmcache_ascend.*`` imports.
The existing GPUKVFormat enum numbers remain as serialized layout contracts;
their historical names do not enable GPU or SGLang execution.
Pinned common CANN/kvcache-ops materials keep their audited identity; P4's build
and runtime entry points accept only 910B3. Generic material code is not a
declaration of support for other hardware.

Installation
------------

Keep Python 3.11/aarch64, CANN 8.5.1, torch 2.9.0, torch-npu 2.9.0.post2,
transformers 5.2.0 and the approved pinned native materials. Do not upgrade
dependencies implicitly. Install both P4 repositories in every test container.
Do not modify an active P3 baseline container.

.. code-block:: bash

   export ASCEND_HOME_PATH=/usr/local/Ascend/cann-8.5.1
   source "$ASCEND_HOME_PATH/set_env.sh"
   export SOC_VERSION=ascend910b3
   python -B p1_dev.py doctor
   python -B p1_dev.py editable --isolated-env --output /tmp/p4-lmcache-editable-new
   python -B p1_dev.py verify --mode editable

Use a new output directory. The historical filename ``p1_dev.py`` is intentional;
it now checks P4 identity. Rebuild native artifacts and the strict editable link
tree after switching phases. Source-only or stale P3 artifacts are not accepted.

SoC spelling during installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The shell profile uses ``SOC_VERSION=ascend910b3``. The LMCache Python builder
reads CANN's case-sensitive ``Ascend910B3.ini`` and passes
``-DSOC_VERSION=Ascend910B3`` to CMake. The CMake gate accepts case variants
of this one device and normalizes the downstream value to ``Ascend910B3``.
Other devices and empty values still fail; do not remove the hardware guard.

The initial P4 revision rejected the builder's spelling with
``P4 supports only SOC_VERSION=ascend910b3``. Update to the corrected paired
P4 revision and rerun the editable installation above in every affected
container. Changing the environment variable alone cannot fix that revision.
Do not change dependencies or manually remove the failed build directory;
each retry already uses a fresh native build directory. This fix also applies
to ordinary wheel builds, which use the same builder. Passing the SoC gate
does not establish native compilation, ABI or inference acceptance.

Validation
----------

Run ``tools/check_p4_profile.py`` and ``tools/check_npu_native.py`` on the source
host. Run ``tools/p4_runtime_smoke.py --output <new-directory>`` from outside the
checkout in the installed intranet environment. ``--npu`` additionally checks
a small pinned-host/NPU copy on an idle test device. No model is loaded by this
probe. Ordinary wheel/sdist rebuild, P/D, CPU sharing, RemoteFill, checkpoint
recovery and long-running model tests are still required for acceptance.

Only the three explicitly approved op-compile-tool 0.1.0 stdlib metadata errors
may be waived. All other dependency errors must remain blocking.

Recovery
--------

Both P3 tags and earlier phase branches are retained. Recreate an independent
test environment from the paired tag for rollback; do not mix a P3 package
with P4 or erase another developer's local changes.
