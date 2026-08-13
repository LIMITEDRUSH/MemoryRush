"""Parse TXT and Markdown documents into JSONL."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from memoryrush.ingestion import parse_directory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parse TXT and Markdown documents.")
    parser.add_argument("input_dir", help="Directory containing .txt or .md files.")
    parser.add_argument(
        "--output",
        default="data/processed/documents.jsonl",
        help="Output JSONL path.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    documents = parse_directory(args.input_dir)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="\n") as output_file:
        for document in documents:
            output_file.write(json.dumps(document.to_dict(), ensure_ascii=False) + "\n")

    print(f"Parsed {len(documents)} documents -> {output_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
