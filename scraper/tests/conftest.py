from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Make scrapers importable
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))
