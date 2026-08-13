"""Validate or run deterministic provisional Direction 1 admission baselines."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from memoryrush.admission.experiment_runner import (
    SUPPORTED_METHODS,
    ExperimentConfig,
    RunClass,
    build_invalid_experiment_artifact,
    load_frozen_benchmark,
    run_direction1_experiment,
    write_experiment_artifact,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("benchmark", help="Frozen Direction 1 JSONL path.")
    parser.add_argument("--benchmark-sha256", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--run-class",
        required=True,
        choices=tuple(item.value for item in RunClass),
        help="Explicit epistemic run class; no class is assumed by default.",
    )
    parser.add_argument("--methods", nargs="+", required=True, choices=SUPPORTED_METHODS)
    parser.add_argument("--matched-target", type=int)
    parser.add_argument("--seed", default="direction1-fixed-seed-v1")
    parser.add_argument("--prompt-version", default="deterministic-no-prompt-v1")
    parser.add_argument("--config-version", default="direction1-runner-v0.1")
    parser.add_argument("--output")
    parser.add_argument("--git-head")
    parser.add_argument("--git-dirty", type=_parse_bool)
    parser.add_argument(
        "--check-input-only",
        action="store_true",
        help="Validate benchmark hash/schema and config without running methods.",
    )
    return parser


def _parse_bool(value: str) -> bool:
    normalized = value.casefold()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise argparse.ArgumentTypeError("must be 'true' or 'false'")


def read_git_state(repository: Path) -> tuple[str, bool]:
    """Read actual repository provenance; CLI claims must match these values."""

    head_process = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )
    status_process = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=normal"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )
    head = head_process.stdout.strip().casefold()
    if len(head) != 40 or any(character not in "0123456789abcdef" for character in head):
        raise ValueError("git rev-parse returned an invalid HEAD")
    return head, bool(status_process.stdout)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    started_at = datetime.now().astimezone()
    actual_git_head: str | None = None
    actual_git_dirty: bool | None = None
    try:
        if not args.check_input_only:
            if args.output is None or args.git_head is None or args.git_dirty is None:
                raise ValueError(
                    "--output, --git-head, and --git-dirty are required unless "
                    "--check-input-only"
                )
            Path(args.output).resolve().parent.mkdir(parents=True, exist_ok=True)
            actual_git_head, actual_git_dirty = read_git_state(PROJECT_ROOT)
            if args.git_head != actual_git_head:
                raise ValueError("--git-head does not match the repository HEAD")
            if args.git_dirty is not actual_git_dirty:
                raise ValueError("--git-dirty does not match the repository status")
        config = ExperimentConfig(
            run_id=args.run_id,
            run_class=RunClass(args.run_class),
            benchmark_sha256=args.benchmark_sha256,
            seed=args.seed,
            methods=tuple(args.methods),
            prompt_version=args.prompt_version,
            config_version=args.config_version,
        )
        frozen = load_frozen_benchmark(args.benchmark, config.benchmark_sha256)
        if args.check_input_only:
            print(
                json.dumps(
                    {
                        "benchmark_path": frozen.benchmark_path,
                        "benchmark_sha256": frozen.benchmark_sha256,
                        "case_count": len(frozen.cases),
                        "mode": "check-input-only",
                        "run_class": config.run_class.value,
                        "valid": True,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            return 0
        artifact = run_direction1_experiment(
            frozen,
            config,
            git_head=actual_git_head,
            git_dirty=actual_git_dirty,
            started_at=started_at,
            matched_target=args.matched_target,
        )
        write_experiment_artifact(args.output, artifact)
    except (OSError, TypeError, ValueError) as exc:
        invalid_written = False
        if (
            args.output is not None
            and (actual_git_head is not None or args.git_head is not None)
            and (actual_git_dirty is not None or args.git_dirty is not None)
        ):
            output = Path(args.output)
            try:
                output.resolve().parent.mkdir(parents=True, exist_ok=True)
                benchmark_path = Path(args.benchmark)
                byte_size = benchmark_path.stat().st_size if benchmark_path.is_file() else 0
                invalid = build_invalid_experiment_artifact(
                    run_id=args.run_id,
                    benchmark_path=benchmark_path,
                    benchmark_sha256=args.benchmark_sha256,
                    benchmark_byte_size=byte_size,
                    seed=args.seed,
                    prompt_version=args.prompt_version,
                    config_version=args.config_version,
                    git_head=actual_git_head or args.git_head,
                    git_dirty=(
                        actual_git_dirty
                        if actual_git_dirty is not None
                        else args.git_dirty
                    ),
                    started_at=started_at,
                    ended_at=datetime.now().astimezone(),
                    failure=str(exc),
                )
                write_experiment_artifact(output, invalid)
                invalid_written = True
            except (OSError, TypeError, ValueError):
                invalid_written = False
        print(
            json.dumps(
                {
                    "error": str(exc),
                    "invalid_artifact_written": invalid_written,
                    "valid": False,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 1

    print(
        json.dumps(
            {
                "benchmark_sha256": frozen.benchmark_sha256,
                "case_count": len(frozen.cases),
                "output": str(Path(args.output).resolve()),
                "run_id": config.run_id,
                "valid": True,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
