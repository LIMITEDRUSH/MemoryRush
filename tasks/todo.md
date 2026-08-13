# MemoryRush Research Tasks

Chinese version: [todo_CN.md](todo_CN.md)

## Task 0: Research Reframing

**Description:** Replace the previous product-style MVP plan with a research-oriented specification and ordered execution plan.

**Acceptance criteria:**
- [x] `docs/RESEARCH_SPEC.md` exists.
- [x] `docs/RESEARCH_PLAN.md` exists.
- [x] `tasks/plan.md` and `tasks/todo.md` reflect the research sequence.

**Verification:**
- [ ] Human review confirms the new direction.

**Dependencies:** None

**Files likely touched:**
- `docs/RESEARCH_SPEC.md`
- `docs/RESEARCH_PLAN.md`
- `tasks/plan.md`
- `tasks/todo.md`

**Estimated scope:** Small: documentation only

## Task 1: Finalize Source Document Contracts

**Description:** Define the minimal source document and paragraph fields needed for evidence-grounded memory extraction.

**Acceptance criteria:**
- [x] Document contract includes ID, title, source path or source label, document type, and paragraphs.
- [x] Paragraph contract includes stable ID, text, position, and source reference.
- [x] Contract names match the research spec or a documented compatibility reason exists.

**Verification:**
- [ ] Existing parser tests pass. Pending: `pytest` is not installed in the active environment.
- [x] Manual review against `docs/RESEARCH_SPEC.md`.

**Dependencies:** Task 0

**Files likely touched:**
- `memoryrush/domain/`
- `tests/`

**Estimated scope:** Small: 1-2 files

## Task 2: Verify TXT/Markdown Parsing

**Description:** Ensure TXT and Markdown inputs produce stable ordered paragraphs suitable for evidence references.

**Acceptance criteria:**
- [x] `.txt`, `.md`, and `.markdown` inputs are supported.
- [x] Unsupported suffixes fail clearly.
- [x] Paragraph IDs are stable for unchanged content.
- [x] Markdown H1 title extraction is covered by tests.

**Verification:**
- [x] `python scripts/parse_docs.py data/sample_docs`
- [ ] `python -m pytest tests/test_text_parser.py`. Pending: `pytest` is not installed in the active environment.

**Dependencies:** Task 1

**Files likely touched:**
- `memoryrush/ingestion/`
- `scripts/parse_docs.py`
- `tests/test_text_parser.py`

**Estimated scope:** Small to Medium: 2-3 files

## Task 3: Define Structured Memory Output Contracts

**Description:** Create typed contracts for summary, core ideas, evidence spans, memory units, recall questions, and processing runs.

**Acceptance criteria:**
- [x] Every memory unit requires at least one evidence paragraph ID.
- [x] Confidence and salience scores are bounded.
- [x] Recall questions link to a memory unit.
- [x] Processing run metadata can store prompt version and model name.

**Verification:**
- [x] Contract unit tests instantiate valid examples.
- [x] Invalid examples fail validation.

**Dependencies:** Task 2

**Files likely touched:**
- `memoryrush/pipeline/`
- `tests/pipeline/`

**Estimated scope:** Medium: 3-5 files

## Task 4: Add Evidence Validation

**Description:** Validate that generated evidence references point to real source paragraphs and that outputs are not empty or duplicated.

**Acceptance criteria:**
- [x] Unknown paragraph IDs are reported as validation issues.
- [x] Empty memory units are rejected.
- [x] Duplicate memory units are flagged.
- [x] Validation output is inspectable by tests and scripts.

**Verification:**
- [ ] `python -m pytest tests/pipeline`. Pending: `pytest` is not installed in the active environment.

**Dependencies:** Task 3

**Files likely touched:**
- `memoryrush/pipeline/`
- `tests/pipeline/`

**Estimated scope:** Medium: 2-4 files

## Task 5: Build Fake-Provider Pipeline Test

**Description:** Connect parsing, provider output, validation, and artifact generation with a deterministic fake provider.

