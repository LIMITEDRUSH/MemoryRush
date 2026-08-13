"""Ollama adapter for article-memory extraction."""

from __future__ import annotations

import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from memoryrush.pipeline import ArticleMemoryOutput, article_memory_output_from_dict


class OllamaMemoryProvider:
    provider_name = "ollama"

    def __init__(
        self,
        model_name: str,
        endpoint: str = "http://localhost:11434/api/generate",
        timeout_seconds: int = 120,
    ) -> None:
        self.model_name = model_name
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self.last_raw_output: str | None = None

    def generate(self, prompt_context: str) -> ArticleMemoryOutput:
        payload = {
            "model": self.model_name,
            "prompt": prompt_context,
            "stream": False,
            "format": "json",
        }
        request = Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except URLError as exc:
            raise RuntimeError(
                "Could not reach Ollama. Start Ollama and pull the configured model first."
            ) from exc

        envelope = json.loads(body)
        raw_output = envelope.get("response")
        if isinstance(raw_output, str):
            self.last_raw_output = raw_output
        return parse_ollama_generate_response(body)


def parse_ollama_generate_response(response_body: str) -> ArticleMemoryOutput:
    envelope = json.loads(response_body)
    raw_output = envelope.get("response")
    if not isinstance(raw_output, str) or not raw_output.strip():
        raise ValueError("Ollama response did not contain a non-empty JSON response field.")

    return article_memory_output_from_dict(json.loads(raw_output))
