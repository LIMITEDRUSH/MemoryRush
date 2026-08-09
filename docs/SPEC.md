# Spec: MemoryRush MVP

> Historical note: this document is kept for context. The current planning source of truth is `docs/RESEARCH_SPEC.md`.

## Objective

Build a local-first MVP that turns one article into structured, source-grounded memory material.

The MVP should answer:

```text
Can MemoryRush reliably turn an article into useful knowledge that a user actually wants to remember?
```

## MVP User Flow

1. User submits an article by pasting text or selecting a TXT/Markdown file.
2. System parses the article into paragraphs with stable source IDs.
3. System runs an AI processing pipeline.
4. System outputs:
   - short summary
   - core ideas
   - memory units
   - evidence snippets
   - recall questions
5. User reviews each memory unit.
6. User accepts, edits, or rejects each memory unit.
7. Accepted memory units are stored locally.
8. User can view saved memory units.

## Minimum AI Output Structure

The MVP output should be small and reviewable.

```json
{
  "summary": "Short article summary.",
  "core_ideas": [
    {
      "idea": "One important idea from the article.",
      "why_it_matters": "Why this idea is worth remembering.",
      "evidence": {
        "paragraph_id": "p_003",
        "quote": "Source text supporting the idea."
      }
    }
  ],
  "memory_units": [
    {
      "content": "A durable memory statement.",
      "memory_type": "conceptual_insight",
      "evidence_paragraph_ids": ["p_003"],
      "tags": ["retrieval", "RAG"],
      "confidence": 0.82
    }
  ],
  "recall_questions": [
    {
      "question": "What causes many RAG hallucinations?",
      "expected_answer": "Retrieval failures that leave the model without relevant evidence.",
      "memory_unit_index": 0
    }
  ]
}
```

Do not include relationship graphs, spaced repetition schedules, advanced personalization, or multi-document recall in the first MVP output.

## Functional Requirements

### Article Input

- Accept pasted text.
- Accept `.txt` files.
- Accept `.md` / `.markdown` files.
- Reject unsupported file types with a clear message.

### Parsing

- Preserve source path or source label.
- Split article into ordered paragraphs.
- Assign stable paragraph IDs.
- Extract Markdown H1 as title when present.

### AI Processing

- Generate one concise summary.
- Generate 3-7 core ideas.
- Generate one memory unit per accepted core idea candidate.
- Require evidence for every generated memory unit.
- Generate 1-2 recall questions per memory unit.

### Review

- Display memory units with evidence.
- Allow accept, edit, and reject.
- Save accepted memory units.

### Storage

- Store data locally.
- MVP may start with SQLite or JSONL, but storage must preserve:
  - article metadata
  - paragraphs
  - memory units
  - evidence references
  - recall questions
  - review status

### Display

- Show article title and paragraphs.
- Show summary.
- Show generated memory units.
- Show evidence snippets.
- Show recall questions.
- Show saved memory units.

## Non-Functional Requirements

- Runs locally.
- No authentication in MVP.
- No network requirement except local Ollama if a local LLM is used.
- Clear error messages when dependencies or models are missing.
- Source evidence must be visible to the user.
- Generated output should be deterministic enough for tests when fake providers are used.

## Tech Stack

- Language: Python `>=3.10,<3.14`
- UI: Streamlit
- Storage: SQLite for durable MVP state; JSONL acceptable for early pipeline outputs
- Local LLM: Ollama
- Embeddings: sentence-transformers in later retrieval phases
- Tests: pytest

## Commands

```powershell
python scripts/check_setup.py
python -m memoryrush.cli health
python -m memoryrush.cli samples
python scripts/parse_docs.py data/sample_docs
python -m pytest
python -m compileall memoryrush scripts app tests
streamlit run app/streamlit_app.py
```

Setup:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
ollama pull qwen2.5:7b-instruct
```

## Project Structure

```text
memoryrush/
  domain/          Pure product entities and rules
  application/     Use cases such as process article and review memory
  pipeline/        Parsing, extraction, memory generation, recall-question generation
  providers/       LLM and embedding interfaces/adapters
  prompts/         Versioned prompt templates
  storage/         SQLite/JSONL repositories
  evaluation/      Metrics and benchmark runners
app/               Streamlit UI
scripts/           Local workflow scripts
tests/             Unit and integration tests
docs/              Product, spec, architecture, roadmap
data/sample_docs/  Safe sample documents
```

## Code Style

Use typed Python with small functions and explicit domain names.

```python
@dataclass(frozen=True)
class MemoryUnit:
    memory_id: str
    content: str
    evidence_paragraph_ids: list[str]
    tags: list[str]
    confidence: float
```

Rules:

- Domain models should not import Streamlit, SQLite, Ollama, or FAISS.
- UI code should call application use cases, not provider adapters directly.
- Prompt text should live in prompt files, not inside Streamlit pages.
- Scripts should be thin wrappers around reusable code.

## Testing Strategy

- Unit test parsing and domain serialization.
- Unit test deterministic pipeline stages with fake LLM providers.
- Unit test output validation for memory units and recall questions.
- Use temporary files/databases in tests.
- Treat live Ollama tests as optional manual checks.

## Boundaries

Always:

- Preserve evidence links from generated output back to source paragraphs.
- Keep AI provider logic behind interfaces.
- Keep the MVP small and reviewable.
- Run focused verification before committing implementation changes.

Ask first:

- Adding a database migration tool.
- Adding cloud services.
- Adding authentication.
- Adding new file formats beyond TXT/Markdown.
- Adding API-based LLM providers.

Never:

- Commit private documents, API keys, real reading logs, or model cache files.
- Claim evaluation improvements without reproducible metrics.
- Store prompts only in UI code.
- Let UI become the core business logic layer.

## Success Criteria

- A user can submit one TXT/Markdown article.
- The system returns a summary, 3-7 memory units, evidence, and recall questions.
- The user can accept/edit/reject memory units.
- Accepted memory units are saved locally.
- The output can be evaluated on a small benchmark.

## Open Questions

- Should the first durable store be SQLite immediately, or JSONL until the review flow is stable?
- Should the MVP use only Ollama, or include an optional OpenAI-compatible provider interface?
- Should recall questions be generated in the same LLM call as memory units or as a separate stage?
- What is the first benchmark size: 10, 20, or 50 articles?
