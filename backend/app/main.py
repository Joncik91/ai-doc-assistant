"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from app.api.audit import router as audit_router
from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.guardrails import router as guardrails_router
from app.api.health import router as health_router
from app.api.query import router as query_router
from app.api.stats import router as stats_router
from app.auth.operators import bootstrap_operators
from app.config import get_settings
from app.observability.logging import configure_logging
from app.observability.metrics import initialize_metrics, metrics_content_type, render_metrics
from app.observability.middleware import ObservabilityMiddleware
from app.observability.stats import APP_STARTED_AT, collect_runtime_stats
from app.storage.database import initialize_database

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Bootstrap local runtime state for the application."""
    logger.info(
        "startup",
        extra={
            "app_name": settings.app_name,
            "version": settings.app_version,
            "llm_provider": settings.llm_provider,
            "debug": settings.debug,
        },
    )
    initialize_database()
    bootstrap_operators()
    initialize_metrics(settings.app_name, settings.app_version, APP_STARTED_AT)
    logger.info("bootstrap_complete", extra={"component": "auth"})
    yield
    logger.info("shutdown", extra={"app_name": settings.app_name})


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ObservabilityMiddleware)

app.include_router(auth_router)
app.include_router(audit_router)
app.include_router(stats_router)
app.include_router(guardrails_router)
app.include_router(health_router)
app.include_router(documents_router)
app.include_router(query_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "app": settings.app_name,
            "version": settings.app_version,
        },
    )


@app.get("/api/v1/config")
async def config_info():
    """Runtime configuration info (non-sensitive fields)."""
    return JSONResponse(
        status_code=200,
        content={
            "app_name": settings.app_name,
            "version": settings.app_version,
            "llm_provider": settings.llm_provider,
            "llm_model": settings.llm_model,
        },
    )


@app.get("/api/v1/health/provider")
async def provider_health():
    """Check LLM provider health and status."""
    from app.llm.factory import health_check

    status = await health_check()
    return JSONResponse(
        status_code=200 if status.get("healthy") else 503,
        content=status,
    )


@app.get("/metrics")
async def metrics() -> PlainTextResponse:
    """Expose Prometheus metrics for the runtime."""
    collect_runtime_stats()
    return PlainTextResponse(render_metrics(), media_type=metrics_content_type())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
