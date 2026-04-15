# AI Document Assistant

A portfolio-grade AI document assistant showcasing safe, disciplined software engineering practices.

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Or: Python 3.11+, Node.js 20+

### With Docker Compose

```bash
# Set up environment (copy example)
cp .env.example .env

# Edit .env to add your DeepSeek API key:
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
- `LLM_PROVIDER` – LLM provider (deepseek)
- `LLM_API_KEY` – API key for the provider
- `LLM_MODEL` – Model name
- `CHROMA_PERSIST_DIRECTORY` – Vector store location
- `DOCUMENT_STORAGE_DIRECTORY` – Persisted upload location
- `MAX_UPLOAD_SIZE_BYTES` – Maximum allowed upload size
- `DATABASE_URL` – SQLite database path
- `SECRET_KEY` – JWT secret (change in production)

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
- `POST /api/v1/documents/upload` – Upload and ingest a document
- `GET /api/v1/documents` – List indexed documents
- `GET /api/v1/documents/{document_id}` – Inspect a single document
- `DELETE /api/v1/documents/{document_id}` – Remove a document and its indexed chunks
- `POST /api/v1/query` – Ask a grounded question over indexed chunks
- `GET /api/v1/health/retrieval` – Vector-store readiness status

### Operator workspace
- Browser login with JWT or API key
- Document registry, upload progress, and delete actions
- Guardrail preview, session memory, citations, and audit history
- Runtime stats, health cards, and release-readiness signals

## Design Principles

This project demonstrates:
- **SOLID**: Single responsibility, open/closed, Liskov substitution, interface segregation, dependency inversion
- **DRY**: Centralized configuration, shared auth logic, reusable models
- **SECURITY**: JWT auth, API keys, rate limiting, query validation, PII detection, structured logging
- **YAGNI**: No multi-tenancy, no document-level ACLs, local-first retrieval, cloud-only generation

## LLM Provider

Currently configured for **DeepSeek** via OpenAI-compatible API.

The provider is abstracted behind a contract in `backend/app/llm/` so other providers (Ollama, GPT, Claude) can be added without changing routes or the UI.

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

## License

Built as a portfolio project.
