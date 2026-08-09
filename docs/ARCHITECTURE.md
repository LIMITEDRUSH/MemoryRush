# MemoryRush MVP Architecture

> Historical note: this document is kept for context. The current architecture direction is summarized in `docs/RESEARCH_SPEC.md` and `docs/RESEARCH_PLAN.md`.

## Architecture Principles

- Build a modular monolith.
- Optimize for one developer and fast iteration.
- Keep product logic separate from Streamlit.
- Keep domain models separate from infrastructure.
- Keep LLM provider logic behind interfaces.
- Make every generated memory unit source-grounded.
- Make evaluation possible from the beginning.

## System Overview

```text
Streamlit UI / CLI
  -> application use cases
    -> domain models
    -> AI pipeline
      -> prompt templates
      -> LLM provider interface
    -> storage repositories
    -> evaluation helpers
```

The MVP does not need a separate backend server. Streamlit can call application services directly.

## Technical Choices

| Area | MVP choice | Justification |
|---|---|---|
| Frontend | Streamlit | Fastest path to a local review UI for one developer. |
| Backend | No separate server initially | Avoids unnecessary API surface; Streamlit calls application services directly. |
| Language | Python | Best fit for local LLM, embeddings, evaluation, and quick iteration. |
| Database | SQLite | Simple durable local storage with no server setup. |
| Authentication | None for MVP | Single local user; auth would not validate the core product idea. |
| Article ingestion | Pasted text, TXT, Markdown | Keeps input reliable before adding PDF/DOCX/URL complexity. |
| LLM abstraction | Provider interface with Ollama first | Allows local-first operation while preserving future API support. |
| Background processing | Synchronous first | Simpler debugging; add jobs only when processing time becomes painful. |
| Deployment | Local development | Privacy, low cost, and faster iteration. |

## Domain Model

| Entity | Responsibility |
|---|---|
| `Article` | User-submitted source content and metadata. |
| `ArticleParagraph` | Ordered source paragraph with stable ID. |
| `ProcessingRun` | One attempt to process an article through the AI pipeline. |
| `Summary` | Short source-grounded article summary. |
| `CoreIdea` | Important idea detected from the article. |
| `Evidence` | Source paragraph reference and quote supporting an output. |
| `MemoryUnit` | Durable statement the user may want to remember. |
| `RecallQuestion` | Question generated to help the user review a memory unit. |
| `ReviewDecision` | User decision: accepted, edited, rejected. |

Deferred until after MVP:

- `User`: single local user is enough first.
- `DocumentChunk`: needed when retrieval over many documents starts.
- `Relationship`: useful later for cross-document support/conflict links.
- `MemoryState`: useful later for reinforcement and decay.

## MVP Data Flow

```text
Article input
-> parse paragraphs
-> run AI processing
-> validate structured output
-> display summary / memory units / recall questions
-> user review
-> persist accepted memory units
-> evaluate output quality
```

## AI Pipeline

| Stage | Purpose | Input | Output | LLM required | Evaluation |
|---|---|---|---|---|---|
| Parse | Convert file/text into paragraphs | file/text | `Article`, `ArticleParagraph[]` | No | paragraph count, metadata preservation |
| Understand | Identify article topic and claims | paragraphs | short notes/themes | Yes | human review |
| Select importance | Choose important ideas | paragraphs + themes | `CoreIdea[]` | Yes first, later ML | Precision@K, NDCG@K |
| Generate memory units | Convert ideas into durable statements | core ideas + evidence | `MemoryUnit[]` | Yes | usefulness, factuality |
| Generate recall questions | Create review material | memory units | `RecallQuestion[]` | Yes | answerability, usefulness |
| Validate | Check schemas and evidence links | generated output | accepted/rejected structured output | No | schema pass rate |
| Persist | Save reviewed output | review decisions | local records | No | CRUD tests |

The MVP should use fewer stages if implementation becomes too slow, but it should not merge prompts, provider calls, persistence, and UI into one file.

## Repository Structure

```text
memoryrush/
  domain/
    models.py
  application/
    process_article.py
    review_memory.py
  pipeline/
    contracts.py
    article_memory_pipeline.py
    validators.py
  prompts/
    article_memory_v1.md
    recall_questions_v1.md
  providers/
    llm.py
    ollama.py
  storage/
    sqlite.py
    repositories.py
  evaluation/
    metrics.py
    dataset.py
  ingestion/
    text_parser.py
  cli.py
app/
  streamlit_app.py
scripts/
  parse_docs.py
  process_article.py
tests/
  domain/
  pipeline/
  application/
  storage/
  evaluation/
docs/
data/
  sample_docs/
  annotations/
```

## Module Responsibilities

| Module | Responsibility |
|---|---|
| `domain` | Pure entities and rules. |
| `application` | Coordinates use cases such as processing an article. |
| `pipeline` | Defines AI processing stages and structured output validation. |
| `prompts` | Stores versioned prompts. |
| `providers` | Isolates Ollama and future LLM providers. |
| `storage` | Persists articles, memory units, decisions, and questions. |
| `evaluation` | Measures output quality and benchmark results. |
| `ingestion` | Reads TXT/Markdown and later other formats. |
| `app` | Streamlit presentation layer only. |
| `scripts` | Thin local workflow commands. |

## Dependency Rules

- `domain` depends on nothing inside the app.
- `application` may depend on `domain`, `pipeline`, `storage`, and provider interfaces.
- `pipeline` may depend on `domain`, prompts, and provider interfaces.
- `providers` may depend on external APIs/libraries, not on UI.
- `app` may depend on `application`, not direct LLM/storage internals.
- `evaluation` may read outputs from pipeline/storage, but production code should not depend on evaluation.

## Database Responsibilities

For MVP, SQLite should store:

- articles
- article paragraphs
- processing runs
- summaries
- core ideas
- evidence
- memory units
- recall questions
- review decisions

Indexes and vector search are deferred until multi-document recall becomes part of the active MVP.

## Prompt Strategy

- Store prompts under `memoryrush/prompts/`.
- Version prompt filenames, for example `article_memory_v1.md`.
- Require JSON output.
- Save prompt version in `ProcessingRun`.
- Validate LLM output before display or storage.

## Evaluation Strategy

Start with a small benchmark of 10-20 articles.

Automatic checks:

- schema validity
- evidence link coverage
- duplicate memory unit rate
- recall question answerability against source evidence

Human checks:

- summary usefulness
- importance selection quality
- memory unit usefulness
- factual accuracy
- recall question quality

## Testing Strategy

- Parser tests for TXT/Markdown.
- Domain tests for serialization and validation.
- Pipeline tests using fake LLM responses.
- Storage tests using temporary SQLite databases.
- Evaluation metric tests on tiny hand-built examples.
- Minimal Streamlit smoke/import test.

## MVP vs Future Architecture

MVP:

- local-first
- Streamlit
- TXT/Markdown
- one article at a time
- structured memory output
- local persistence
- small benchmark

Future:

- PDF/DOCX/URL ingestion
- multi-document recall
- embedding search
- memory strength and decay
- user profiles
- richer review scheduling
- optional cloud sync

## Known Trade-offs

- Streamlit is less flexible than a custom frontend, but much faster for MVP validation.
- SQLite is not a multi-user database, but fits local-first development.
- Local LLMs may produce lower-quality outputs than API models, but improve privacy and cost.
- Prompted extraction is not enough for final claims; evaluation must compare it to simpler baselines.
