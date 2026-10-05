# AGENTS.md

## Standard packaging entrypoints (2026-10-05)

The user explicitly requires baseline-compatible `pip install -e .`,
`python setup.py bdist_wheel` and `python setup.py sdist` on current `p6`.
Keep the build implementation in root `setup.py`; do not reintroduce
`p1_build.py`, `p1_dev.py` or another required install wrapper. Preserve the
native build flags, artifacts, pinned materials and runtime implementations.
Editable defaults to strict mode. Prepared intranet installs use
`--no-build-isolation --no-deps --no-index` to preserve the foundation.
Frozen refs remain immutable. This supersedes historical helper instructions.

## Current fork: P5 and P6 joint qualification (2026-10-05)

The user authorized freezing native-layout and preparing P5/P6 together.
Work on p5, then p6 inheriting all p5 changes. Keep native-layout-frozen-20261005
and earlier refs immutable. Change release/validation/operations tooling only;
preserve frozen runtime, native implementations, ABI and the 910B3/GLM-5.2 scope.
Use one final intranet functionality/performance campaign on the p6 pair.
Do not claim qualification, switch live services, or retire original checkouts
before evidence and recovery gates pass. No native builds on this source host.
This supersedes earlier working-branch instructions below.

Current installation/deployment instructions are in
`docs/source/getting_started/baseline_validation.rst`. Keep the native-layout
command interface and validated serving arguments. Paired strict editable
remains valid for this baseline comparison; wheel/image release evidence is
a separate requirement. Historical phase notes below are provenance only.

## Current fork: native repository layout (2026-10-04)

Work on `refactor/native-layout` from immutable `p4-frozen-20261004`.
The user approved removing the repository-root `ascend/` donor tree. Integrate
native sources into `csrc/`, `cmake/`, `third_party/`, and the root tests/tools.
Preserve native Python owners, algorithms, ABI names, pinned materials and the
P4 910B3/GLM-5.2 scope. Keep both colliding test contracts with explicit names;
do not overwrite one suite with another. Frozen P4 and earlier refs must not
change. This overrides historical branch/plugin instructions below. Native
builds and 2P2D acceptance remain in the intranet, not this source workstation.

Guidelines for AI coding agents (Copilot, Cursor, Claude Code, etc.) working in this repository.

## Current fork: P4 profile pruning (2026-10-03)

The user authorized freezing P3 and implementing P4 on `p4`. Preserve both
`p3-frozen-20261003` tags and earlier phase branches. Keep only native Ascend/vLLM
integration and the GLM-5.2 DSA/MTP cache lifecycle, including CPU KV storage,
P/D, RemoteFill, checkpoint and recovery. Remove other vendors, legacy plugins,
SGLang/MindSpore and CacheBlend. LoRA/pooling removal is explicitly approved.
These instructions supersede the P3/P2 branch restrictions below. Do not build
native artifacts, install torch/CANN or touch intranet services on this host.

## Current fork: P3 native Ascend integration

On 2026-09-28 the user authorized starting P3 from the complete P2 code and
validating P2/P3 together in the intranet. Work on `p3`; retain `p2` at
`cfe8a1754db743d41c8bb63f8d02ad7c3051948c`, and keep `p1`/`main` unchanged.
P3 native owners now include configuration, method-merged engine/adapter,
DeviceConnectorInterface, NPU connectors, IPC, storage/transport and lmcache.c_ops.
The original plugin and GPU connector are reference archives under
ascend/legacy-p3, excluded from distributions. Do not restore import patches or
the process-wide transfer_to_npu shim. P4 bulk pruning remains separate.
Source/host checks do not establish P3 build, ABI or runtime acceptance.

The user authorized preserving P1 and starting vLLM P2 on 2026-09-27. Retain
`p1` and `main` at the saved P1 input. This overrides the upstream
`dev` branch and CUDA setup instructions below. LMCache runtime native integration
belongs to P3; P2 updates paired development tooling and imports of vLLM's
shared diagnostic, event-handoff and Mooncake contracts at their native owners.

