Native repository layout and installation
=========================================

P5/P6 derive from immutable ``native-layout-frozen-20261005``, which removed
the repository-root ``ascend/`` donor tree. They do not change inference algorithms, cache
protocols or native ABI names. The supported profile remains Ascend910B3 and
GLM-5.2 native text generation, with DSA dual groups, MTP, CPU KV storage/sharing,
P/D, RemoteFill, checkpoint and recovery. Runtime C8 remains disabled for acceptance.

Directory ownership
-------------------

``lmcache/`` is the only product Python package. Native host allocators and NPU
bindings share ``csrc/``; the root ``CMakeLists.txt`` includes
``cmake/npu_extensions.cmake``. Pinned kvcache-ops lives in
``third_party/kvcache-ops``. Tests, tools and docs use the root directories.

Both colliding test modules are retained. NPU variants use ``*_npu.py`` in the
same functional test directory; ``utils_npu.py`` extends common test helpers.
The synthetic ``lmcache_tests`` package and import-time connector monkeypatch
are removed. Root fixtures remain authoritative. Moving tests is not evidence
that the entire historical test suite supports this profile or passes on NPU.
Two wrappers for the multiprocess server already removed/excluded in P4 are
preserved byte-for-byte as ``.py.txt`` provenance records under
``docs/design/retired-tests/``. They are not newly skipped active tests.

``lmcache.c_ops``, ``libcache_kernels.so``, HIXL/HCOMM libraries and host storage
extensions keep their names. There is no installable ``lmcache_ascend`` package.
File copyright notices are retained; identical licenses are consolidated in
the root ``LICENSE``. The complete migration map, test names and frozen source
fingerprints are recorded in ``docs/design/layout-migration.json``.
Prior checkpoint/RemoteFill operational notes remain under ``docs/design/``
for provenance; their historical installation paths are not current instructions.

Install in a dedicated intranet environment
------------------------------------------------

Use a new checkout in each dedicated test container. Do not change an active
baseline environment. Install ``lmcache==0.4.3+ascend.p5p6rc1`` together with
``vllm==0.18.0+ascend.p5p6rc1``; rebuild both native extensions and strict editable
link trees. The historical command name ``p1_dev.py`` remains supported.

Keep Python 3.11/aarch64, CANN 8.5.1, torch 2.9.0, torch-npu 2.9.0.post2 and
transformers 5.2.0. No automatic dependency upgrades or build-time downloads
are allowed. Fetching the pinned submodule through an approved proxy is an
explicit preparation step, separate from building.

Run from the LMCache checkout:

.. code-block:: bash

   set -euo pipefail
   git submodule update --init -- third_party/kvcache-ops
   python -B p1_dev.py materials --from-submodule third_party/kvcache-ops
   python -B tools/check_native_layout.py
   export ASCEND_HOME_PATH=/usr/local/Ascend/cann-8.5.1
   source "$ASCEND_HOME_PATH/set_env.sh"
   export SOC_VERSION=ascend910b3
   python -B p1_dev.py doctor
   LAYOUT_REPORT=$(mktemp -d /tmp/lmcache-layout.XXXXXXXX)
   python -B p1_dev.py editable --isolated-env --output "$LAYOUT_REPORT/editable"
   python -B p1_dev.py verify --mode editable

The pinned kvcache-ops commit is
``9f18d2339bc58a43429f7d5bdaef1628c820eff5``. An approved local submodule checkout
can also be supplied to ``materials --from-submodule``. Material provenance is
now written to root ``submodule-materials.json``; an sdist must contain both
the manifest and actual payloads. The script refuses changed material trees.

Use ``p1_dev.py build --output <new-directory>`` for a regular wheel. The SoC
gate still normalizes only case variants of 910B3 to CANN's ``Ascend910B3``;
other devices remain rejected. ``--isolated-env`` does not bypass old package
conflicts. Start with a clean dedicated environment, not an old P4 installation.

Changing an old checkout in place can leave ignored donor build/material files.
The layout gate rejects any remaining root ``ascend/``, including links. Prefer
a new checkout; do not erase the old tree with recursive clean commands.

Validation and rollback
-----------------------

``tools/check_native_layout.py --source-only`` verifies source structure and
byte-identical frozen runtime/native implementations without compiler probes.
It reports absent submodule payloads but is not a build-material approval.
After registering real materials, run it without ``--source-only`` and run
``p1_dev.py doctor`` for dependency/material checks.

``tools/run_layout_host_checks.py --list`` shows the explicit host subset and
deferred tensor cases. Run without ``--list`` for host validation with sibling
``vllm/`` and ``LMCache/`` checkouts. No framework installation or NPU is used.
Full tensor/device tests remain intranet work. GitHub Actions uses the paired
branch; private peer repositories require administrator-configured read access.

Verify regular wheel installation, sdist unpack/rebuild, editable native paths
and the full 2P2D service. From outside the checkout, run the installed runtime
probe via ``tools/p4_runtime_smoke.py --output <new-directory>``; ``--npu`` must
be limited to an idle test device. vLLM's proxy example is now under root
``examples/disaggregated_prefill_v1/``. Keep validated serving parameters and
both TP8/DP2 and TP4/DP4 regression requirements unchanged.

Only the three previously approved op-compile-tool 0.1.0 standard-library
metadata errors may be waived. All other dependency errors remain blocking.
Source/host success does not establish CANN compilation, ABI or model acceptance.
Rollback requires both repositories and installations from the frozen native-layout
pair in an independent environment, never mixed candidate/layout1 packages.
The final P6 pair contains all P5 preparation and receives one combined intranet
qualification campaign. Source checks do not authorize production cutover.
