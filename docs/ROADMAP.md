# MemoryRush MVP Roadmap

> Historical note: this document is kept for context. The current execution plan is `docs/RESEARCH_PLAN.md` and `tasks/todo.md`.

This roadmap follows the planning-and-task-breakdown format: Phase -> Milestone -> Feature -> Task. Each task is intended to be independently testable.

## Phase 1: Product and Spec Foundation

### Milestone 1.1: MVP Definition

#### Feature: Product specification

##### Task 1: Finalize product definition

**Objective:** Define the problem, target user, MVP scope, exclusions, and assumptions.

**Dependencies:** None

**Expected output:** `docs/PRODUCT.md`

**Acceptance criteria:**
- Problem and target user are explicit.
- MVP and non-MVP features are separated.
- Differentiation from summarizers, notes, flashcards, Readwise-like tools, and RAG chat is explained.

**Verification method:** Manual review of `docs/PRODUCT.md`.

##### Task 2: Finalize MVP spec

**Objective:** Define exact functional requirements and output structure.

**Dependencies:** Task 1

**Expected output:** `docs/SPEC.md`

**Acceptance criteria:**
- End-to-end MVP user flow is defined.
- AI output schema is concrete.
- Success criteria are testable.

**Verification method:** Manual review of `docs/SPEC.md`.

## Phase 2: First Vertical Slice

### Milestone 2.1: Article Input to Structured Paragraphs

#### Feature: TXT/Markdown ingestion

##### Task 3: Parse one article into paragraphs

**Objective:** Convert TXT/Markdown input into an article with ordered paragraphs.

**Dependencies:** Task 2

**Expected output:** Parser and CLI output JSON.

**Acceptance criteria:**
- `.txt`, `.md`, and `.markdown` are supported.
- Unsupported file types fail clearly.
- Each paragraph has a stable ID and source reference.

**Verification method:**
- `python scripts/parse_docs.py data/sample_docs`
- parser unit tests

### Milestone 2.2: Structured Memory Output

#### Feature: Article memory generation

##### Task 4: Define pipeline contracts

**Objective:** Define typed inputs/outputs for summary, core ideas, memory units, evidence, and recall questions.

**Dependencies:** Task 3

**Expected output:** Pipeline contract module.

**Acceptance criteria:**
- Contracts match the output schema in `docs/SPEC.md`.
- Evidence references are required.
- Tests can instantiate valid and invalid examples.

**Verification method:** Contract unit tests.

##### Task 5: Add fake-provider pipeline test

**Objective:** Prove the pipeline shape before calling a real LLM.

**Dependencies:** Task 4

**Expected output:** Pipeline test using a fake LLM response.

**Acceptance criteria:**
- Fake output validates successfully.
- Missing evidence fails validation.
- No network/model dependency is required.

**Verification method:** `python -m pytest tests/pipeline`

##### Task 6: Add Ollama-backed generation

**Objective:** Generate MVP memory output using a local LLM.

**Dependencies:** Task 5

**Expected output:** Ollama provider and article processing script.

**Acceptance criteria:**
- User can process one sample article.
- Output includes summary, memory units, evidence, and recall questions.
- Model errors are shown clearly.

**Verification method:**
- `ollama pull qwen2.5:7b-instruct`
- `python scripts/process_article.py data/sample_docs/example.md`

## Phase 3: Review and Persistence

### Milestone 3.1: Local Memory Store

#### Feature: Review decisions and saved memory

##### Task 7: Add local persistence

**Objective:** Store articles, memory units, evidence, recall questions, and review decisions locally.

**Dependencies:** Task 6

**Expected output:** SQLite or JSONL persistence layer.

**Acceptance criteria:**
- Accepted memory units survive process restart.
- Evidence references are stored.
- Rejected memory units are not shown as saved memory.

**Verification method:** Storage tests with a temporary database or temp files.

##### Task 8: Add review UI

**Objective:** Let the user accept, edit, or reject generated memory units.

**Dependencies:** Task 7

**Expected output:** Streamlit review workflow.

**Acceptance criteria:**
- Generated output is visible.
- Accept/edit/reject controls work.
- Saved memory units can be viewed.

**Verification method:** Manual Streamlit check.

## Phase 4: Evaluation

### Milestone 4.1: Small Benchmark

#### Feature: Output quality measurement

##### Task 9: Create benchmark dataset

**Objective:** Build a small labeled set for early evaluation.

**Dependencies:** Task 8

**Expected output:** 10-20 article benchmark with expected important ideas.

**Acceptance criteria:**
- Each benchmark item has source article, expected core ideas, and evidence.
- Dataset format is documented.

**Verification method:** Dataset schema check.

##### Task 10: Add evaluation metrics

**Objective:** Measure whether output is useful and source-grounded.

**Dependencies:** Task 9

**Expected output:** Evaluation script and metrics.

**Acceptance criteria:**
- Reports coverage, redundancy, evidence coverage, and recall-question answerability.
- Results can be reproduced by a single command.

**Verification method:** `python scripts/evaluate.py --sample`

## Phase 5: MVP Polish

### Milestone 5.1: Demo Readiness

#### Feature: Usable local demo

##### Task 11: Clean README quickstart

**Objective:** Make setup and demo flow reproducible.

**Dependencies:** Task 10

**Expected output:** Updated README.

**Acceptance criteria:**
- Clean clone instructions work.
- Required local model is listed.
- Known limitations are explicit.

**Verification method:** Fresh environment smoke test.

##### Task 12: Add demo sample and screenshots

**Objective:** Make the project understandable quickly.

**Dependencies:** Task 11

**Expected output:** Sample article, sample generated output, and screenshots.

**Acceptance criteria:**
- Demo does not include private data.
- Screenshot reflects actual UI.
- Sample output includes evidence links.

**Verification method:** Manual review.

## First Five Implementation Tasks

1. Finalize `docs/PRODUCT.md`.
2. Finalize `docs/SPEC.md`.
3. Parse TXT/Markdown into paragraph-level article data.
4. Define pipeline output contracts.
5. Add fake-provider pipeline validation tests.

## Biggest Product Risk

The biggest risk is generic output: the system may produce plausible summaries and memory units that are not actually worth remembering. The mitigation is to keep output small, require source evidence, force user review, and evaluate importance selection on a small labeled benchmark early.
