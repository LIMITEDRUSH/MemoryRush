"""Validate a Direction 1 JSONL benchmark without running any model."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from memoryrush.admission.benchmark import load_benchmark


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("benchmark", help="Path to newline-delimited Direction 1 cases.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        cases = load_benchmark(args.benchmark)
    except (OSError, ValueError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False))
        return 1

    decisions = Counter(case.oracle.decision.value for case in cases)
    families = Counter(case.case_family for case in cases)
    label_sources = Counter(case.oracle.label_source for case in cases)
    result = {
        "valid": True,
        "case_count": len(cases),
        "decisions": dict(sorted(decisions.items())),
        "case_families": dict(sorted(families.items())),
        "label_sources": dict(sorted(label_sources.items())),
        "contains_human_gold": any(
            case.oracle.adjudication_status == "human_gold" for case in cases
        ),
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

