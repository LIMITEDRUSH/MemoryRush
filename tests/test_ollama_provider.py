import json

from memoryrush.providers.ollama import OllamaMemoryProvider, parse_ollama_generate_response


def test_parse_ollama_generate_response_loads_article_memory_output() -> None:
    response_body = {
        "response": json.dumps(
            {
                "summary": "A summary.",
                "core_ideas": [
                    {
                        "idea": "Evidence matters.",
                        "why_it_matters": "It keeps output grounded.",
                        "evidence": {"paragraph_id": "p_001", "quote": "Evidence matters."},
                        "salience_score": 0.8,
                    }
                ],
                "memory_units": [
                    {
                        "content": "Evidence matters for generated memory.",
                        "memory_type": "conceptual_insight",
                        "evidence_paragraph_ids": ["p_001"],
                        "tags": ["evidence"],
                        "confidence": 0.75,
                    }
                ],
                "recall_questions": [
                    {
                        "question": "What matters for generated memory?",
                        "expected_answer": "Evidence.",
                        "memory_unit_index": 0,
                    }
                ],
            }
        )
    }

    output = parse_ollama_generate_response(json.dumps(response_body))

    assert output.memory_units[0].content == "Evidence matters for generated memory."


def test_ollama_provider_uses_configured_model_name() -> None:
    provider = OllamaMemoryProvider(model_name="qwen2.5:7b-instruct")

    assert provider.provider_name == "ollama"
    assert provider.model_name == "qwen2.5:7b-instruct"
