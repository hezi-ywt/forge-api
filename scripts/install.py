"""Install ForgeAPI into a project-local virtual environment."""

from __future__ import annotations

import argparse
import subprocess
import sys
import venv
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Install ForgeAPI package and Skill")
    parser.add_argument("--venv", type=Path, default=root / ".venv", help="project-local virtual environment")
    args = parser.parse_args()

    venv_path = args.venv.expanduser().resolve()
    if not (venv_path / "Scripts" / "python.exe").exists():
        venv.EnvBuilder(with_pip=True).create(venv_path)
    python = venv_path / "Scripts" / "python.exe"
    subprocess.run([str(python), "-m", "pip", "install", "-e", str(root)], check=True)
    print(f"installed ForgeAPI into project environment: {venv_path}")
    print(f"Skill source remains in the project: {root / 'skills' / 'forge-api' / 'SKILL.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
