import io
import json
import urllib.error
from dataclasses import asdict

import pytest
from test_recall_chat import ChatModel
from test_scoring import Scorer, fixture_output

from memoryrush.api import APIConfig, OpenAICompatibleProvider, _NoAPIRedirect, completion_endpoint
from memoryrush.bank import MemoryBank
from memoryrush.chat import answer
from memoryrush.cli import make_provider
from memoryrush.pipeline import process_text
from memoryrush.providers import ProviderError

SECRET = "fixture-only-secret-never-a-real-key"


def provider(**kwargs):
    config = APIConfig("https://models.example.test/v1", "fixture-model", **kwargs)
    return OpenAICompatibleProvider(config, SECRET, approved_endpoint=config.endpoint)


class Response:
    def __init__(self, payload):
        self.raw = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self, size):
        return self.raw[:size]


def envelope(value, finish="stop"):
    return {"choices": [{"finish_reason": finish, "message": {"content": json.dumps(value)}}]}


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/v1",
        "https://user:secret@example.com/v1",
        "https://example.com/v1?key=secret",
        "https://example.com/v1#secret",
        "https://localhost/v1",
        "https://127.0.0.1/v1",
        "https://10.1.1.1/v1",
        "https://example.com:bad/v1",
        "https://example.com/\ninvalid",
    ],
)
def test_api_endpoint_rejects_unsafe_input(url):
    with pytest.raises(ValueError):
        completion_endpoint(url)


def test_endpoint_normalization_and_consent():
    expected = "https://models.example.test/v1/chat/completions"
    assert completion_endpoint("https://MODELS.example.test:443/v1/") == expected
    assert completion_endpoint(expected) == expected
    config = APIConfig(expected, "fixture")
    with pytest.raises(ValueError, match="允许"):
        OpenAICompatibleProvider(config, SECRET)
    with pytest.raises(ValueError, match="允许"):
        OpenAICompatibleProvider(
            config, SECRET, approved_endpoint="https://other.test/chat/completions"
        )
    with pytest.raises(ValueError, match="密钥"):
        OpenAICompatibleProvider(config, "", approved_endpoint=expected)
    with pytest.raises(ValueError, match="空白"):
        OpenAICompatibleProvider(config, "bad\r\nheader", approved_endpoint=expected)


def test_api_payload_auth_and_explicit_token_parameter(monkeypatch):
    seen = []

    def fake_open(self, request, timeout):
        seen.append(request)
        assert request.full_url == "https://models.example.test/v1/chat/completions"
        assert request.get_header("Authorization") == f"Bearer {SECRET}"
        body = json.loads(request.data)
        assert SECRET not in json.dumps(body)
        assert body["max_completion_tokens"] == 2048
        assert "max_tokens" not in body and "temperature" not in body
        assert "chat_template_kwargs" not in body
        assert body["response_format"]["type"] == "json_object"
        assert timeout == 180
        assert body["messages"][0]["content"].endswith('"type": "object"}')
        return Response(envelope({"result": "ok"}))

    monkeypatch.setattr("urllib.request.OpenerDirector.open", fake_open)
    adapter = provider(token_parameter="max_completion_tokens", output_tokens=2048)
    assert adapter.complete_json("Question", schema={"type": "object"}) == {"result": "ok"}
    assert len(seen) == 1
    assert SECRET not in json.dumps(adapter.config.public_dict())


@pytest.mark.parametrize("mode", ["json_schema", "prompt"])
def test_explicit_compatibility_modes(monkeypatch, mode):
    def fake_open(self, request, timeout):
        body = json.loads(request.data)
        if mode == "json_schema":
            assert body["response_format"]["json_schema"]["strict"] is True
        else:
            assert "response_format" not in body
        return Response(envelope({"ok": True}))

    monkeypatch.setattr("urllib.request.OpenerDirector.open", fake_open)
    assert provider(response_mode=mode).complete_json("x", schema={"type": "object"})["ok"]


@pytest.mark.parametrize("status", [400, 401, 403, 404, 429, 500])
def test_http_errors_redact_and_never_retry(monkeypatch, status):
    calls = []

    def fail(self, request, timeout):
        calls.append(1)
        raise urllib.error.HTTPError(
            request.full_url + SECRET, status, SECRET, {}, io.BytesIO(SECRET.encode())
        )

    monkeypatch.setattr("urllib.request.OpenerDirector.open", fail)
    with pytest.raises(ProviderError) as failure:
        provider().complete_json("Private question")
    assert str(status) in str(failure.value)
    assert SECRET not in str(failure.value)
    assert "Private question" not in str(failure.value)
    assert len(calls) == 1 and failure.value.__suppress_context__


def test_redirect_and_network_errors_do_not_disclose_or_fallback(monkeypatch):
    with pytest.raises(ProviderError, match="重定向"):
        _NoAPIRedirect().redirect_request(None, None, 302, "", {}, "https://elsewhere.test")

    def fail(*a, **k):
        raise OSError(SECRET)

    monkeypatch.setattr("urllib.request.OpenerDirector.open", fail)
    with pytest.raises(ProviderError) as failure:
        provider().complete_json("x")
    assert SECRET not in str(failure.value)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        [],
        {"choices": []},
        {"choices": [None]},
        envelope({}, "length"),
        {"choices": [{"finish_reason": "stop", "message": {"content": "not JSON"}}]},
        {"choices": [{"finish_reason": "stop", "message": {"content": None}}]},
        {"choices": [{"finish_reason": "stop", "message": {"content": "{}", "refusal": "No"}}]},
    ],
)
def test_invalid_or_partial_api_results_are_rejected(monkeypatch, payload):
    monkeypatch.setattr("urllib.request.OpenerDirector.open", lambda *a, **k: Response(payload))
    with pytest.raises(ProviderError):
        provider().complete_json("x")


def test_mock_api_flows_through_scoring_storage_and_recall(tmp_path, monkeypatch):
    calls = []

    def fake_open(self, request, timeout):
        body = json.loads(request.data)
        prompt = body["messages"][-1]["content"]
        calls.append(prompt)
        if "DATA:\n" not in prompt:
            value = asdict(fixture_output())
        elif "candidates" in json.loads(prompt.split("DATA:\n")[1]):
            value = Scorer().complete_json(prompt, 4096)
        else:
            value = ChatModel().complete_json(prompt, 4096)
        return Response(envelope(value))

    monkeypatch.setattr("urllib.request.OpenerDirector.open", fake_open)
    adapter, bank = provider(), MemoryBank(tmp_path / "test.db")
    artifact = process_text(
        "x.md", "Useful concept number one.\n\nA different practical mechanism.", adapter
    )
    bank.import_artifact(artifact)
    assert all(m["unit"]["assessment"]["method"] == "llm" for m in bank.memories(True))
    turn = answer(bank, adapter, bank.new_session(), "What is the concept?")
    assert turn["provider"] == "openai-compatible" and turn["used_memory_ids"]
    assert len(calls) == 4  # extraction, scoring, relevance and grounded answer
    assert SECRET not in json.dumps(bank.artifacts())
    assert SECRET not in json.dumps(turn)


def test_cli_requires_opt_in_and_named_environment(monkeypatch):
    monkeypatch.setenv("TEST_MEMORYRUSH_KEY", SECRET)
    with pytest.raises(ValueError, match="allow-remote"):
        make_provider("api", "fixture", "https://models.example.test/v1")
    adapter = make_provider(
        "api",
        "fixture",
        "https://models.example.test/v1",
        allow_remote=True,
        api_key_env="TEST_MEMORYRUSH_KEY",
    )
    assert adapter.model_name == "fixture"
