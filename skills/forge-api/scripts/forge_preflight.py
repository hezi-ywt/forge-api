"""Compatibility wrapper for the installed ``forge-preflight`` command."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from forge_api.cli import main

raise SystemExit(main())
