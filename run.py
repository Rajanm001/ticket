"""Single-command entry point that works on any platform (including Windows
without `make`): install deps, build the dataset if missing, start the API.

Usage:
    python run.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _run(args: list[str]) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> None:
    _run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    if not (ROOT / "data" / "tickets.json").exists():
        _run([sys.executable, "scripts/generate_data.py"])

    _run([sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000"])


if __name__ == "__main__":
    main()
