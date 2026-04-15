# Deployment

## Primary path

The supported runtime is Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

The frontend keeps browser requests on relative `/api/...` paths and relies on
the Vite dev-server proxy. Local development defaults that proxy to
`http://localhost:8000`; containerized runtimes must set
`VITE_API_PROXY_TARGET` to the backend service address.

## Runtime endpoints

- `http://localhost:5173` — operator UI
- `http://localhost:8000` — backend API
- `http://localhost:8000/health` — basic health
- `http://localhost:8000/api/v1/stats` — runtime snapshot
- `http://localhost:8000/metrics` — Prometheus metrics

## Environment

Keep the following values in `.env` or the target deployment system:

- `LLM_API_KEY`
- `SECRET_KEY`
- `BOOTSTRAP_ADMIN_PASSWORD`
- `BOOTSTRAP_API_KEY`

The application does not ship hardcoded fallback credentials; these values must
be provided explicitly for local runs and deployments.

## Kubernetes

The repository also includes a single illustrative manifest in `k8s/stack.yaml`
for teams that want a cluster-shaped artifact alongside Compose.

Every `replace-me*` value in that manifest must be changed before deployment,
especially the bootstrap admin password and API key.
