"""Command line entry points for MemoryRush."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from memoryrush import __version__
from memoryrush.api import APIConfig, OpenAICompatibleProvider
from memoryrush.bank import MemoryBank, current_strength, data_directory
from memoryrush.chat import answer
from memoryrush.parsing import parse_document_file
from memoryrush.pipeline import process_document
from memoryrush.providers import (
    DeterministicPreviewProvider,
    LlamaCppProvider,
    OllamaProvider,
    ProviderError,
)
from memoryrush.storage import save_artifact


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

    process = subparsers.add_parser("process", help="Create a source-grounded memory artifact.")
    process.add_argument("input", help="Path to a UTF-8 .txt, .md, or .markdown document.")
    process.add_argument(
        "--provider",
        choices=("ollama", "llama.cpp", "api", "preview"),
        default="llama.cpp",
        help="Local model, explicitly enabled HTTPS API, or offline preview.",
    )
    process.add_argument("--model", default="qwen3:8b", help="Exact model ID.")
    process.add_argument("--endpoint", default=None, help="Local endpoint or HTTPS API base URL.")
    process.add_argument("--db", default=None, help="Private SQLite path.")
    process.add_argument("--budget", type=int, default=5, help="Maximum admitted memories.")
    process.add_argument(
        "--output-dir",
        default=str(data_directory() / "artifacts"),
        help="Private artifact directory.",
    )

    ask = subparsers.add_parser(
        "ask", help="Ask using persistent memories and recent conversation."
    )
    ask.add_argument("question")
    ask.add_argument("--provider", choices=("llama.cpp", "ollama", "api"), default="llama.cpp")
    ask.add_argument("--model", default="qwen3:8b")
    ask.add_argument("--endpoint", default=None)
    ask.add_argument("--db", default=None)
    ask.add_argument(
        "--session", default=None, help="Existing conversation ID; omitted starts one."
    )
    for command in (process, ask):
        command.add_argument(
            "--allow-remote",
            action="store_true",
            help=(
                "Explicitly permit sending article text, reading interests, candidate memories, "
                "question and recent conversation to --endpoint; requests may incur charges."
            ),
        )
        command.add_argument(
            "--api-key-env",
            default="MEMORYRUSH_API_KEY",
            help="Name of the environment variable containing the key; never pass the key itself.",
        )
        command.add_argument(
            "--json-mode", choices=("json_object", "json_schema", "prompt"), default="json_object"
        )
        command.add_argument(
            "--token-parameter",
            choices=("max_tokens", "max_completion_tokens"),
            default="max_tokens",
        )
        command.add_argument("--api-output-tokens", type=int, default=8192)
    bank = subparsers.add_parser("memories", help="List stored memory scores and current strength.")
    bank.add_argument("--db", default=None)

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


def run_process(
    input_path: str,
    provider_name: str,
    model_name: str,
    budget: int,
    output_dir: str,
    endpoint: str | None = None,
    db_path: str | None = None,
    api_options: dict | None = None,
) -> int:
    try:
        document = parse_document_file(input_path)
        provider = make_provider(provider_name, model_name, endpoint, **(api_options or {}))
        bank = MemoryBank(db_path) if provider_name != "preview" or db_path else None
        artifact = process_document(
            document,
            provider,
            memory_budget=budget,
            profile=bank.setting("profile") if bank else "",
            prior_memories=bank.memories(True) if bank else [],
        )
        if bank:
            bank.import_artifact(artifact)
        output_path = save_artifact(artifact, output_dir)
    except (OSError, ValueError, ProviderError) as exc:
        print(f"MemoryRush could not process the document: {exc}")
        return 1

    admitted = sum(decision.admitted for decision in artifact.admission)
    print(f"Saved {output_path.as_posix()}")
    print(
        f"Validation: {artifact.validation.error_count} error(s), "
        f"{artifact.validation.warning_count} warning(s); admitted {admitted} memory point(s)."
    )
    return 0


def make_provider(
    name: str,
    model: str,
    endpoint: str | None = None,
    *,
    allow_remote=False,
    api_key_env="MEMORYRUSH_API_KEY",
    json_mode="json_object",
    token_parameter="max_tokens",
    api_output_tokens=8192,
):
    if name == "preview":
        return DeterministicPreviewProvider()
    if name == "api":
        if not endpoint or not allow_remote:
            raise ValueError("API 模式需要 --endpoint 和显式 --allow-remote；未发出请求。")
        config = APIConfig(
            endpoint, model, api_key_env, json_mode, token_parameter, api_output_tokens
        )
        return OpenAICompatibleProvider(
            config, os.environ.get(api_key_env, ""), approved_endpoint=config.endpoint
        )
    if name not in {"llama.cpp", "ollama"}:
        raise ValueError("Unknown model provider.")
    cls = LlamaCppProvider if name == "llama.cpp" else OllamaProvider
    return cls(model_name=model, **({"endpoint": endpoint} if endpoint else {}))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    api_options = {
        key: getattr(args, key)
        for key in (
            "allow_remote",
            "api_key_env",
            "json_mode",
            "token_parameter",
            "api_output_tokens",
        )
        if hasattr(args, key)
    }

    if args.command == "health":
        return run_health()
    if args.command == "samples":
        return run_samples(args.path)
    if args.command == "process":
        return run_process(
            args.input,
            args.provider,
            args.model,
            args.budget,
            args.output_dir,
            args.endpoint,
            args.db,
            api_options,
        )
    if args.command == "memories":
        for memory in MemoryBank(args.db).memories():
            print(
                f"{memory['memory_id']} [{memory['state']}] base={memory['base_score']:.3f} "
                f"strength={current_strength(memory):.3f} {memory['content']}"
            )
        return 0
    if args.command == "ask":
        try:
            provider = make_provider(args.provider, args.model, args.endpoint, **api_options)
            bank = MemoryBank(args.db)
            session = args.session or bank.new_session()
            turn = answer(
                bank,
                provider,
                session,
                args.question,
            )
            print(
                f"Session: {session}\n{turn['answer']}\nCitations: {', '.join(turn['used_memory_ids'])}"
            )
            return 0
        except (ValueError, OSError, ProviderError) as exc:
            print(f"MemoryRush could not answer: {exc}")
            return 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
