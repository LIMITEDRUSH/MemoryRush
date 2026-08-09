# MemoryPoint Research Roadmap

This document defines MemoryPoint as a complete retrieval and ranking project rather than a standard RAG application.

## Project Positioning

```text
MemoryPoint: Personalized Long-Term Reading Memory Retrieval with Salience Ranking and Dynamic Recall
```

The project should be framed as a personalized retrieval and ranking system for long-term reading memory. The strongest version combines:

- working product demo
- annotated dataset
- ML ranking baselines
- dynamic memory scoring
- RAG baseline comparisons
- ablation study
- technical report
- reproducible GitHub repo

## Research Questions

```text
RQ1: Can memory-point retrieval outperform standard chunk-based RAG for long-term reading recall?

RQ2: Can user highlights and recall history improve personalized memory ranking?

RQ3: Does reinforcement and decay improve retrieval quality over static memory storage?
```

## Required Deliverables

- Web demo with reading, highlighting, memory review, memory bank, and recall chat.
- Clean GitHub repository with reproducible setup.
- Around 100 annotated documents for reading-memory evaluation.
- TF-IDF, Sentence-BERT, MLP, LLM scorer, and hybrid MemoryRanker baselines.
- Comparisons against standard RAG, summary-only memory, static memory points, and ablated MemoryPoint variants.
- Metrics: Precision@K, Recall@K, NDCG@K, MRR, citation correctness, unsupported answer rate, and user preference.
- 6-8 page technical report.
- Screenshots and short demo video.
- Final project summary with measured results.

## Dataset Plan

Suggested scale:

```text
100 documents
800-3000 words per document
Topics: AI, ML, cognition, HCI, productivity
```

Each document should include:

- 3-5 high-salience memory points.
- 5-10 medium-salience passages.
- low-salience negative samples.
- source evidence spans.
- topic tags.
- memory type.
- highlight label.

Annotation schema:

```json
{
  "document_id": "doc_001",
  "passage_id": "p_014",
  "text": "...",
  "salience_label": "high",
  "memory_point": "...",
  "evidence_span": "...",
  "tags": ["RAG", "retrieval", "hallucination"],
  "memory_type": "conceptual_insight",
  "highlight_label": "important"
}
```

## Ranking Methods

| Method | Purpose |
|---|---|
| TF-IDF + Logistic Regression | classical baseline |
| Sentence-BERT + Logistic Regression | embedding baseline |
| Sentence-BERT + MLP | neural baseline |
| LLM scorer | prompt-based baseline |
| Hybrid MemoryRanker | final system |

Hybrid MemoryRanker:

```text
score =
0.25 * semantic_similarity
+ 0.20 * salience_score
+ 0.15 * user_highlight_signal
+ 0.15 * memory_strength
+ 0.10 * novelty
+ 0.10 * cross_document_connectivity
+ 0.05 * recency
```

## Evaluation Design

| System | Description |
|---|---|
| Standard RAG | only chunk retrieval |
| Summary Memory | retrieve from summaries |
| Static MemoryPoint | memory points without dynamic scoring |
| MemoryPoint - Highlight | no user highlight signal |
| MemoryPoint - Decay | no reinforcement/decay |
| Full MemoryPoint | complete system |

Primary metrics:

```text
Precision@5
Recall@5
NDCG@5
MRR
Citation correctness
Unsupported answer rate
User preference score
```

The key result should answer whether full MemoryPoint improves long-term reading recall over standard chunk-based RAG. Any improvement numbers must come from actual experiments.

## Product Demo Scope

The complete version should avoid unnecessary scope such as multi-user auth, browser plugins, mobile apps, or large production deployment.

Required pages:

1. **Reading Page**
   Upload an article, inspect source text, read the AI summary, and highlight passages.

2. **Memory Review Page**
   Review candidate memory points with `accept`, `edit`, and `reject`.

3. **Memory Bank**
   Browse long-term memories with score, strength, source, and recall history.

4. **Recall Chat**
   Ask questions about the current article and historical memory with citations.

## Development Roadmap

### Phase 1: Repository and Ingestion

- Python project structure.
- requirements, `.env.example`, sample data.
- PDF, TXT, Markdown, and pasted-text ingestion.
- paragraph, chunk, and metadata preservation.

### Phase 2: Baseline RAG

- chunking
- embeddings
- vector database
- standard RAG answers
- source citations

### Phase 3: Memory Point MVP

- article summary
- candidate memory point extraction
- evidence span binding
- SQLite memory storage

### Phase 4: Reading UI

- Streamlit reading page
- summary view
- source paragraph view
- highlight labels
- memory point review
- memory bank

### Phase 5: Dataset

- collect around 100 documents
- define annotation schema
- label high, medium, and low salience passages
- create train, dev, and test splits

### Phase 6: ML Ranking

- TF-IDF baseline
- Sentence-BERT baseline
- MLP baseline
- LLM scorer
- Hybrid MemoryRanker

### Phase 7: Dynamic Memory

- recall event log
- recall count
- last recalled timestamp
- reinforcement
- decay
- memory strength visualization

### Phase 8: Recall Mode

- new article triggers old memories
- support, conflict, complement, and extension relation detection
- source-grounded chat over current and historical memory

### Phase 9: Evaluation

- retrieval benchmark
- ranking benchmark
- ablation study
- citation correctness
- unsupported answer rate
- results tables

### Phase 10: Report and Portfolio Polish

- 6-8 page technical report
- README results table
- screenshots
- demo video
- reproducible scripts
- final project summary

## Completion Estimate

| Target | Scope | Estimated time |
|---|---|---:|
| Basic MVP | ingestion, RAG, memory extraction, simple UI | 2-3 weeks |
| Strong project version | MVP + memory bank + recall chat + dynamic scoring + clean README | 5-7 weeks |
| Evaluation version | dataset + ML baselines + ablations + report + demo video | 9-12 weeks |
| Complete version | polished demo + reproducible experiments + report + quantified gains | 12-16 weeks |

By weekly commitment:

| Weekly commitment | Complete version estimated duration |
|---|---:|
| 15-20 hours/week | 3-4 months |
| 25-30 hours/week | 10-12 weeks |
| 40 hours/week | 7-9 weeks |

Main time costs:

- Data annotation: 2-4 weeks.
- RAG and memory pipeline: 2-3 weeks.
- Streamlit demo: 1-2 weeks.
- ML baselines: 2-3 weeks.
- Evaluation and ablation: 2-3 weeks.
- Technical report and GitHub polish: 1-2 weeks.

## Scope Control

To finish on time, focus on:

```text
long-term reading recall
+ memory point ranking
+ user highlight signal
+ dynamic reinforcement/decay
+ evaluation against RAG baselines
```

Do not prioritize:

- multi-user accounts
- browser extension
- mobile app
- complex permissions
- large-scale deployment
- excessive UI animation
- too many file formats

## Final Project Summary

```text
Developed MemoryPoint, a personalized reading-memory retrieval system that extracts and ranks source-grounded memory points from long-form documents using salience prediction, user highlight signals, and dynamic reinforcement/decay.

Built a 100-document annotated dataset with passage-level salience labels and evidence-linked memory points; trained TF-IDF, Sentence-BERT, MLP, and hybrid ranking baselines.

Evaluated MemoryPoint against standard RAG, summary-only memory, and static memory-point baselines using Precision@K, Recall@K, NDCG@K, MRR, and citation correctness.

Improved cross-document recall quality by X% NDCG@5 over standard chunk-based RAG while reducing unsupported answer rate by Y%.
```

The final X and Y must be replaced with real experiment results.
