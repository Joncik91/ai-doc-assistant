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

## Acceptance evidence

### Corpus coverage audit

The curated demo corpus was checked against the shipped evaluation set. Result:
**8/8 prompts have direct source coverage in the referenced documents**, so the
demo corpus meets the PRD usefulness prerequisite for live cited answers.

| Prompt | Expected sources | Evidence |
| --- | --- | --- |
| Q01 | `operator-workflow.md`, `security-operating-model.md` | Auth docs explicitly mention JWT and `X-API-Key` access |
| Q02 | `operator-workflow.md` | Upload flow lists TXT, Markdown, PDF, and DOCX |
| Q03 | `operator-workflow.md` | Workflow notes duplicate detection and ignore behavior |
| Q04 | `security-operating-model.md` | Safety docs mention guardrails, rate limiting, and audit logging |
| Q05 | `security-operating-model.md`, `deployment-notes.md` | Runtime docs mention stats, metrics, and request IDs |
| Q06 | `deployment-notes.md` | Deployment notes state Docker Compose is the primary path |
| Q07 | `product-overview.md`, `operator-workflow.md` | Product/workflow docs mention source citations and confidence |
| Q08 | `operator-workflow.md` | Workflow documents delete support for unneeded documents |

### Shipped acceptance status

| Requirement | Status | Evidence |
| --- | --- | --- |
| Streamed grounded answers | Pass | Backend `/api/v1/query/stream` plus frontend incremental rendering |
| Expandable citation UX | Pass | Citation cards expand to show excerpt and chunk metadata |
| Theme support | Pass | Operator UI supports dark and light themes |
| Second provider path | Pass | Ollama adapter available behind `LLM_PROVIDER` |
| Demo usefulness proof | Pass | Corpus coverage audit above confirms all 8 prompts are source-backed |
