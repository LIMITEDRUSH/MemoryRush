# MemoryRush Research Plan

Chinese version: [RESEARCH_PLAN_CN.md](RESEARCH_PLAN_CN.md)

## Overview

The project should proceed as a research prototype, not a broad application. The shortest useful path is:

```text
article -> stable paragraphs -> structured memory units -> validation -> small benchmark -> baseline comparison
```

Everything else should earn its place by helping answer the research questions in `docs/RESEARCH_SPEC.md`.

## Dependency Graph

```text
Research specification
  -> domain and schema contracts
    -> ingestion with stable paragraph IDs
      -> fake-provider pipeline validation
        -> local LLM extraction
          -> artifact storage
            -> small benchmark
              -> evaluation metrics
                -> baseline comparisons
                  -> UI/review workflow
                    -> retrieval and dynamic memory experiments
```

Implementation should follow this order because MemoryRush depends on evidence-linked outputs. If schemas and validation are weak, later UI, retrieval, and model training will only amplify noise.

## Major Decisions

| Decision | Choice | Reason |
|---|---|---|
| Project framing | Personal research prototype | The core value is validating memory-unit extraction and recall, not operating a broad app. |
| First interface | CLI/script first, Streamlit after pipeline | A UI is useful, but the research risk is extraction quality and evidence validity. |
| First data input | TXT/Markdown | These formats remove parser noise and let the first experiments focus on memory logic. |
| First AI method | Local LLM prompted extraction | It tests the representation quickly while preserving local-first operation. |
| First evaluation | 10-20 labeled articles | Small enough to create manually, large enough to expose failure modes. |
| Storage order | JSONL artifacts first, SQLite when review state matters | Early experiments need inspectable run outputs more than query features. |
| Retrieval order | Defer vector search until extraction is evaluated | Chunk retrieval is a baseline, not the unique first claim. |

## Phase 0: Reframing And Planning

**Goal:** Replace the product-style plan with a research-oriented specification and task sequence.

Deliverables:

- `docs/RESEARCH_SPEC.md`
- `docs/RESEARCH_PLAN.md`
- `tasks/plan.md`
- `tasks/todo.md`

Acceptance:

- Research questions are explicit.
- Commercial/product assumptions are removed from the active plan.
- First implementation task is small and testable.
- Deferred features are clearly named.

Verification:

```powershell
rg -n "pricing|subscription|monetization|customer growth|marketing|enterprise" docs tasks README.md
```

Commercial terms may appear only when explicitly listed as non-goals.

## Phase 1: Evidence-Preserving Article Representation

**Goal:** Make source text stable enough that later AI output can cite it.

Tasks:

- finalize or adjust `SourceDocument` and `SourceParagraph` contracts,
- parse TXT and Markdown,
- generate stable document and paragraph IDs,
- preserve title, source path, document type, and paragraph order,
- add parser tests.

Acceptance:

- sample TXT/Markdown files parse into ordered paragraphs,
- unsupported file types fail clearly,
- paragraph IDs are stable for the same source content,
- parsed output can be serialized.

Verification:

```powershell
python scripts/parse_docs.py data/sample_docs
python -m pytest tests/test_text_parser.py
```

## Phase 2: Structured Memory Output Contracts

**Goal:** Define exactly what generated memory output must look like before using a live model.

Tasks:

- define Pydantic models for summary, core ideas, evidence spans, memory units, recall questions, and processing runs,
- require every memory unit to cite paragraph IDs,
- validate confidence and salience score ranges,
- add invalid-output tests.

Acceptance:

- valid fake outputs pass validation,
- missing evidence fails,
- unknown paragraph IDs fail,
- duplicate or empty memory units are flagged.

Verification:

```powershell
python -m pytest tests/pipeline
python -m compileall memoryrush scripts app tests
```

## Phase 3: Fake-Provider End-To-End Pipeline

**Goal:** Prove the pipeline shape without model variability.

Tasks:

- create a provider interface,
- create a fake provider returning deterministic structured output,
- connect parse -> prompt context -> provider -> validation -> artifact output,
- write a single focused end-to-end test.

Acceptance:

- one sample article produces a validated artifact through the fake provider,
- tests do not require network or Ollama,
- validation issues are explicit and inspectable.

Verification:

```powershell
python -m pytest tests/pipeline
```

## Phase 4: Local LLM Extraction Prototype