P1/baseline NPU retesting and known defect repairs are deferred by the user.
Use available static and host checks on this source workstation; do not install
torch/CANN or build native artifacts. NPU/ABI validation remains pending for
the prepared intranet environment, and P1 acceptance remains incomplete.

## Project Overview

This fork provides native Ascend910B3 KV cache management for GLM-5.2 with
vLLM, CPU KV storage/sharing, P/D, RemoteFill, checkpoint and recovery.
SGLang, MindSpore, CUDA/HIP and the old plugin are not supported products.

## Repository

The current work branch is `p6`, inheriting `p5` and the frozen native-layout
pair. Preserve all frozen refs. Do not follow the old upstream `dev` workflow
for changes in this fork.

## Python Environment

Reuse the intranet Python 3.11.14/aarch64 and pinned CANN 8.5.1,
torch 2.9.0+cpu, torch-npu 2.9.0.post2 environment. Do not install torch,
create a Python 3.12 serving environment or build native artifacts here.
Use available host tooling for static/host checks on this workstation.

## Build & Install

Follow the baseline guide in dedicated intranet containers. Initialize pinned Git
submodules, then use `python -m pip install -e . --no-build-isolation --no-deps --no-index`
in each repo. Root setup.py validates/registers materials during native builds/sdist;
it never downloads them. Use `python setup.py bdist_wheel` / `python setup.py sdist`
for artifacts and `tools/check_native_layout.py --installed editable` (or `wheel`)
for read-only checks. Reinstall both after a phase/version change; do not switch a
live editable checkout. CUDA/HIP and source-only installs are not alternatives.

## Testing

### Running Tests

```bash
# Run the explicit native-layout host subset
python -B tools/run_layout_host_checks.py --list
python -B tools/run_layout_host_checks.py

# Run a single test file
pytest -xvs tests/v1/test_cache_engine.py

# Run a single test
pytest -xvs tests/v1/test_cache_engine.py::test_function_name
```

Use the prepared test dependencies without implicit upgrades. Device/tensor
tests remain intranet work; the historical full suite is not a supported-profile matrix.

Pytest marker: `@pytest.mark.no_shared_allocator` disables the shared-allocator monkeypatch for a test.

### Testing Practices

- Write tests against the **public interface and docstring contract**, not the implementation. Test as if you don't know the internals — verify that behavior matches what the docstring describes.
- Avoid accessing private members in tests unless strongly needed.
- All new features and bug fixes should include corresponding tests.
- Ensure existing tests still pass before submitting changes.

## Linting & Code Quality

```bash
# Run all checks (mirrors CI exactly)
pre-commit run --all-files

# Individual tools
ruff check .              # Lint (E, F, B, SLF rules)
ruff format .             # Format (line-length 88)
isort .                   # Import sorting (black profile, from_first=true)
mypy --config-file=pyproject.toml   # Type checking
codespell --toml pyproject.toml     # Spell checking
```

C++ files use clang-format (Google style, 80-col). Rust code in `rust/` uses `cargo fmt` and `cargo clippy`.

All Python files require an `# SPDX-License-Identifier: Apache-2.0` header as the first line.

### Import Ordering

Imports must follow this section-heading convention:

```python
# Standard
import os

# Third Party
import torch

# First Party
from lmcache.v1.config import LMCacheEngineConfig

# Local
from .utils import helper
```

### SLF (Private Member Access)

SLF lint rules are currently enforced by CI only in `lmcache/v1/multiprocess/` and `lmcache/v1/distributed/`. However, **all new code should follow SLF discipline regardless of location** — never access private members (prefixed with `_`) of other classes. Treat this as a project-wide coding standard for any new or modified code.

## Coding Conventions

### Type Hints

All functions and methods must have type hints for their arguments and return values.

### Docstrings

Every public function and method must have a clear docstring covering:
- What the function does
- Arguments (with types and descriptions)
- Return values
- Raised exceptions (if any)
- Additional notes when behavior is non-obvious

