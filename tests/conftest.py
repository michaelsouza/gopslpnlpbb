from __future__ import annotations

import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"
TOOLS = REPO / "tools"

for path in (SRC, TOOLS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
