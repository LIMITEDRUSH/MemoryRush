"""Local serialization helpers for reviewable processing artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from memoryrush.models import ProcessingArtifact


def artifact_json(artifact: ProcessingArtifact) -> str:
    return json.dumps(artifact.to_dict(), ensure_ascii=False, indent=2)


def save_artifact(artifact: ProcessingArtifact, output_dir: str | Path) -> Path:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{artifact.run_id}.json"
    path.write_text(artifact_json(artifact), encoding="utf-8")
    return path
