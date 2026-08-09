# MemoryRush Product Definition

> Historical note: this document is kept for context. The current planning source of truth is `docs/RESEARCH_SPEC.md`.

## Assumptions

1. The first version is for one local user, not a multi-user SaaS product.
2. The initial user is a student, researcher, or builder reading technical articles and wanting reusable knowledge.
3. The MVP should validate one question: can MemoryRush turn an article into knowledge the user actually wants to remember?
4. The MVP should not try to be a full note-taking system, flashcard platform, PDF chatbot, or personal knowledge base.
5. Local-first operation matters because user reading material may be private.

## Problem

People often read useful articles but fail to retain the few ideas that matter later. Existing tools usually help with one narrow part of the workflow:

- AI summarizers compress content, but often produce generic summaries.
- Note-taking apps store notes, but do not decide what is worth remembering.
- Flashcard apps support review, but require users to manually convert reading into cards.
- Highlighting tools preserve passages, but do not explain why they matter or how to recall them later.

MemoryRush should bridge that gap by turning an article into source-grounded memory material: important ideas, evidence, explanations, and recall questions.

## Initial Target User

The first target user is an individual learner who regularly reads long-form technical or educational content and wants to retain reusable concepts.

Examples:

- A student reading AI/ML papers, blog posts, or course notes.
- A developer reading technical articles and design docs.
- A researcher building a personal literature memory.

This user values:

- accurate source grounding
- concise structured output
- control over what is saved
- review material that can be reused later
- privacy and low cost

## Core User Journey

1. User submits one article as pasted text, TXT, or Markdown.
2. MemoryRush parses and normalizes the article.
3. MemoryRush identifies the most important ideas.
4. MemoryRush generates structured memory output with source evidence.
5. User reviews, edits, accepts, or rejects generated items.
6. Accepted items become memory units.
7. MemoryRush generates recall questions for later review.

## Differentiation

| Alternative | What it does | MemoryRush difference |
|---|---|---|
| AI summarizer | Produces a compressed summary | Focuses on what should be remembered and why, with evidence. |
| Note-taking app | Stores user-written notes | Generates structured memory candidates from articles. |
| Flashcard app | Reviews manually created cards | Creates recall questions from source-grounded memory units. |
| Readwise-like tool | Saves highlights | Turns highlights and article content into structured memory material. |
| Standard RAG chatbot | Answers questions over chunks | Builds durable memory units and review material after reading. |

## MVP Feature Set

The MVP should include only what is needed to test whether the product idea works.

Required:

- Submit one article through paste, TXT, or Markdown.
- Parse the article into source paragraphs.
- Generate a short summary.
- Identify 3-7 core ideas.
- Create memory units with evidence from the source.
- Generate recall questions for the memory units.
- Let the user accept, edit, or reject memory units.
- Store accepted memory units locally.
- Display the article, generated output, and saved memory units in a simple UI.

Optional if easy:

- Basic keyword search over saved memory units.
- Export memory units as JSON or Markdown.

## Not in MVP

- Multi-user accounts.
- Authentication.
- Browser extension.
- Mobile app.
- Cloud sync.
- PDF/DOCX parsing.
- Large-scale vector database.
- Graph database.
- Spaced repetition scheduler.
- Complex knowledge graph UI.
- Training a custom model.
- Full RAG chat over many documents.

## Major Assumptions to Validate

| Assumption | Validation method |
|---|---|
| Users prefer structured memory units over a plain summary. | Compare user ratings for summary-only vs memory-unit output. |
| The system can select important information reliably. | Human label top ideas and measure Precision@K / NDCG@K. |
| Source evidence increases user trust. | Ask users to rate trust with and without evidence snippets. |
| Recall questions are useful enough to keep. | User accept/reject rate and usefulness rating. |
| Local models are good enough for MVP output quality. | Compare local LLM output to a small manually reviewed sample. |

## Product Risks

| Risk | Why it matters | Mitigation |
|---|---|---|
| Summarization becomes generic | The product would look like a normal AI summarizer. | Keep summary short; make memory units, evidence, and recall questions the main output. |
| Hallucination | False memory units would damage trust. | Require evidence paragraph IDs and source quotes for every memory unit. |
| Selecting unimportant information | The product fails if saved items are not worth remembering. | Limit output to 3-7 memory units and evaluate importance selection with human labels. |
| Producing too much output | Users will not review or trust large generated dumps. | Use a strict output budget and require user accept/edit/reject. |
| Poor differentiation from ChatGPT | Users can already paste articles into ChatGPT. | Focus on structured memory units, recall questions, local storage, and review flow. |
| Long article processing | Local models may be slow or lose context. | Start with moderate-length articles; add chunked processing only when needed. |
| Cost | API-based workflows can become expensive. | MVP should support local Ollama first; API providers can remain optional. |
| Evaluation difficulty | Without measurement, product claims stay subjective. | Create a 10-20 article benchmark early and track acceptance/usefulness. |
| User trust | Users need to verify why an item was saved. | Show evidence next to every core idea and memory unit. |

## Success Criteria

The MVP succeeds if, for a small benchmark of 10-20 articles:

- Users accept at least half of generated memory units without major edits.
- Each accepted memory unit has clear source evidence.
- Generated recall questions are judged useful for most accepted memory units.
- The system produces less noise than a generic summary-only workflow.