### Writing Documentation

User-facing and design documentation lives in the `docs/source/` directory and is built with **Sphinx**. Documentation files use reStructuredText (`.rst`). When adding or modifying docs, place them in the appropriate subdirectory under `docs/source/` (e.g., `developer_guide/`, `getting_started/`, `kv_cache/`) and make sure any new pages are linked from a `toctree` so they appear in the built site.

When writing or updating documentation, follow these principles:

- **Be concrete and concise.** State exactly what something does and why — avoid vague, hand-wavy descriptions. One precise sentence beats a paragraph of generalities.
- **Include examples.** Show concrete code snippets, command invocations, or data formats so the reader can immediately see how things work in practice.
- **Explain the _why_, not just the _what_.** Briefly state the design motivation or trade-off behind a decision so readers understand the reasoning.
- **Use diagrams or short flows for complex interactions.** When multiple components interact (e.g., the multiprocess pipeline), a short step-by-step flow or ASCII diagram is far clearer than prose alone.
- **Keep scope focused.** Each document should have a clear audience and purpose. Don't mix user-facing setup guides with internal architecture notes.

#### Building and verifying docs

Always verify that the Sphinx build passes after making documentation changes:

```bash
# Build into a fresh temporary directory; no product imports or native build
DOCS_OUTPUT=$(mktemp -d /tmp/lmcache-docs.XXXXXXXX)
sphinx-build -E -W -b html docs/source "$DOCS_OUTPUT"
```

The build must complete **without errors or warnings**. Review the generated
HTML in `$DOCS_OUTPUT` to confirm formatting, links, and examples render correctly.
Use available Sphinx tooling; do not alter the serving environment to build docs.
You can preview locally with:

```bash
python -m http.server --bind 127.0.0.1 --directory "$DOCS_OUTPUT"
```

### Encapsulation

Never access private members (prefixed with `_`) of other classes. Interact only through their public APIs.

### Code Organization

- **Module-level helper functions** go at the top of the file (after imports, before classes).
- **Private/helper methods** within a class go at the end of the class, after all public methods.

## Code Review Checklist

When reviewing code (or self-checking before submitting), verify all of the following:

### Correctness
- [ ] The code does what it claims to do and matches the PR description.
- [ ] Edge cases are handled (empty inputs, None values, boundary conditions).
- [ ] No regressions to existing functionality — existing tests still pass.

### Style & Standards
- [ ] `pre-commit run --all-files` passes with no errors.
- [ ] All new/modified functions have type hints for arguments and return values.
- [ ] All new/modified public functions have complete docstrings.
- [ ] License header (`# SPDX-License-Identifier: Apache-2.0`) is present on all Python files.
- [ ] Import ordering follows the section-heading convention (Standard / Third Party / First Party / Local).

### Encapsulation & Design
- [ ] No direct access to private members (`_`-prefixed) of other classes.
- [ ] New public APIs are minimal and well-defined — avoid exposing internals.
- [ ] Module-level helpers are placed at the top; private methods at the end of the class.

### Testing
- [ ] New features and bug fixes include corresponding tests.
- [ ] Tests target the public interface and docstring contract, not implementation details.
- [ ] The explicit host subset passes; pending NPU/tensor cases are reported.

### Documentation
- [ ] New or updated documentation is concrete, concise, and includes examples.
- [ ] Design decisions explain the _why_, not just the _what_.
- [ ] Docs are placed in the correct subdirectory under `docs/source/` and linked from a `toctree`.
- [ ] Sphinx build with `-E -W` completes without errors or warnings in a fresh output directory.

### Safety & Performance
- [ ] No security vulnerabilities (injection, unsafe deserialization, etc.).
- [ ] No unnecessary memory copies or allocations in hot paths.
- [ ] Thread safety is maintained for shared data structures.
- [ ] NPU and host cache resources are properly allocated, freed and synchronized.
