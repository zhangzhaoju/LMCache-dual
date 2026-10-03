# SPDX-License-Identifier: Apache-2.0
"""Static native ownership checks; no torch import, compiler or device probe."""

from __future__ import annotations

# Standard
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check() -> dict:
    """Validate canonical owners, method preservation and retired import paths.

    Returns:
        A source-only report; success does not imply native ABI/NPU acceptance.
    """
    errors: list[str] = []
    trees = {}
    for path in sorted((ROOT / "lmcache").rglob("*.py")):
        relative = str(path.relative_to(ROOT))
        try:
            tree = ast.parse(
                path.read_text(), filename=relative, feature_version=(3, 11)
            )
        except SyntaxError as exc:
            errors.append(f"{relative}: {exc}")
            continue
        trees[relative] = tree
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names]
                names += [node.module or ""] if isinstance(node, ast.ImportFrom) else []
                if any(
                    n.startswith(("lmcache_ascend", "vllm_ascend"))
                    or n == "transfer_to_npu"
                    for n in names
                ):
                    errors.append(f"{relative}:{node.lineno}: retired import")
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (
                        isinstance(target, ast.Subscript)
                        and ast.unparse(target.value) == "sys.modules"
                    ):
                        errors.append(f"{relative}:{node.lineno}: module replacement")
    manifest = json.loads((ROOT / "docs/p3-native-migration.json").read_text())
    retired = json.loads((ROOT / "docs/p4-retired-native-owners.json").read_text())
    checked_methods = 0
    checked_classes = 0
    for merge in manifest["method_merges"]:
        path = merge["owner"].replace(".", "/") + ".py"
        name = merge["base"]
        if path.endswith("npu_connectors.py"):
            name = merge["donor"]
        if name == "CudaIPCWrapper":
            name = "NPUIPCWrapper"
        removed = name in retired["removed_classes"].get(path, [])
        cls = next(
            (
                n
                for n in trees[path].body
                if isinstance(n, ast.ClassDef) and n.name == name
            ),
            None,
        )
        if removed:
            if cls is not None:
                errors.append(f"Retired P4 class still present: {path}:{name}")
            continue
        if cls is None:
            errors.append(f"Missing canonical class: {path}:{name}")
            continue
        methods = {n.name for n in cls.body if isinstance(n, ast.FunctionDef)}
        expected = set(merge["base_methods"]) | set(merge["donor_methods"])
        expected |= set(merge["common_delegates"].values())
        removed_methods = set(
            retired.get("removed_methods", {}).get(f"{path}:{name}", [])
        )
        if removed_methods - expected:
            errors.append(
                f"{path}:{name}: unknown retired methods {sorted(removed_methods - expected)}"
            )
        if removed_methods & methods:
            errors.append(
                f"{path}:{name}: retired methods remain {sorted(removed_methods & methods)}"
            )
        expected -= removed_methods
        missing = expected - methods
        if missing:
            errors.append(f"{path}:{name}: lost methods {sorted(missing)}")
        for n in ast.walk(cls):
            if (
                isinstance(n, ast.Attribute)
                and isinstance(n.value, ast.Name)
                and n.value.id == "self"
                and n.attr.startswith("_common_")
                and n.attr not in methods
            ):
                errors.append(f"{name}: unresolved common delegation {n.attr}")
        if any("GPUConnector" in ast.unparse(base) for base in cls.bases):
            errors.append(f"{name}: legacy GPU inheritance")
        checked_methods += len(expected)
        checked_classes += 1
    for destination in set(manifest["relocations"].values()):
        if any(destination.startswith(p) for p in retired["removed_prefixes"]):
            if (ROOT / destination).exists():
                errors.append(f"Retired P4 destination still present: {destination}")
            continue
        if not (ROOT / destination).is_file():
            errors.append(f"Missing native destination {destination}")
    active = {
        "lmcache/v1/cache_engine.py",
        "lmcache/v1/storage_backend/storage_manager.py",
        "lmcache/integration/vllm/vllm_v1_adapter.py",
        "lmcache/integration/vllm/utils.py",
        "lmcache/v1/npu_connector/npu_connectors.py",
        "lmcache/v1/npu_connector/__init__.py",
        "lmcache/v1/multiprocess/custom_types.py",
        "lmcache/v1/device_connector/utils.py",
    }
    for relative in active:
        for node in ast.walk(trees[relative]):
            if isinstance(node, ast.Attribute) and ast.unparse(node).startswith(
                ("torch.cuda", "torch.xpu", "torch.npu.cudart")
            ):
                errors.append(f"{relative}:{node.lineno}: non-NPU device API")
    return {
        "scope": "static_source_not_build_ABI_or_NPU",
        "python_files": len(trees),
        "method_contracts": checked_methods,
        "merged_classes": checked_classes,
        "errors": errors,
        "passed": not errors,
    }


if __name__ == "__main__":
    result = check()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)
