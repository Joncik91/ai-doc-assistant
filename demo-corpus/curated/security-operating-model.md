# Security operating model

## Controls

- Single-operator auth keeps the demo scope narrow
- JWT and API-key paths are both supported
- Guardrails block obvious prompt injection and risky prompts
- Rate limiting protects the query surface from repeated abuse
- Audit events capture logins, uploads, deletes, blocked queries, and queries

## Observability

- Health endpoints report runtime and retrieval readiness
- `/api/v1/stats` summarizes corpus and safety activity
- `/metrics` exposes Prometheus-compatible counters and gauges
- Logs include request IDs so activity can be correlated