**Acceptance criteria:**
- [x] One sample article flows through the pipeline without a live model.
- [x] Valid fake output produces a valid artifact.
- [x] Invalid fake output produces validation issues.

**Verification:**
- [ ] `python -m pytest tests/pipeline`. Pending: `pytest` is not installed in the active environment.
- [x] `python -m compileall memoryrush scripts app tests`

**Dependencies:** Task 4

**Files likely touched:**
- `memoryrush/pipeline/`
- `memoryrush/providers/`
- `tests/pipeline/`

**Estimated scope:** Medium: 3-5 files

## Task 6: Add Local LLM Provider Interface

**Description:** Add a provider interface and an Ollama adapter without putting provider details into domain or UI code.

**Acceptance criteria:**
- [x] Provider interface accepts prompt/context and returns structured text or JSON.
- [x] Ollama adapter handles missing service/model errors clearly.
- [x] Tests can use the fake provider without importing Ollama-specific code.

**Verification:**
- [x] Provider unit tests.
- [x] Manual Ollama smoke test when model is installed.

**Dependencies:** Task 5

**Files likely touched:**
- `memoryrush/providers/`
- `tests/providers/`

**Estimated scope:** Medium: 3-5 files

## Task 7: Create Versioned Memory Extraction Prompt

**Description:** Write the first prompt template for article-to-memory extraction and keep it outside UI code.

**Acceptance criteria:**
- [x] Prompt asks for summary, core ideas, memory units, evidence IDs, and recall questions.
- [x] Prompt version is stored with processing results.
- [x] Prompt explicitly requires evidence paragraph IDs from the source context.

**Verification:**
- [x] Manual prompt review.
- [x] Fake-provider or prompt-rendering test.

**Dependencies:** Task 6

**Files likely touched:**
- `memoryrush/prompts/`
- `memoryrush/pipeline/`
- `tests/pipeline/`

**Estimated scope:** Small to Medium: 2-3 files

## Task 8: Save First Local Model Run Artifact

**Description:** Process one safe sample article through the local model and save an inspectable artifact.

**Acceptance criteria:**
- [x] Artifact includes input document ID, prompt version, model name, raw output, parsed output, and validation status with the fake provider.
- [x] No private data is used.
- [x] Real local-model failure modes and validation limitations are recorded.

**Verification:**
- [x] `ollama pull qwen3:8b`
- [x] `python scripts/process_article.py data/sample_docs/reading_memory_example.txt --provider ollama --model qwen3:8b --output data/processed/qwen3_8b_article_memory_artifact.json`
- [x] `python scripts/process_article.py data/sample_docs/reading_memory_example.txt --provider fake`

**Dependencies:** Task 7

**Files likely touched:**
- `scripts/process_article.py`
- `memoryrush/pipeline/`
- `data/processed/` ignored artifact output

**Estimated scope:** Medium: 3-5 files

## Task 9: Define Annotation Schema

**Description:** Define the JSONL format for benchmark labels used to evaluate salience and evidence grounding.

**Acceptance criteria:**
- [ ] Schema includes document ID, paragraph ID, salience label, expected memory idea, and evidence reference.
- [ ] Schema supports high, medium, and low salience labels.
- [ ] Example annotation file contains no private data.

**Verification:**
- [ ] Annotation schema check script or focused test.

**Dependencies:** Task 5

**Files likely touched:**
- `docs/`
- `data/annotations/`
- `tests/evaluation/`

**Estimated scope:** Small to Medium: 2-4 files

## Task 10: Create First Benchmark

**Description:** Build a small benchmark of 10-20 safe articles with salience labels and expected memory units.

**Acceptance criteria:**
- [ ] Each benchmark document has parsed source paragraphs.
- [ ] Each document has at least a few high-salience labels.
- [ ] Labeling guidelines are written.

**Verification:**
- [ ] Benchmark loader can read every example.
- [ ] Manual review for privacy/copyright risk.

**Dependencies:** Task 9

