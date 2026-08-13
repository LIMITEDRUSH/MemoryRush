You are extracting source-grounded reading memory from one article.

Use only the provided paragraphs. Every core idea and memory unit must cite paragraph IDs from the source context.

Return valid JSON with this shape:

```json
{
  "summary": "Concise source-grounded article summary.",
  "core_ideas": [
    {
      "idea": "A specific idea worth remembering.",
      "why_it_matters": "Why this idea may be useful later.",
      "evidence": {
        "paragraph_id": "p_001",
        "quote": "Short supporting quote from that paragraph."
      },
      "salience_score": 0.0
    }
  ],
  "memory_units": [
    {
      "content": "A durable memory statement.",
      "memory_type": "conceptual_insight",
      "evidence_paragraph_ids": ["p_001"],
      "tags": ["topic"],
      "confidence": 0.0
    }
  ],
  "recall_questions": [
    {
      "question": "A review question.",
      "expected_answer": "The expected answer.",
      "memory_unit_index": 0
    }
  ]
}
```

Rules:

- Generate 3 to 7 memory units unless the article is too short.
- Do not invent evidence.
- Keep quotes short and copied from the referenced paragraph.
- Use confidence and salience scores between 0.0 and 1.0.
- Return JSON only.
