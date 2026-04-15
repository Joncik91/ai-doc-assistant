# Evaluation

The demo corpus ships with a small question set in `demo-corpus/evaluation-set.json`.

## What the set checks

- Auth and operator flow
- Duplicate handling
- Guardrail blocking
- Deployment and observability clues
- Citation quality

## Success target

The product brief calls for a curated demo set that reaches useful cited answers
for most prompts. The JSON set is intentionally small so it can be run manually
during a live demo or expanded later into automated checks.

## Sprint 6 closeout

- Grounded answers stream from backend to frontend through `/api/v1/query/stream`.
- Citation cards expand to show excerpts and metadata.
- The operator UI supports dark and light themes.
- An Ollama adapter is available behind the same provider abstraction.
- The shipped demo flow plus this evaluation set cover the PRD acceptance proof.
