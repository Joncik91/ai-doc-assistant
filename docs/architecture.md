# Architecture

AI Document Assistant is built as a small, swappable stack:

- **Frontend:** React + Vite operator workspace
- **Backend:** FastAPI with JWT and API-key auth
- **LLM provider:** DeepSeek behind a provider abstraction
- **Retrieval:** local chunking, embeddings, and Chroma
- **Persistence:** SQLite for metadata, ingestion events, and audit events
- **Observability:** request IDs, structured logs, stats, and Prometheus metrics

## Request flow

1. The operator signs in and receives a session token or uses `X-API-Key`.
2. Documents are uploaded into the registry and chunked locally.
3. Retrieval pulls the best chunks and forwards only the selected context to the provider.
4. Guardrails and rate limiting run before the query is executed.
5. Audit events and runtime statistics are persisted for operator review.

## Design constraints

- Keep the provider layer replaceable.
- Keep retrieval local.
- Keep secrets out of browser storage.
- Prefer explicit failure over silent fallback.

