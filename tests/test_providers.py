import json

import pytest

from memoryrush.parsing import parse_document
from memoryrush.providers import (
    LlamaCppProvider,
    OllamaProvider,
    ProviderError,
    validate_local_endpoint,
)


class _FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


def test_ollama_provider_parses_structured_response(monkeypatch) -> None:
    model_output = {
        "summary": "A grounded summary.",
        "core_ideas": [],
        "memory_units": [
            {
                "content": "Stable IDs keep generated memories traceable.",
                "memory_type": "claim",
                "evidence": [{"paragraph_id": "p_001", "quote": "Stable IDs"}],
                "tags": ["grounding"],
                "confidence": 0.9,
                "scores": {
                    "importance": 0.9,
                    "novelty": 0.6,
                    "usefulness": 0.8,
                    "evidence_strength": 1.0,
                },
            }
        ],
        "recall_questions": [
            {
                "question": "Why use stable IDs?",
                "answer": "They keep memories traceable.",
                "memory_unit_index": 0,
            }
        ],
    }
    http_payload = json.dumps({"response": json.dumps(model_output)}).encode()

    def fake_urlopen(self, request, timeout):
        assert request.full_url.endswith("/api/generate")
        assert timeout == 180
        return _FakeResponse(http_payload)

    monkeypatch.setattr("urllib.request.OpenerDirector.open", fake_urlopen)
    document = parse_document("sample.txt", "Stable IDs keep generated memories traceable.")
    result = OllamaProvider().generate(document, "prompt")

    assert result.output.memory_units[0].tags == ["grounding"]
    assert result.output.recall_questions[0].memory_unit_index == 0


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://example.com/api",
        "http://10.0.0.1:8080",
        "http://localhost.evil.com/api",
        "file:///tmp/x",
        "http://user:secret@localhost:8888/api",
    ],
)
def test_remote_or_credentialed_model_urls_rejected(endpoint):
    with pytest.raises(ValueError):
        validate_local_endpoint(endpoint)


def test_llama_schema_and_truncation(monkeypatch):
    def request(endpoint, body, timeout):
        assert body["response_format"]["schema"] == {"type": "object"}
        assert not body["chat_template_kwargs"]["enable_thinking"]
        return {"choices": [{"finish_reason": "length", "message": {"content": "{}"}}]}

    monkeypatch.setattr("memoryrush.providers._request_json", request)
    with pytest.raises(ProviderError, match="finish"):
        LlamaCppProvider().complete_json("x", schema={"type": "object"})


def test_context_overflow_fails_before_http(monkeypatch):
    monkeypatch.setattr(
        "memoryrush.providers._request_json", lambda *a: pytest.fail("HTTP must not run")
    )
    with pytest.raises(ProviderError, match="context"):
        OllamaProvider().complete_json("字" * 6000)
