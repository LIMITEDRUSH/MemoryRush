"""Process one TXT/Markdown article into a structured memory artifact."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from memoryrush.ingestion import parse_document
from memoryrush.pipeline import run_article_memory_pipeline
from memoryrush.providers import FakeMemoryProvider, OllamaMemoryProvider


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Process one article into memory output.")
    parser.add_argument("input_file", help="Path to a .txt, .md, or .markdown article.")
    parser.add_argument(
        "--output",
        default="data/processed/article_memory_artifact.json",
        help="Output JSON artifact path.",
    )
    parser.add_argument(
        "--provider",
        choices=["fake", "ollama"],
        default="fake",
        help="Generation provider. Use fake for deterministic local checks.",
    )
    parser.add_argument(
        "--model",
        default="qwen2.5:7b-instruct",
        help="Ollama model name when --provider ollama is used.",
    )
    parser.add_argument(
        "--prompt-version",
        default="article_memory_v1",
        help="Prompt template name under memoryrush/prompts without .md.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    document = parse_document(args.input_file)
    provider = _build_provider(provider_name=args.provider, model_name=args.model)
    model_name = getattr(provider, "model_name", getattr(provider, "provider_name", "unknown"))
    artifact = run_article_memory_pipeline(
        document=document,
        provider=provider,
        prompt_version=args.prompt_version,
        model_name=model_name,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    status = "valid" if artifact.validation_report.is_valid else "invalid"
    print(f"Processed {document.source_path} -> {output_path.as_posix()} ({status})")
    return 0 if artifact.validation_report.is_valid else 1


def _build_provider(provider_name: str, model_name: str) -> FakeMemoryProvider | OllamaMemoryProvider:
    if provider_name == "fake":
        return FakeMemoryProvider()
    return OllamaMemoryProvider(model_name=model_name)


if __name__ == "__main__":
    raise SystemExit(main())
