# MemoryRush Research Specification

## Status

Draft source of truth for the next planning cycle. This document supersedes the earlier product-style MVP framing. Implementation should not start until this specification and `docs/RESEARCH_PLAN.md` are reviewed.

## Assumptions

1. MemoryRush is a personal, research-oriented AI/ML engineering project.
2. The first real user is the project author reading technical articles, papers, notes, and educational material.
3. The project should validate a memory and retrieval idea, not optimize for a business workflow.
4. Local-first execution is preferred because reading data may be private and because reproducibility matters.
5. A small, well-measured research prototype is more valuable than a broad feature surface.
6. The initial benchmark can be small, but it must be explicit, repeatable, and honest about limitations.

## Objective

MemoryRush studies whether an AI system can turn long-form reading into durable, source-grounded memory units that are more useful for later recall than generic summaries or plain chunk retrieval.

The central research question is:

```text
Can source-grounded memory units, selected by salience and refined by user feedback, improve long-term reading recall compared with summary-only and chunk-based retrieval baselines?
```

The project should produce:

- a local research prototype,
- a documented memory-unit schema,
- a small annotated benchmark,
- baseline comparisons,
- evaluation results,
- and a technical report or project write-up.

## What MemoryRush Is

MemoryRush is a local reading-memory research system. Given one article, it should parse the source, identify candidate ideas worth remembering, bind each memory unit to evidence, generate review questions, and preserve review decisions for later evaluation.

It is not merely:

- a document chatbot,
- a generic summarizer,
- a note-taking clone,
- a flashcard generator,
- or a vector-search demo.

The distinctive claim is that reading memory should be selective, evidence-linked, and measurable.

## Research Questions

### RQ1: Salience

Can MemoryRush select article passages or ideas that a human would judge worth remembering?

Early metric: Precision@K and NDCG@K against a small human-labeled benchmark.

### RQ2: Source Grounding

Can every generated memory unit be traced back to supporting source paragraphs?

Early metric: evidence coverage, invalid evidence-reference rate, and unsupported memory-unit rate.

### RQ3: Review Usefulness

Are generated memory units and recall questions useful enough for the author to accept or lightly edit?

Early metric: accept/edit/reject rate, usefulness rating, and duplicate/noise rate.

### RQ4: Retrieval Benefit

When asking later questions, do memory units improve recall quality compared with retrieving raw chunks or summaries?

Later metric: Precision@K, NDCG@K, citation correctness, and human preference on recall tasks.

### Deferred RQ: Dynamic Memory

Does reinforcement and decay improve long-term retrieval ranking over static memory storage?

This is important to the original idea, but it should come after the first memory-unit extraction and evaluation loop works.

## Scope

### First Research Slice

The first slice should process one TXT or Markdown article and produce a reviewable structured output:

- normalized article metadata,
- ordered source paragraphs,
- concise summary,
- 3-7 candidate core ideas,
- memory units,
- evidence references,
- recall questions,
- validation report.

The user can review the output manually at first. A full UI is useful later, but the first research slice should prove the pipeline and schema.

### Required For The First Validated Prototype

- TXT and Markdown ingestion.
- Stable paragraph IDs.
- Structured memory-unit schema.
- Fake-provider tests for deterministic validation.
- Local LLM provider path, preferably Ollama.
- Local output storage, initially JSONL or SQLite.
- 10-20 article benchmark with hand-labeled salient passages or expected memory units.
- Evaluation script for schema validity, evidence coverage, salience ranking, and duplicate rate.

### Deferred Until The Prototype Is Useful

- PDF, DOCX, URL ingestion.
- Multi-document recall.
- Embedding search and vector indexes.
- reinforcement and decay.
- highlight-driven personalization.
- graph relations between memories.
- custom model training.
- polished Streamlit workflow.

These are not rejected. They are sequenced after the first validated extraction and evaluation loop.

### Deliberately Out Of Scope

- account systems,
- payments,
- pricing,
- customer growth,
- marketing pages,
- organization administration,
- cloud sync as a default requirement,
- large deployment architecture,
- mobile apps,
- browser extensions,
- complex permissions,
- production observability.

Those topics do not help answer the current research questions.

## Technical Stack

### Chosen Stack

- Language: Python `>=3.10,<3.14`
- Data contracts: Pydantic for structured AI output validation
- CLI/scripts: Python scripts and `memoryrush.cli`
- Local UI: Streamlit, after the pipeline is stable
- Local LLM: Ollama first
- Storage: JSONL for early generated artifacts; SQLite when review state needs durable querying
- ML/evaluation: scikit-learn, pandas, numpy
- Embeddings later: sentence-transformers
- Vector search later: FAISS, only when retrieval experiments begin
- Tests: pytest

