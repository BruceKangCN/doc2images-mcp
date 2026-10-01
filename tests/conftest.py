"""Shared pytest configuration for the doc2images-mcp test suite."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Pin the base directory for relative paths to the project root *before* the
# package is imported, so tests are independent of the directory pytest is
# launched from.
os.environ["DOC2IMG_BASE_DIR"] = str(PROJECT_ROOT)

DATA_DIR = PROJECT_ROOT / "data"
TMP_DIR = PROJECT_ROOT / "tmp"
