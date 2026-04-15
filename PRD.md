# PRD: ABB AI Document Assistant

## Objective

Build an employer-facing, production-minded AI document assistant that demonstrates responsible AI product engineering end to end: document ingestion, retrieval, grounded answer generation with citations, safe-by-design controls, clear system boundaries, and a polished operator experience.

The product is intended to showcase how AI products should be built: with strong separation of concerns, minimal unnecessary complexity, explicit security tradeoffs, and disciplined scope control guided by SOLID, DRY, SECURITY, and YAGNI.

### Primary user

- A single authenticated operator/admin managing a shared document corpus

### Core user jobs

1. Upload and manage internal documents.
2. Ask business or technical questions in natural language.
3. Receive grounded answers with citations and confidence cues.
4. Review ingestion warnings, audit history, and system health.

## Assumptions

1. V1 is a **single-workspace, single-operator** application with no document-level permissions.
2. V1 is a **portfolio-quality production demo**: Docker Compose is the primary supported deployment path.
3. Cloud-hosted LLMs are the **primary inference path** in v1.
4. The inference layer must be **provider-abstracted** and support an **OpenAI-compatible** primary integration.
5. The initial cloud provider implementation for v1 is **DeepSeek**.
6. Local models via Ollama are optional in v1 and should fit behind the same abstraction without major refactoring.
7. PII detection in v1 is **detect-and-warn**, not auto-redact or block.
8. Conversation memory is session-scoped, while query history is persisted for operator review and audit purposes.
9. For v1, a lightweight metadata store such as SQLite is acceptable for audit, ingestion status, and query history unless later requirements justify a separate relational database.
10. Document sources are swappable inputs; the ingestion pipeline must not depend on any single repository or corpus source.

## Product Principles

- **SOLID:** Clear service boundaries across ingestion, retrieval, generation, auth, and guardrails.
- **DRY:** Shared models, configuration, and provider interfaces; no duplicate auth, parsing, or citation logic.
- **SECURITY:** Explicit auth boundaries, least-privilege defaults, auditable actions, safe secret handling, and controlled provider egress.
- **YAGNI:** No multi-tenancy, no RBAC matrix, no document-level ACLs, no premature distributed infrastructure, and no speculative AI orchestration layers in v1.

## Product Scope

### In scope for v1

- Document upload and ingestion for PDF, DOCX, TXT, and Markdown files
- Structured text extraction and metadata capture
- Chunking and embedding into a vector store
- Semantic retrieval with top-k scoring
- Answer generation with grounded citations
- Session-scoped conversational follow-ups
- Operator-facing document management
- Operator-facing query UI
- PII detection warnings during ingestion
- Low-confidence disclaimers on weak answers
- Harmful/off-topic request filtering
- Query, response, and source audit logging
- API key support for API consumers
- JWT-based operator authentication for the web app
- Request logging, health checks, metrics, and Docker deployment
- Kubernetes manifests included as a portfolio artifact, but not treated as the primary runtime target

### Explicitly out of scope for v1

- Multi-tenant workspaces
- Document-level permissions
- Human approval workflows for ingestion
- Automatic PII redaction or DLP enforcement
- Fine-tuning or training custom models
- Advanced reranking pipelines unless retrieval quality proves insufficient
- Real-time collaborative chat
- Complex conversation workspaces, folders, or saved prompt libraries
- Full Kubernetes production hardening and GitOps rollout workflows

## Functional Requirements

### FR1. Document ingestion

- The system shall accept one or more files via API and web UI.
- The system shall support PDF, DOCX, TXT, and Markdown.
- The system shall extract text and preserve source metadata where available, including document name, page number, and section heading.
- The system shall chunk documents using structure-aware heuristics rather than fixed-size character slicing only.
- The system shall compute embeddings and store them persistently in a vector database.
- The system shall detect duplicate documents using a deterministic content fingerprint and avoid duplicate ingestion.
- The system shall expose ingestion status values such as queued, processing, completed, warning, and failed.
- The system shall record ingestion warnings, including PII findings and parse anomalies.

### FR2. Retrieval and answer generation

