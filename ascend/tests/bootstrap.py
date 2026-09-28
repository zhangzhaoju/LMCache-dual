# SPDX-License-Identifier: Apache-2.0
"""Resolve this checkout's test fixtures without cloning or patching products."""

from pathlib import Path
from types import ModuleType
import sys

TEST_ALIAS = "lmcache_tests"


def prepare_environment() -> bool:
    """Expose local test helpers under an unambiguous test-only package alias."""
    tests = Path(__file__).resolve().parents[2] / "tests"
    if not tests.is_dir():
        raise RuntimeError(f"Paired LMCache tests not found: {tests}")
    module = ModuleType(TEST_ALIAS)
    module.__path__ = [str(tests)]
    sys.modules[TEST_ALIAS] = module
    return True
