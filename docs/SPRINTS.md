# Sprint Plan

This repository follows a six-sprint delivery plan. Sprints 1-5 are complete; Sprint 6 remains pending approval and implementation.

## Sprint 1: Foundation and first working slice

**Status:** Complete

**Goal:** establish the backend/frontend scaffold, runtime contracts, authentication primitives, and the DeepSeek provider abstraction.

**Delivered**
- FastAPI backend scaffold with centralized configuration
- React + Vite frontend scaffold
- Docker runtime assets
- JWT login flow and API-key access path
- DeepSeek provider abstraction and provider health endpoint
- Backend route tests and frontend smoke test

## Sprint 2: Ingestion and grounded retrieval

**Status:** Complete

**Goal:** make documents ingestible, embeddable, retrievable, and answerable through a cited API flow.

**Delivered**
- Persistent document registry and ingestion status tracking
- Duplicate detection with persisted ingestion events
- Multi-format extraction for PDF, DOCX, TXT, and Markdown
- Chunking, local embeddings, and Chroma-backed vector storage
- Grounded query endpoint returning answers with citations

## Sprint 3: Operator experience and guardrails

**Status:** Complete

**Goal:** deliver the browser-based operator workflow and make safety behavior visible in the product.

**Delivered**
- Protected operator UI shell with JWT and API-key sign-in
- Document management screens with upload, duplicate awareness, and delete actions
- Chat UI with session memory, guardrail preflight, and citation cards
- Audit history view with filtering and backend event logging
- Harmful/off-topic filtering and rate limiting in the backend

## Sprint 4: Production-demo polish

**Status:** Complete

**Goal:** make the project portfolio-ready, observable, and easy to run and demonstrate.

**Scope**
- Health, stats, metrics, and structured logging improvements
- Deployment assets and secure configuration hardening
- Demo corpus curation and evaluation set
- Final docs for demo, deployment, and architecture

**Delivered**
- Request IDs, structured logging, runtime stats, and Prometheus metrics
- Kubernetes manifest and updated deployment notes
- Curated demo corpus plus evaluation set
- Architecture, deployment, and evaluation documentation

## Sprint 5: PRD contract closure and backend hardening

**Status:** Complete

**Goal:** close the remaining backend and API contract gaps so ingestion, auditability, and configuration match the PRD more closely.

**Delivered**
- Multi-file upload support in the API and web UI
- PRD-aligned document lifecycle states and warning handling
- PII detection warnings during ingestion
- Query audit payloads with answer and cited-source details
- Environment-injected secrets and the missing OpenAPI artifact

## Sprint 6: PRD experience completion and provider completeness

**Status:** Complete

**Goal:** finish the remaining user-visible and provider-related PRD gaps so the product fully satisfies the intended demo experience.

**Delivered**
- Backend-to-frontend streaming query responses with incremental UI updates
- Expandable citation cards plus light-theme support
- Ollama adapter behind the existing provider abstraction
- Final PRD acceptance closeout and evaluation proof
