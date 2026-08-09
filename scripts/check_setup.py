"""Basic setup check for Phase 0."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from memoryrush.cli import run_health


def main() -> int:
    required_paths = [
        Path("README.md"),
        Path("requirements.txt"),
        Path(".env.example"),
        Path("memoryrush"),
        Path("app"),
        Path("data/sample_docs"),
        Path("tests"),
    ]
    missing = [path.as_posix() for path in required_paths if not path.exists()]
    if missing:
        print("Missing required paths:")
        for path in missing:
            print(f"- {path}")
        return 1

    return run_health()


if __name__ == "__main__":
    raise SystemExit(main())
