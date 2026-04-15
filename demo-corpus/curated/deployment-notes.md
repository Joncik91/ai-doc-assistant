# Deployment notes

## Local runtime

The primary supported path is Docker Compose:

```bash
docker compose up --build
```

## Key endpoints

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Health: `http://localhost:8000/health`
- Stats: `http://localhost:8000/api/v1/stats`
- Metrics: `http://localhost:8000/metrics`

## Configuration

The app is driven by environment variables. Secrets stay out of source control
and should be provided through `.env` or deployment tooling.

