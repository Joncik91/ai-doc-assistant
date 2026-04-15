"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import get_settings
from app.api.auth import router as auth_router
from app.auth.operators import bootstrap_operators

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)


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


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"LLM Provider: {settings.llm_provider}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Bootstrap operators
    bootstrap_operators()
    logger.info("Bootstrap operators initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info(f"Shutting down {settings.app_name}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
