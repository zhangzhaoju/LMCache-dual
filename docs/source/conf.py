# SPDX-License-Identifier: Apache-2.0
"""Offline P4 documentation build; no product imports or remote inventories."""

project = "LMCache Native Ascend Layout"
author = "LMCache contributors"
copyright = "2026, LMCache contributors"
extensions = []
html_theme = "alabaster"
exclude_patterns = [
    "getting_started/ascend_p4.rst",
    "getting_started/ascend_p1.rst",
    "getting_started/ascend_p2.rst",
    "getting_started/ascend_p3.rst",
]
