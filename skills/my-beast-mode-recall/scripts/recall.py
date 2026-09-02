#!/usr/bin/env python3
"""Route recall requests to the sibling My Beast Mode memory helper."""

import os
from pathlib import Path
import sys


helper = Path(__file__).resolve().parents[2] / "my-beast-mode/scripts/memory.py"
if not helper.is_file():
    raise SystemExit("my-beast-mode is required; install the repository with --all")
os.execv(sys.executable, [sys.executable, str(helper), "recall", *sys.argv[1:]])
