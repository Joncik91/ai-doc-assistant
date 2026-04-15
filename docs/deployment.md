# Deployment

## Primary path

The supported runtime is Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

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

## Kubernetes

The repository also includes a single illustrative manifest in `k8s/stack.yaml`
for teams that want a cluster-shaped artifact alongside Compose.

