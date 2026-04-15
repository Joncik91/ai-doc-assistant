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

**Status:** Planned

**Goal:** make the project portfolio-ready, observable, and easy to run and demonstrate.

**Planned scope**
- Health, stats, metrics, and structured logging improvements
- Deployment assets and secure configuration hardening
- Demo corpus curation and evaluation set
- Final docs for demo, deployment, and architecture