### Why This Stack

Python is the best fit because the project combines text processing, local LLM calls, ML baselines, evaluation scripts, and quick research iteration. Streamlit is appropriate only as a local research UI, not as the core system. Pydantic is justified because MemoryRush depends on validating structured AI outputs and rejecting unsupported memory units. SQLite is useful once review decisions and evaluation examples need durable relationships. FAISS and embedding models are deferred because the first unresolved problem is not retrieval speed; it is whether memory units are worth generating.

## Architecture Decision

Use a local modular monolith.

```text
CLI / Streamlit
  -> application workflows
    -> domain models
    -> ingestion
    -> memory extraction pipeline
      -> prompts
      -> provider interfaces
    -> validation
    -> local storage
    -> evaluation
```

### Alternatives Considered

| Option | Benefits | Problems For MemoryRush | Decision |
|---|---|---|---|
| Notebook-only prototype | Fastest research sketch | Hard to test, version, and reproduce | Use notebooks only for exploration, not core pipeline |
| Modular Python package | Testable, reusable, research-friendly | Slightly more setup than a notebook | Chosen |
| Separate backend and frontend | Cleaner app boundary later | Adds API and deployment work before research validation | Defer |
| Full RAG stack first | Familiar baseline | Delays the unique memory-unit question | Build only after extraction baseline |
| Custom ML model first | Stronger ML identity | Requires labels before knowing the schema works | Defer until benchmark exists |

## Domain Model

Initial entities:

| Entity | Purpose |
|---|---|
| `SourceDocument` | One submitted article with metadata. |
| `SourceParagraph` | Ordered paragraph with stable ID and source position. |
| `ProcessingRun` | One attempt to process a document with a given prompt/model/config. |
| `CoreIdea` | Candidate idea selected from the source. |
| `EvidenceSpan` | Source paragraph ID plus supporting quote. |
| `MemoryUnit` | Durable statement intended for later recall. |
| `RecallQuestion` | Question and expected answer linked to a memory unit. |
| `ValidationIssue` | Structured reason an output is rejected or needs review. |
| `ReviewDecision` | Manual accept/edit/reject decision. |
| `EvaluationExample` | Labeled benchmark example for salience and evidence checks. |

Deferred entities:

- `MemoryState` for reinforcement and decay.
- `Highlight` for explicit user feedback.
- `MemoryRelation` for support/conflict/extension links.
- `EmbeddingChunk` for retrieval baselines.

## Pipeline Contract

First validated pipeline:

```text
Input file/text
-> parse into SourceDocument + SourceParagraph[]
-> build prompt context
-> generate structured candidate output
-> validate schema and evidence links
-> write run artifact
-> compare against labels when available
```

Minimum structured output:

```json
{
  "summary": "Concise source-grounded article summary.",
  "core_ideas": [
    {
      "idea": "A specific idea worth remembering.",
      "why_it_matters": "Reason this idea may be useful later.",
      "evidence": {
        "paragraph_id": "p_003",
        "quote": "Exact or near-exact supporting source text."
      },
      "salience_score": 0.82
    }
  ],
  "memory_units": [
    {
      "content": "A durable memory statement.",
      "memory_type": "conceptual_insight",
      "evidence_paragraph_ids": ["p_003"],
      "tags": ["RAG", "retrieval"],
      "confidence": 0.78
    }
  ],
  "recall_questions": [
    {
      "question": "What is the remembered claim?",
      "expected_answer": "The answer supported by the memory unit.",
      "memory_unit_index": 0
    }
  ]
}
```

Validation must reject or flag:

- memory units without evidence paragraph IDs,
- evidence paragraph IDs not present in the source document,
- empty or duplicate memory units,
- unsupported quotes,
- malformed model output.

## AI/ML Approach

### Stage 1: Prompted Extraction Baseline

Start with local LLM extraction because it directly tests the memory-unit representation before collecting labels. The prompt must request structured JSON and evidence references.

### Stage 2: Heuristic And Summary Baselines

Add simple baselines early:

- summary-only memory,
- first/last paragraph heuristic,
- keyword or TF-IDF salience heuristic.

These prevent the project from overclaiming that an LLM pipeline is useful without comparison.

### Stage 3: Small Labeled Benchmark

