# Retrieval Evaluation

## Frozen Result

Original evaluation date: 2026-10-09
Revalidated: 2026-10-11

The benchmark contains 14 answerable questions over four source documents:

- `attention.md`
- `rag.md`
- `lora.md`
- `react.md`

The golden set uses `evidence.acceptable_chunks`. A case is successful when at least one acceptable answer-bearing chunk appears in the top five results. It does not require every listed chunk to appear.

The current authoritative hybrid-retrieval result is:

```text
Evidence Recall@5: 0.714
MRR@5:             0.389
```

This result uses the current evaluator and the current 14-case golden set.

An earlier evaluator and golden-set schema produced:

```text
Recall@5: 0.476
MRR@5:    0.225
```

That historical result is not directly comparable. It treated every referenced
chunk as necessary, while the current evaluator treats acceptable chunks as
alternative answer-bearing evidence.

An additional historical result was reported as `Evidence Recall@5=0.786` and
`MRR@5=0.335`, but its evaluator version and golden-set provenance were not
recorded. It is unaudited and is not used for performance comparison or sign-off.

The FTS change is retained provisionally. This evaluation does not claim that it
improved overall retrieval quality relative to either historical result.

## Retrieval Configuration

Hybrid retrieval combines:

- pgvector cosine-distance search using 384-dimensional embeddings
- PostgreSQL full-text search using the `english` configuration
- OR-based natural-language terms passed to `websearch_to_tsquery`
- reciprocal rank fusion

The full-text change prevents natural-language questions from requiring every query term to occur in the same chunk.

## Reproduce

Start PostgreSQL, Redis, and an API using the current source, then run:

```bash
EVAL_API_URL=http://localhost:8000 \
API_KEY=dev-test-key \
DATABASE_URL=postgresql+psycopg://your_user:your_password@127.0.0.1:5432/dgms \
python evaluation/evaluate_retrieval.py
```

The API must expose `POST /query` and use the same database corpus as the
evaluator. The evaluator prints each case's acceptable chunk IDs, retrieved
chunks, fused ranks, evidence recall, and reciprocal rank before reporting the
aggregate metrics.

## Metric Definitions

- **Evidence Recall@5:** fraction of cases where at least one acceptable
  answer-bearing chunk appears in the top five results.
- **MRR@5:** mean reciprocal rank of the first acceptable chunk found in the
  top five results; cases with no acceptable chunk contribute zero.

The benchmark contains 14 answerable questions across four source documents.

## Known Failures

The benchmark still includes genuine retrieval misses. The most important remaining cases are positional encoding and some RAG conceptual passages. These remain in the benchmark rather than being removed or relabeled to inflate the score.
