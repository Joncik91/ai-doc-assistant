# AI Document Assistant

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React + TypeScript](https://img.shields.io/badge/React%20%2B%20TypeScript-18%20·%205-3178C6?logo=react&logoColor=white)](https://react.dev/)
[![Chroma](https://img.shields.io/badge/vector%20store-Chroma-E8954A)](https://www.trychroma.com/)
[![Docker Compose](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![License: MIT](https://img.shields.io/badge/license-MIT-E8954A.svg)](LICENSE)
[![SOLID · DRY · YAGNI](https://img.shields.io/badge/SOLID%20·%20DRY%20·%20YAGNI-applied-E8954A)](#design-principles)

**A portfolio-grade AI document assistant showcasing safe, disciplined software engineering practices.**

Local-first retrieval (Chroma + deterministic embeddings) over a swappable LLM backend (DeepSeek by default, Ollama supported). FastAPI backend with JWT + API-key auth, rate limiting, PII detection, audit history, Prometheus metrics. React + TypeScript operator workspace. Ships with Docker Compose, illustrative Kubernetes manifests, demo corpus, and a sprint-planned roadmap.

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API](#api)
- [Design Principles](#design-principles)
- [LLM Provider](#llm-provider)
- [Vector Search](#vector-search)
- [Testing](#testing)
- [Deployment](#deployment)
- [Roadmap](#roadmap)
- [Security](#security)
- [License](#license)

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Or: Python 3.11+, Node.js 20+

### With Docker Compose

```bash
# Set up environment (copy example)
cp .env.example .env

# Edit .env to add your model provider credentials:
# LLM_API_KEY=your-deepseek-api-key-here

# Start all services
docker compose up --build

# Access the app:
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Chroma: http://localhost:8001
```

### Local Development (without Docker)

**Backend:**
```bash
cp .env.example .env
# Edit .env and set:
# - LLM_API_KEY
# - SECRET_KEY
# - BOOTSTRAP_ADMIN_PASSWORD
# - BOOTSTRAP_API_KEY

cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create data directory
mkdir -p ../data

# Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend (in another terminal):**
```bash
cd frontend
npm install
npm run dev
```

The frontend uses relative `/api/...` requests. In local development, Vite
proxies them to `http://localhost:8000` by default. In containerized runtimes,
the frontend dev server must set `VITE_API_PROXY_TARGET` to the backend
service address.

## Project Structure

```
.
├── backend/               # FastAPI application
│   ├── app/
│   │   ├── main.py       # Entry point
│   │   ├── config.py     # Configuration management
│   │   ├── auth/         # Authentication and authorization
│   │   ├── llm/          # LLM provider abstraction
│   │   ├── retrieval/    # Vector search and retrieval
│   │   ├── ingestion/    # Document processing pipeline
│   │   ├── storage/      # Metadata and document store
│   │   ├── guardrails/   # Safety and filtering
│   │   ├── audit/        # Query history and logging
│   │   ├── observability/# Metrics and tracing
│   │   ├── api/          # API routes
│   │   └── models/       # Data schemas
│   ├── tests/            # Backend tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/             # React + TypeScript application
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/          # API client
│   │   ├── types.ts      # Shared UI types
│   │   └── test/         # Frontend test setup
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── Dockerfile
├── demo-corpus/          # Sample documents for demos
├── k8s/                  # Kubernetes manifests (portfolio artifact)
├── docs/                 # Architecture, deployment, and evaluation notes
├── docker-compose.yml    # Local development runtime
├── PRD.md               # Product requirements document
├── PRODUCT_BRIEF.md     # Original brief
└── README.md            # This file
```

## Configuration

All configuration is environment-driven and centralized in `backend/app/config.py`.

Key variables (see `.env.example`):

- `DEBUG` – Enable debug mode
- `LLM_PROVIDER` – LLM provider (deepseek or ollama)
- `LLM_API_KEY` – API key for the provider (not required for ollama)
- `LLM_BASE_URL` – Optional provider endpoint override; defaults to `https://api.deepseek.com/v1` for DeepSeek and `http://localhost:11434` for Ollama
- `LLM_MODEL` – Model name for the selected provider
- `CHROMA_PERSIST_DIRECTORY` – Vector store location
- `DOCUMENT_STORAGE_DIRECTORY` – Persisted upload location
- `MAX_UPLOAD_SIZE_BYTES` – Maximum allowed upload size
- `DATABASE_URL` – SQLite database path
- `SECRET_KEY` – JWT secret (required)
- `BOOTSTRAP_ADMIN_PASSWORD` – Operator bootstrap password (required)
- `BOOTSTRAP_API_KEY` – API key for programmatic access (required)

## API

The backend exposes a REST API at `http://localhost:8000/api/v1/`.

### Health and Config
- `GET /health` – Health check
- `GET /api/v1/config` – Runtime configuration (non-sensitive)

### Authentication
- `POST /api/v1/auth/login` – Operator login
- `GET /api/v1/auth/me` – Resolve the current actor via JWT or `X-API-Key`
- `GET /api/v1/health/provider` – Provider readiness status
- `POST /api/v1/guardrails/check` – Prompt safety preflight for the operator UI
- `GET /api/v1/audit/events` – Recent operator actions and query history
- `GET /api/v1/stats` – Runtime snapshot for the operator dashboard
- `GET /metrics` – Prometheus-compatible metrics output

### Documents and retrieval
- `POST /api/v1/documents/upload` – Upload and ingest one or more documents
- `GET /api/v1/documents` – List indexed documents
- `GET /api/v1/documents/{document_id}` – Inspect a single document
- `DELETE /api/v1/documents/{document_id}` – Remove a document and its indexed chunks
- `POST /api/v1/query` – Ask a grounded question over indexed chunks
- `POST /api/v1/query/stream` – Stream a grounded question response over indexed chunks
- `GET /api/v1/health/retrieval` – Vector-store readiness status

### Operator workspace
- Browser login with JWT or API key
- Document registry, upload progress, and delete actions
- Guardrail preview, streamed answers, session memory, citations, and audit history
- Dark and light theme support
- Runtime stats, health cards, and release-readiness signals

## Design Principles

This project demonstrates:
- **SOLID**: Single responsibility, open/closed, Liskov substitution, interface segregation, dependency inversion
- **DRY**: Centralized configuration, shared auth logic, reusable models
- **SECURITY**: JWT auth, API keys, rate limiting, query validation, PII detection, structured logging
- **YAGNI**: No multi-tenancy, no document-level ACLs, local-first retrieval, cloud-only generation

## LLM Provider

Currently configured for **DeepSeek** via OpenAI-compatible API.

The provider is abstracted behind a contract in `backend/app/llm/`, and the repo now also ships an **Ollama** adapter behind the same interface so provider selection stays environment-driven.

- **DeepSeek:** set `LLM_PROVIDER=deepseek`, provide `LLM_API_KEY`, and optionally override `LLM_BASE_URL`
- **Ollama:** set `LLM_PROVIDER=ollama`, set `LLM_MODEL` to a local model such as `llama3.1`, and leave `LLM_BASE_URL` unset unless your Ollama server is not on `http://localhost:11434`

## Vector Search

Chroma is wired into the local runtime, with deterministic local embeddings and cited retrieval backed by the stored document chunks.

## Testing

**Backend:**
```bash
cd backend
pytest
```

**Frontend:**
```bash
cd frontend
npm run test
```

## Deployment

The current runtime supports Docker Compose as the primary path, plus
illustrative Kubernetes manifests.

See:

- `docs/deployment.md`
- `docs/architecture.md`
- `docs/evaluation.md`

## Roadmap

The sprint plan is tracked in [`docs/SPRINTS.md`](docs/SPRINTS.md).

## Security

Security is treated as a first-class engineering concern, not a feature
flag. The relevant surfaces:

- **Auth.** Every API route except `/health`, `/api/v1/config`, and
  `/api/v1/auth/login` requires either a JWT (operator workspace) or
  an `X-API-Key` header (programmatic access). `BOOTSTRAP_ADMIN_PASSWORD`
  and `BOOTSTRAP_API_KEY` are required environment variables — the
  app refuses to start without them, so there is no "default password"
  failure mode.
- **Secrets.** `SECRET_KEY` (JWT signing), `LLM_API_KEY`, and the
  bootstrap credentials are all environment-driven. `.env.example`
  documents the surface; `.env` is gitignored. Don't commit `.env`.
- **Rate limiting + PII.** The query path runs through a guardrail
  preflight (`/api/v1/guardrails/check`) and a query-validation step
  before reaching the LLM. PII detection is on by default.
- **What leaves the host.** When `LLM_PROVIDER=deepseek`, the user
  question + retrieved document chunks are sent to DeepSeek's API.
  Switch to `LLM_PROVIDER=ollama` for a self-hosted endpoint where
  nothing leaves the machine. Document storage and the vector index
  are always local (`DOCUMENT_STORAGE_DIRECTORY`, `CHROMA_PERSIST_DIRECTORY`).
- **Audit log.** Every operator action and query lands in the audit
  store, queryable via `GET /api/v1/audit/events`. Useful for
  reconstructing what an actor did and what was returned.

Don't expose this to the public internet without a reverse proxy
that terminates TLS, enforces additional rate limiting, and binds
the service to authenticated networks (LAN, WireGuard, Tailscale).

## License

MIT — see [LICENSE](LICENSE).