- The system shall accept natural-language questions and retrieve relevant chunks from the indexed corpus.
- The system shall generate answers grounded in retrieved context only.
- The system shall return citations including source document and location metadata when available.
- The system shall support streaming responses to the UI.
- The system shall preserve session-scoped conversational context for follow-up questions.
- The system shall display or return a low-confidence disclaimer when retrieval or answer confidence falls below a configured threshold.

### FR3. Guardrails and responsible AI

- The system shall scan extracted content for PII indicators during ingestion and surface warnings to the operator.
- The system shall filter clearly harmful or out-of-scope queries according to a configurable policy.
- The system shall log every query, answer, cited source set, and guardrail event in an audit trail.
- The system shall make outbound model usage explicit in configuration and documentation.
- In cloud-model mode, the system shall only send prompt content and selected retrieval context needed for generation.

### FR4. API

- The system shall expose versioned REST endpoints under `/api/v1`.
- The system shall provide endpoints for document upload, listing, deletion, querying, history, health, and stats.
- The system shall publish OpenAPI documentation.
- The system shall enforce authentication on protected endpoints.
- The system shall log request metadata with correlation IDs.

### FR5. Web application

- The system shall provide a responsive chat interface optimized for desktop and usable on tablet/mobile.
- The system shall provide a document management panel with upload, status, warning, and delete actions.
- The system shall render citations as expandable source cards.
- The system shall support dark and light themes.
- The system shall expose system state clearly enough for a demo without requiring terminal access.

### FR6. Authentication and access

- The web application shall require operator authentication and use JWTs for authenticated sessions.
- The API shall support API keys for programmatic access.
- Rate limits shall apply per authenticated actor or API key.
- Since v1 is single-workspace, all authenticated access shall operate on the same shared corpus.

### FR7. Deployment and operations

- The system shall run through `docker compose up --build` as the primary setup path.
- The system shall support environment-based configuration for model provider, keys, thresholds, and storage paths.
- The system shall expose health and metrics endpoints.
- The repository shall include Kubernetes manifests that reflect the architecture, even if Compose remains the primary supported runtime for v1.

## Non-Functional Requirements

### Security

- Secrets must be injected through environment variables or secret stores, never hardcoded.
- Authenticated endpoints must reject unauthorized requests by default.
- File uploads must validate type and size before processing.
- Request logs must avoid leaking secrets or raw credentials.
- Query and ingestion audit logs must be tamper-evident enough for a portfolio demo, with immutable append-style behavior preferred.

### Reliability

- Failed ingestions must report explicit failure states.
- Retrieval or provider failures must return actionable errors, not silent fallbacks.
- Provider abstraction must support substitution without changing route or UI contracts.

### Performance

- Median end-to-end answer latency should target under 10 seconds on the default cloud provider for a representative demo corpus.
- P95 answer latency should target under 15 seconds.
- The system should support at least 10-20 representative documents in demo mode without degraded operator experience.

### Accuracy and trust

- Answers must include citations when grounded content is available.
- The system should achieve at least 80% answer usefulness on a curated demo evaluation set.
- Low-confidence responses must be visibly marked rather than overstated.

### Maintainability

- Ingestion, retrieval, generation, guardrails, auth, and API composition must be implemented as separable modules with testable interfaces.
- Cross-cutting concerns such as config, logging, auth, and models must be shared, not duplicated.

## Tech Stack

| Layer | Technology | Purpose |
| --- | --- | --- |
| Backend | Python 3.12 + FastAPI | API server, orchestration, typed service boundaries |
| Frontend | React + Vite + Tailwind | Operator UI |
| LLM integration | OpenAI-compatible client abstraction (initial provider: DeepSeek) | Cloud-primary inference layer |
| Local LLM option | Ollama adapter | Optional local inference path |
| Embeddings | `sentence-transformers` | Local embeddings for retrieval |
| Vector store | ChromaDB | Persistent semantic index |
| Metadata/audit store | SQLite (v1 assumption) | Ingestion status, query history, audit records |
| Containers | Docker + Docker Compose | Primary local runtime |
| Portfolio ops artifact | Kubernetes manifests | Deployment maturity signaling |
| Monitoring | Structured logs + Prometheus metrics | Observability |

## Commands

These are target project commands the implementation should support.

```bash
# full stack
docker compose up --build

# backend
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
cd backend && pytest
cd backend && ruff check .
cd backend && ruff format .

# frontend
cd frontend && npm install
cd frontend && npm run dev -- --host 0.0.0.0 --port 5173
cd frontend && npm run test
cd frontend && npm run lint
cd frontend && npm run build
```

