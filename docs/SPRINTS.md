# Sprint Plan

This repository follows a four-sprint delivery plan. Sprint 1 is complete; later sprints remain pending approval and implementation.

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

**Status:** Planned

**Goal:** make documents ingestible, embeddable, retrievable, and answerable through a cited API flow.

**Planned scope**
- Document registry and ingestion status tracking
- Duplicate detection and persisted metadata
- Multi-format extraction for PDF, DOCX, TXT, and Markdown
- Chunking and embedding into Chroma
- Query endpoint returning grounded answers with citations

## Sprint 3: Operator experience and guardrails

**Status:** Planned

**Goal:** deliver the browser-based operator workflow and make safety behavior visible in the product.

**Planned scope**
- Protected operator UI shell and document management screens
- Chat UI with session-scoped follow-ups and citation cards
- Audit history surfaces
- Harmful/off-topic filtering and rate limiting

## Sprint 4: Production-demo polish

**Status:** Planned

**Goal:** make the project portfolio-ready, observable, and easy to run and demonstrate.

**Planned scope**
- Health, stats, metrics, and structured logging improvements
- Deployment assets and secure configuration hardening
- Demo corpus curation and evaluation set
- Final docs for demo, deployment, and architecture