Create 10-20 labeled articles before model training. Labels should identify high-salience passages and expected memory units.

### Stage 4: ML Ranking Baselines

Only after the benchmark exists:

- TF-IDF + Logistic Regression,
- Sentence-BERT + Logistic Regression,
- Sentence-BERT + MLP if enough labels exist,
- LLM scorer baseline,
- hybrid ranker combining salience, evidence quality, and later user feedback.

## Evaluation Strategy

### Early Evaluation

- schema pass rate,
- evidence reference validity,
- evidence quote support rate,
- duplicate memory-unit rate,
- memory unit count within target range,
- manual accept/edit/reject rate.

### Benchmark Evaluation

- Precision@K for high-salience passage selection,
- NDCG@K for salience ranking,
- Recall@K when labels are complete enough,
- citation correctness,
- unsupported memory-unit rate,
- recall-question answerability.

### Later Retrieval Evaluation

Compare:

- chunk-based retrieval,
- summary-only retrieval,
- static memory units,
- memory units with user feedback,
- memory units with reinforcement/decay.

Do not claim improvement until these results are produced by reproducible scripts.

## Commands

Expected commands as the project matures:

```powershell
python scripts/check_setup.py
python -m memoryrush.cli health
python -m memoryrush.cli samples
python scripts/parse_docs.py data/sample_docs
python -m pytest
python -m compileall memoryrush scripts app tests
streamlit run app/streamlit_app.py
```

Future research commands:

```powershell
python scripts/process_article.py data/sample_docs/reading_memory_example.txt
python scripts/evaluate_memory_units.py data/annotations
```

## Proposed Repository Structure

```text
memoryrush/
  domain/             Pure entities and validation-friendly models
  ingestion/          TXT/Markdown parsing first; richer parsers later
  pipeline/           Extraction orchestration and structured contracts
  prompts/            Versioned prompt templates
  providers/          LLM provider interfaces and Ollama adapter
  storage/            JSONL/SQLite persistence
  evaluation/         Benchmark loading and metrics
  cli.py              Thin command entry point
app/
  streamlit_app.py    Local research UI
scripts/
  check_setup.py
  parse_docs.py
  process_article.py
  evaluate_memory_units.py
tests/
  domain/
  ingestion/
  pipeline/
  evaluation/
docs/
  RESEARCH_SPEC.md
  RESEARCH_PLAN.md
data/
  sample_docs/
  annotations/
  processed/          Ignored generated artifacts
```

## Code Style

Keep the core explicit and boring. Domain and pipeline code should be typed, deterministic where possible, and easy to test with fake providers.

```python
class MemoryUnit(BaseModel):
    content: str
    memory_type: str
    evidence_paragraph_ids: list[str]
    tags: list[str] = []
    confidence: float = Field(ge=0.0, le=1.0)
```

Rules:

- Domain models do not import Streamlit, Ollama, SQLite, or FAISS.
- Provider adapters do not contain project logic.
- Prompts live in files and are versioned.
- Scripts call reusable package functions instead of owning core behavior.
- Tests use fake providers before live model checks.

## Boundaries

Always:

- preserve paragraph-level evidence links,
- validate structured AI output before saving it,
- keep generated artifacts separate from source data,
- make evaluation reproducible,
- keep the first implementation slice small.

Ask first:

- adding cloud dependencies,
- changing the benchmark scope,
- introducing a new major dependency,
- replacing the local-first assumption,
- expanding ingestion beyond TXT/Markdown in the first slice.

Never:

- commit private documents, reading logs, API keys, model caches, or generated personal memory databases,
- claim measured gains without an evaluation script and result files,
- build broad app features before the memory extraction loop is validated,
- treat summary quality alone as project success.

## Success Criteria For The Next Milestone

The next milestone is complete when:

- one TXT/Markdown article can be parsed into stable paragraphs,
- a fake provider can produce valid structured memory output,
- invalid evidence links are caught by tests,
- one local LLM run can produce reviewable output for a sample article,
- the output artifact records prompt/model/config metadata,
- and a 10-20 article benchmark format is defined.

## Open Questions

1. Should the first manual benchmark contain 10 articles for speed or 20 articles for more stable evaluation?
2. Should generated artifacts use JSONL until review state exists, or should SQLite be introduced immediately?
3. Which local model should be the default: `qwen2.5:7b-instruct`, another Qwen model, or a Llama-family model available on the machine?
4. Should the project name stay MemoryRush while the concept name remains MemoryPoint, or should documentation standardize on one name?