## Project Structure

```text
ai-doc-assistant/
├── docker-compose.yml
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   └── configmap.yaml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/
│   │   ├── auth/
│   │   ├── ingestion/
│   │   ├── retrieval/
│   │   ├── llm/
│   │   ├── guardrails/
│   │   ├── audit/
│   │   ├── storage/
│   │   └── models/
│   └── tests/
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── api/
│       ├── components/
│       ├── features/
│       ├── hooks/
│       └── pages/
├── demo-corpus/
│   └── devdocs/
└── docs/
    ├── architecture.md
    ├── deployment.md
    └── api-spec.yaml
```

## Code Style

Use explicit interfaces, constructor injection, typed models, and narrow responsibilities.

```python
from typing import Protocol

from app.models.chat import ChatTurn, GeneratedAnswer, RetrievedChunk


class LLMClient(Protocol):
    async def generate(
        self,
        *,
        conversation: list[ChatTurn],
        context_chunks: list[RetrievedChunk],
        stream: bool,
    ) -> GeneratedAnswer: ...


class QueryService:
    def __init__(self, retriever, generator: LLMClient, auditor) -> None:
        self._retriever = retriever
        self._generator = generator
        self._auditor = auditor

    async def answer(self, conversation: list[ChatTurn]) -> GeneratedAnswer:
        chunks = await self._retriever.retrieve(conversation[-1].content)
        answer = await self._generator.generate(
            conversation=conversation,
            context_chunks=chunks,
            stream=False,
        )
        await self._auditor.record_query(answer=answer, sources=chunks)
        return answer
```

### Conventions

- Python: type hints required for public functions, small modules, explicit domain models
- React: feature-oriented components, hooks for side effects, API client isolated from UI rendering
- Naming: intention-revealing names, no abbreviations that hide business meaning
- Errors: explicit failures over silent fallbacks
- Comments: only where a decision or invariant is not obvious from code

## Testing Strategy

### Backend

- Unit tests for chunking, duplicate detection, provider abstraction, auth, guardrails, and citation assembly
- Integration tests for upload, query, history, and health endpoints
- Contract tests for provider adapters so local and cloud implementations obey the same interface

### Frontend

- Component tests for chat window, document panel, citation cards, and auth flows
- API integration mocks for loading, success, failure, and streaming states

### End-to-end

- Golden-path tests for upload -> ingest -> query -> cited response
- Negative-path tests for invalid file upload, unauthorized access, provider outage, and blocked queries

### Evaluation

- A small curated question set shall be maintained for demo documents to measure grounded-answer usefulness and citation correctness

## Boundaries

### Always do

- Keep model/provider logic behind a stable abstraction
- Validate file uploads, auth, and request payloads
- Return citations or explicit confidence disclaimers
- Log operator actions, query activity, and ingestion outcomes
- Prefer simple modules and explicit interfaces over framework-heavy indirection

### Ask first

- Adding a new external dependency with security or operational impact
- Replacing SQLite with a separate database
- Adding async queues, caches, or reranking services
- Expanding to multi-user or document-level permissions
- Treating Kubernetes as a required production target in v1

### Never do

- Hardcode secrets or provider credentials
- Send the entire corpus to a cloud model provider
- Bypass citations for generated answers that appear factual
- Hide ingestion or provider failures behind success-shaped responses
- Add enterprise-looking complexity that is not justified by v1 scope

## Success Criteria

1. An authenticated operator can upload supported documents and see deterministic ingestion states.
2. The operator can ask questions and receive cited answers grounded in retrieved content.
3. The UI clearly shows source attribution, warnings, and system feedback without terminal interaction.
4. Cloud-model inference works through a provider abstraction that can accommodate a local Ollama adapter later.
5. Query, source, and guardrail activity is auditable.
6. The application starts with Docker Compose as the primary supported setup.
7. The architecture and code organization clearly demonstrate safe, maintainable AI engineering practices to a hiring audience.

## Open Questions

1. Should operator authentication in v1 be seeded local credentials, SSO simulation, or a simple bootstrap admin flow?
2. Which public or synthetic document subset should be curated for the demo and evaluation set?
