# Retrieval Notes

RAG systems often fail because the retriever does not provide enough relevant evidence to the language model. In those cases, the generation step may look like the source of hallucination, but the underlying problem is missing or noisy context.

Reranking can improve answer quality by filtering retrieved chunks before they enter the final prompt. A stronger retriever is useful, but retrieval quality also depends on chunking, metadata, query rewriting, and source citation.

For MemoryPoint, this document is useful because it contains a clear conceptual memory: retrieval failures can cause downstream answer failures.
