# Product Brief: AI Document Assistant

## Overview
A secure, enterprise-grade Retrieval-Augmented Generation (RAG) application that ingests internal documents and provides accurate, cited answers to business queries. Built to demonstrate full AI product lifecycle competency — from design to production-ready deployment.

## Problem
Enterprise teams spend significant time searching through documents (policies, specs, procurement guidelines, technical standards). Information is scattered across formats and locations, leading to inconsistent answers and wasted time.

## Solution
A self-hosted AI assistant that:
- Ingests documents (PDF, DOCX, TXT, Markdown)
- Chunks and embeds content into a vector store
- Answers natural language questions with **source citations**
- Exposes a REST API and web interface
- Runs entirely locally (no cloud dependencies)

## Target Users
- Procurement teams querying contract terms and supplier policies
- Engineers searching technical standards and specs
- New employees onboarding with company documentation

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  React Frontend  │────▶│  FastAPI Gateway  │────▶│   RAG Engine    │
│  (Chat UI)       │     │  (auth, rate lim) │     │  (retrieval+LLM)│
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                           │
                                                ┌──────────┴──────────┐
                                                │                      │
                                         ┌──────▼──────┐      ┌──────▼──────┐
                                         │  ChromaDB   │      │   Ollama    │
                                         │ (embeddings) │      │  (local LLM)│
                                         └─────────────┘      └─────────────┘
```

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | Python 3.12 + FastAPI | API server, orchestration |
| AI/LLM | Ollama (Llama 3.1 8B) | Local inference, no API keys |
| Embeddings | `sentence-transformers` (all-MiniLM-L6-v2) | Document embedding |
| Vector Store | ChromaDB | Persistent embedding storage |
| Frontend | React + Vite + Tailwind | Chat interface |
| Containers | Docker + Docker Compose | Local orchestration |
| Orchestration | Kubernetes manifests | Production-ready deployment |
| Auth | API key + JWT | Secure access |
| Monitoring | Structured logging + Prometheus metrics | Observability |

## Core Features

### 1. Document Ingestion Pipeline
- Upload via API or drag-and-drop in UI
- Auto-extract text from PDF, DOCX, TXT, MD
- Smart chunking (by section/paragraph, not just character count)
- Metadata preservation (source, page, section title)
- Duplicate detection (skip already-ingested docs)
- Ingestion status tracking

### 2. Query Engine
- Natural language → semantic search → LLM generation
- Top-k retrieval with relevance scoring
- Source attribution (which doc, which page, which section)
- Conversation memory (follow-up questions maintain context)
- Streaming responses

### 3. Responsible AI Guardrails
- **PII Detection**: Flag/redact sensitive info before indexing
- **Confidence Scoring**: Low-confidence answers get a disclaimer
- **Content Filtering**: Block harmful/off-topic queries
- **Audit Trail**: Log every query, response, and source used
- **Rate Limiting**: Per-user query limits

### 4. API Layer
- RESTful endpoints with OpenAPI/Swagger docs
- `/api/v1/documents` — upload, list, delete documents
- `/api/v1/query` — ask questions, get cited answers
- `/api/v1/health` — system status, embedding count
- API key authentication
- Request/response logging

### 5. Frontend
- Clean chat interface (ChatGPT-like)
- Document management panel (upload, status, delete)
- Source citations as expandable cards
- Dark/light mode
- Responsive design

## API Design (Draft)

```
POST   /api/v1/documents/upload     # Upload document(s)
GET    /api/v1/documents             # List ingested documents
DELETE /api/v1/documents/{id}        # Remove document + embeddings

POST   /api/v1/query                # Submit query, get answer + sources
GET    /api/v1/query/history         # Query history

GET    /api/v1/health                # System health check
GET    /api/v1/stats                 # Usage statistics
```

## Project Structure

```
ai-doc-assistant/
├── docker-compose.yml
├── k8s/                          # Kubernetes manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   └── configmap.yaml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py               # FastAPI app
│   │   ├── config.py             # Settings
│   │   ├── auth/                 # API key + JWT
│   │   ├── ingestion/            # Document processing
│   │   │   ├── loader.py         # File extraction
│   │   │   ├── chunker.py        # Smart chunking
│   │   │   └── embedder.py       # Embedding pipeline
│   │   ├── retrieval/            # RAG engine
│   │   │   ├── store.py          # ChromaDB interface
│   │   │   ├── retriever.py      # Semantic search
│   │   │   └── generator.py      # LLM response generation
│   │   ├── guardrails/           # Responsible AI
│   │   │   ├── pii.py
│   │   │   ├── filter.py
│   │   │   └── audit.py
│   │   ├── api/                  # Route handlers
│   │   └── models/               # Pydantic schemas
│   └── tests/
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── App.jsx
│       ├── components/
│       │   ├── ChatWindow.jsx
│       │   ├── DocumentPanel.jsx
│       │   └── SourceCard.jsx
│       └── api/                  # API client
└── docs/
    ├── api-spec.yaml             # OpenAPI spec
    ├── architecture.md
    └── deployment.md
```

## Phased Delivery

### Phase 1 — Core Pipeline (Days 1-2)
- [ ] Project scaffold + Docker Compose
- [ ] Document loader (PDF, DOCX, TXT)
- [ ] Chunker + embedder
- [ ] ChromaDB integration
- [ ] Ollama setup (Llama 3.1 8B)
- [ ] Basic `/query` endpoint
- [ ] Simple test with 5-10 sample documents

### Phase 2 — API + Auth (Days 3-4)
- [ ] Full REST API with all endpoints
- [ ] API key authentication
- [ ] Rate limiting
- [ ] Swagger docs
- [ ] Structured logging
- [ ] Unit + integration tests

### Phase 3 — Frontend (Days 5-6)
- [ ] React chat UI
- [ ] Document upload panel
- [ ] Source citation cards
- [ ] Responsive design

### Phase 4 — Enterprise Polish (Days 7-8)
- [ ] PII detection
- [ ] Content filtering
- [ ] Audit logging
- [ ] Prometheus metrics
- [ ] Kubernetes manifests
- [ ] README + deployment docs
- [ ] Demo video script

## Demo Script (5 minutes)

1. **"The Problem"** (30s) — Show scattered documents, slow search
2. **"Upload"** (30s) — Drag 10 documents into the UI, watch ingestion
3. **"Query"** (1 min) — Ask 3 questions, show cited answers
4. **"Guardrails"** (1 min) — Show PII redaction, low-confidence disclaimer
5. **"API"** (1 min) — Swagger docs, programmatic access
6. **"Infrastructure"** (1 min) — Docker Compose → K8s, monitoring
7. **"Scale"** (30s) — Architecture diagram, how it grows

## Hardware Requirements (Geekom A8)

- **RAM**: 4GB for Ollama + 1GB ChromaDB + 1GB API = ~6GB (A8 has plenty)
- **Storage**: ~5GB for models, ~500MB for app
- **CPU**: Adequate for 8B model inference (expect ~10-15 tokens/sec)
- **GPU**: Not required (CPU inference, or use smaller model like Phi-3)

## Success Metrics
- Query accuracy with citations >80% on test set
- Response latency <15 seconds end-to-end
- Zero data leaves the machine
- Deployable with single `docker compose up`
- Kubernetes manifests validate without modification
