# MemoryRush

MemoryRush is a local research prototype for extracting source-grounded memory points from long-form reading material.

The project focuses on a narrow question: after reading an article, can a system identify the few ideas worth keeping, attach each idea to source evidence, and evaluate whether those memory points are useful for later recall?

Chinese README: [README_CN.md](README_CN.md)

## Current Scope

The first version is intentionally small:

- parse TXT and Markdown articles into stable paragraphs;
- generate structured summaries, core ideas, memory units, evidence links, and recall questions;
- validate that generated memory units point back to source paragraphs;
- build a small annotated benchmark;
- compare against simple baselines such as summary-only and chunk-based retrieval.

This repository is not planned as a SaaS product, note-taking platform, browser extension, or commercial reading app.

## Documentation

| Document | English | Chinese |
|---|---|---|
| Research specification | [docs/RESEARCH_SPEC.md](docs/RESEARCH_SPEC.md) | [docs/RESEARCH_SPEC_CN.md](docs/RESEARCH_SPEC_CN.md) |
| Research plan | [docs/RESEARCH_PLAN.md](docs/RESEARCH_PLAN.md) | [docs/RESEARCH_PLAN_CN.md](docs/RESEARCH_PLAN_CN.md) |
| Implementation plan | [tasks/plan.md](tasks/plan.md) | [tasks/plan_CN.md](tasks/plan_CN.md) |
| Task list | [tasks/todo.md](tasks/todo.md) | [tasks/todo_CN.md](tasks/todo_CN.md) |

Original concept notes are kept under `docs/MemoryPoint_*`.

## Quickstart

Recommended Python version: `3.10` to `3.12`.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/check_setup.py
python -m memoryrush.cli samples
streamlit run app/streamlit_app.py
```

Optional local model for later extraction experiments:

```powershell
ollama pull qwen2.5:7b-instruct
```

## Project Direction

The planned pipeline is:

```text
article
-> stable source paragraphs
-> structured memory candidates
-> evidence validation
-> reviewable artifacts
-> benchmark evaluation
-> baseline comparison
```

The first implementation task is to finalize the source-document and paragraph contracts, because every memory unit, citation, annotation, and evaluation result depends on stable source references.

## Privacy

Do not commit private documents, personal reading logs, API keys, local model caches, or generated personal memory databases. Use safe sample documents and synthetic data for public examples.