**Files likely touched:**
- `data/annotations/`
- `docs/`
- `memoryrush/evaluation/`

**Estimated scope:** Medium: data and docs

## Task 11: Add Evaluation Metrics

**Description:** Measure schema validity, evidence validity, salience ranking quality, duplicate rate, and recall-question answerability.

**Acceptance criteria:**
- [ ] Evaluation runs from a single command.
- [ ] Results are written to an inspectable file.
- [ ] Metrics are documented with limitations.

**Verification:**
- [ ] `python scripts/evaluate_memory_units.py data/annotations`

**Dependencies:** Task 10

**Files likely touched:**
- `memoryrush/evaluation/`
- `scripts/evaluate_memory_units.py`
- `tests/evaluation/`

**Estimated scope:** Medium: 3-5 files

## Task 12: Add Simple Baselines

**Description:** Compare MemoryRush output with simpler methods before making claims.

**Acceptance criteria:**
- [ ] Summary-only baseline exists.
- [ ] Position or TF-IDF salience baseline exists.
- [ ] Results table compares at least two baselines with MemoryRush.

**Verification:**
- [ ] `python scripts/run_baselines.py data/annotations`
- [ ] `python scripts/evaluate_memory_units.py data/annotations`

**Dependencies:** Task 11

**Files likely touched:**
- `memoryrush/evaluation/`
- `scripts/run_baselines.py`
- `tests/evaluation/`

**Estimated scope:** Medium: 3-5 files

## Task 13: Add Local Review UI

**Description:** Add a Streamlit review interface after the pipeline and evaluation path are working.

**Acceptance criteria:**
- [ ] User can inspect source paragraphs, memory units, evidence, and recall questions.
- [ ] User can accept, edit, or reject memory units.
- [ ] UI calls application/pipeline code rather than owning logic.

**Verification:**
- [ ] `streamlit run app/streamlit_app.py`
- [ ] Manual review flow check.

**Dependencies:** Task 8

**Files likely touched:**
- `app/`
- `memoryrush/application/`
- `memoryrush/storage/`

**Estimated scope:** Medium: 3-5 files

## Task 14: Persist Review Decisions

**Description:** Store accept/edit/reject decisions so they can become evaluation and personalization signals.

**Acceptance criteria:**
- [ ] Decisions survive process restart.
- [ ] Edited memory units retain original evidence.
- [ ] Accepted and rejected items are distinguishable.

**Verification:**
- [ ] Storage tests with temporary files or temporary SQLite database.

**Dependencies:** Task 13

**Files likely touched:**
- `memoryrush/storage/`
- `tests/storage/`

**Estimated scope:** Medium: 3-5 files

## Task 15: Add Retrieval Comparisons

**Description:** Compare recall quality across raw chunks, summaries, and memory units.

**Acceptance criteria:**
- [ ] Chunk-based retrieval baseline exists.
- [ ] Summary-only retrieval baseline exists.
- [ ] Memory-unit retrieval can be evaluated with the same queries.

**Verification:**
- [ ] `python scripts/evaluate_recall.py data/annotations`

**Dependencies:** Task 12

**Files likely touched:**
- `memoryrush/evaluation/`
- `memoryrush/retrieval/`
- `scripts/evaluate_recall.py`
- `tests/evaluation/`

**Estimated scope:** Medium: 4-5 files

## Task 16: Add Dynamic Memory Experiment

**Description:** Add reinforcement and decay only after recall events exist, then evaluate it as an ablation.

**Acceptance criteria:**
- [ ] Recall events are logged.
- [ ] Static and dynamic memory rankings can be compared.
- [ ] Dynamic scoring does not replace source-grounded evaluation.

**Verification:**
- [ ] Dynamic-memory unit tests.
- [ ] Retrieval ablation result file.

**Dependencies:** Task 15

**Files likely touched:**
- `memoryrush/domain/`
- `memoryrush/retrieval/`
- `memoryrush/evaluation/`
- `tests/`

**Estimated scope:** Medium: 4-5 files