**Goal:** Generate first real candidate memory units from a local model.

Tasks:

- add an Ollama adapter behind the provider interface,
- create `article_memory_v1` prompt,
- save prompt version, model name, and run metadata,
- process one sample article,
- inspect and record failure modes.

Acceptance:

- one sample article yields summary, memory units, evidence IDs, and recall questions,
- malformed model output is rejected or logged,
- no private data is required.

Verification:

```powershell
ollama pull qwen2.5:7b-instruct
python scripts/process_article.py data/sample_docs/reading_memory_example.txt
```

## Phase 5: Small Benchmark And Annotation Format

**Goal:** Create the first measurement target.

Tasks:

- define annotation JSONL schema,
- select 10-20 safe articles,
- label high-salience passages,
- record expected memory-unit ideas and evidence paragraph IDs,
- write a benchmark loader.

Acceptance:

- each benchmark example has a source document and labels,
- labels distinguish high, medium, and low salience where possible,
- benchmark files contain no private or copyrighted material that should not be committed.

Verification:

```powershell
python scripts/validate_annotations.py data/annotations
```

## Phase 6: Evaluation Metrics

**Goal:** Turn output inspection into reproducible numbers.

Tasks:

- compute schema pass rate,
- compute evidence-link validity,
- compute Precision@K and NDCG@K for salience,
- compute duplicate memory-unit rate,
- compute recall-question answerability proxy or manual review sheet.

Acceptance:

- evaluation can run from one command,
- metrics are written to a result file,
- limitations are documented next to the result.

Verification:

```powershell
python scripts/evaluate_memory_units.py data/annotations
```

## Phase 7: Baselines

**Goal:** Compare MemoryRush against simpler alternatives.

Tasks:

- implement summary-only baseline,
- implement first/last paragraph or section-position heuristic,
- implement TF-IDF salience baseline,
- compare LLM memory extraction against baselines.

Acceptance:

- every baseline produces the same comparable output format,
- results table includes MemoryRush and at least two simple baselines,
- no improvement is claimed without result files.

Verification:

```powershell
python scripts/run_baselines.py data/annotations
python scripts/evaluate_memory_units.py data/annotations
```

## Phase 8: Local Review UI

**Goal:** Add interaction only after the pipeline and evaluation loop are credible.

Tasks:

- add Streamlit page for one article,
- show source paragraphs, memory units, evidence, and recall questions,
- support manual accept/edit/reject,
- persist review decisions.

Acceptance:

- UI does not own pipeline logic,
- accepted/rejected decisions are saved,
- evidence remains visible during review.

Verification:

```powershell
streamlit run app/streamlit_app.py
```

## Phase 9: Retrieval And Dynamic Memory Experiments

**Goal:** Return to the original long-term memory idea with enough foundation to test it.

Tasks:

- add chunk retrieval baseline,
- add memory-unit retrieval,
- compare retrieval over chunks, summaries, and memory units,
- add highlight signal if review data exists,
- add reinforcement/decay only after retrieval logs exist.

Acceptance:

- retrieval experiments compare at least two representations,
- dynamic scoring has an ablation,
- citation correctness is measured.

Verification:

```powershell
python scripts/evaluate_recall.py data/annotations
```

## Phase 10: Report And Repository Polish

**Goal:** Make the research result legible.

Tasks:

- write a concise technical report,
- include method, data, metrics, results, error analysis, and limitations,
- update README with real results,
- add screenshots only after the UI reflects real behavior.

Acceptance:

- project claims match measured results,
- setup commands work,
- repository contains no private data or secrets.

Verification:

```powershell
python scripts/check_setup.py
python -m pytest
```

## Estimated Timeline

Assuming focused solo work:

| Target | Scope | Estimate |
|---|---|---:|
| First validated extraction slice | Phases 1-4 | 1-2 weeks |
| Small evaluation prototype | Phases 1-6 | 3-5 weeks |
| Strong research project | Phases 1-8 | 6-9 weeks |
| Full research version with retrieval/dynamic memory/report | Phases 1-10 | 10-14 weeks |

The main uncertainty is not writing code; it is annotation quality and evaluation design.

## First Implementation Task

Start with `Task 1` in `tasks/todo.md`: finalize the source-document and paragraph contracts against the current parser.

This is the correct first task because every later memory unit, evidence span, benchmark label, and citation depends on stable paragraph identity.
