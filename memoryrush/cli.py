"""Command line entry points for the early MemoryRush project skeleton."""

from __future__ import annotations

import argparse
from pathlib import Path

from memoryrush import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="memoryrush",
        description="Local-first reading memory retrieval system.",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("health", help="Check that the project skeleton is runnable.")

    samples = subparsers.add_parser("samples", help="List sample documents.")
    samples.add_argument(
        "--path",
        default="data/sample_docs",
        help="Directory containing sample .txt or .md documents.",
    )

    return parser


def run_health() -> int:
    print(f"MemoryRush {__version__} is ready.")
    return 0


def run_samples(path: str) -> int:
    sample_dir = Path(path)
    if not sample_dir.exists():
        print(f"No sample directory found: {sample_dir}")
        return 1

    files = sorted(
        p for p in sample_dir.iterdir() if p.is_file() and p.suffix.lower() in {".txt", ".md"}
    )
    if not files:
        print(f"No .txt or .md sample documents found in {sample_dir}")
        return 1

    for file_path in files:
        print(file_path.as_posix())
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "health":
        return run_health()
    if args.command == "samples":
        return run_samples(args.path)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
