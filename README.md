# MemoryRush

A personal, local-first LLM reading assistant. Read TXT or Markdown articles, retain source-grounded Memory Points, and recall them automatically in later conversations. This is a local tool, not a commercial platform.

[中文说明](README_CN.md) · [Detailed usage and mechanisms (Chinese)](docs/READING_ASSISTANT_CN.md)

## Features

- Codex-inspired conversations with history, article attachments, and an optional memory inspector.
- Separate extraction and model-scoring calls, per-axis reasons, exact source quotations, and redundancy-aware admission.
- Local SQLite memory with time decay, model-informed half-lives, pinning, reversible disabling, and reinforcement only for actual citations.
- Automatic recall based on model-rated question relevance and current memory strength, with bounded evidence context and source-cited answers.
- Local llama.cpp and Ollama, or explicitly enabled OpenAI-compatible HTTPS Chat Completions APIs.
- Labelled offline preview; preview candidates are not LLM-scored memories and cannot enter automatic recall.

## Quickstart

Use Python 3.10–3.13 (3.12 recommended). From the repository root:

```powershell
python -m venv .venv-reading
.\.venv-reading\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/check_setup.py
python -m streamlit run app/streamlit_app.py --server.port 8502
```

On macOS/Linux, activate with `source .venv-reading/bin/activate` instead. Open <http://127.0.0.1:8502>. In **Settings**, select your provider and exact model name. Model weights are not included or automatically downloaded.

- **Ollama:** start Ollama and install a local model, e.g. `ollama pull qwen3:8b`; select Ollama and the same model ID in Settings.
- **llama.cpp:** start your GGUF model server, then configure its loopback Chat Completions endpoint and model alias.
- **External API:** choose a preset/custom HTTPS endpoint, model ID, and session-only key (or environment variable name). Explicitly acknowledge outgoing data and costs before enabling it.
- **Offline preview:** inspect the reading workflow without inference; automatic chat requires a real model.

The optional Windows launcher `./scripts/start_local.ps1 -ApiOnly` starts just the UI. `-Ollama` uses an already running Ollama server. For llama.cpp, provide `-LlamaServer` and `-ModelPath` (or `MEMORYRUSH_LLAMA_SERVER` and `MEMORYRUSH_MODEL_PATH`). Automatic environment creation through this launcher requires `uv`; manual installation above does not.

## Scoring and recall

After extraction, the selected LLM separately rates importance, novelty, personal relevance, usefulness, surprise, connections, evidence support, and durability, with reasons. The program combines the first seven axes with explicit user highlights into a base score; durability informs the half-life. High scores cannot override exact quotation checks.

```text
article → extraction → model scoring → evidence/admission checks → local memory
question → model relevance + decayed strength → selected evidence → answer
```

Refreshing the UI does not compound decay. Actual validated citations can reinforce a point at most once per 24 hours. Expand a point in **Memory bank** to inspect scores, reasons, original assessments, evidence, and strength. Exact formulas and limitations are in the guide.

## Command line and tests

```powershell
python -m memoryrush.cli process data/sample_docs/reading_memory_example.txt --provider preview
python -m memoryrush.cli process data/sample_docs/reading_memory_example.txt --provider ollama --model qwen3:8b
python -m memoryrush.cli memories
python -m pytest -q
```

`scripts/smoke_local.py` is an optional real-model check against the default llama.cpp endpoint, using synthetic reading and a separate verification database. It is not part of the offline tests.

## Privacy and limits

Data defaults to `%LOCALAPPDATA%/MemoryRush` on Windows and `~/.local/share/MemoryRush` elsewhere. `MEMORYRUSH_DATA_DIR` overrides it; avoid cloud-synced directories. The database is not encrypted. API keys are not saved to the database or processing exports. `.env.example` documents optional settings; the app does not automatically load `.env`.

External APIs can receive articles, interests, candidate memories, questions, and recent conversation; a single action may make multiple billable calls. There is no automatic cloud fallback. The API adapter has mocked end-to-end coverage, but no real third-party paid-credential verification. Local Qwen integration was checked separately on synthetic input.

Scores and decay are engineering heuristics, not calibrated truth probabilities or demonstrated human-memory gains. Citation matching does not establish semantic correctness. Recall scans enabled memories in batches; large banks may be slow. No PDF/OCR, web ingestion, native Anthropic Messages, Responses-only integration, or token streaming is included.

Keep keys, private articles, histories, databases, model weights, verification traces, and local environments out of Git. Historical concept/research plans in `docs/` and `tasks/` remain earlier design notes, not claims of implemented or validated experiments.
