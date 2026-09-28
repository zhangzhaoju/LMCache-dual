# SPDX-License-Identifier: Apache-2.0
"""Native P3 build entry: one lmcache namespace with Ascend extensions."""

import sys
from pathlib import Path

from setuptools import setup

sys.path.insert(0, str(Path(__file__).resolve().parent))
from p1_build import setup_arguments

setup(**setup_arguments("lmcache"))
