"""FastAPI application entry point for PO Agent Platform v2."""

import logging
import time
import uuid

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from po_agent import __app_name__, __version__
from po_agent.config import get_settings
from po_agent.core import errors
from po_agent.api.v1 import health_check as api_v1_health_check
from po_agent.api.v1 import router as api_v1_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=__app_name__,
    version=__version__,
    description="PO Agent Platform v2.1 - Harness-based assistant for product owner",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include API v1 routes
app.include_router(api_v1_router, prefix="/api/v1", tags=["v1"])


@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Add correlation ID to requests."""
    settings = get_settings()
    correlation_id = request.headers.get(
        settings.correlation_id_header, str(uuid.uuid4())
    )
    request.state.correlation_id = correlation_id

    start_time = time.time()

    try:
        response = await call_next(request)
        response.headers[settings.correlation_id_header] = correlation_id
        return response
    except Exception as exc:
        logger.error(
            "Error processing request",
            extra={
                "correlation_id": correlation_id,
                "path": request.url.path,
                "error": str(exc),
            },
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "correlation_id": correlation_id,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
        )
    finally:
        process_time = time.time() - start_time
        logger.info(
            "Request completed",
            extra={
                "correlation_id": correlation_id,
                "path": request.url.path,
                "method": request.method,
                "duration_ms": int(process_time * 1000),
            },
        )


@app.get("/live")
async def live_check():
    """Process liveness endpoint.

    This endpoint only proves the web process is responding. Readiness checks
    that gate QA or production traffic must use /health or /api/v1/health.
    """
    return {
        "status": "healthy",
        "service": __app_name__,
        "check": "liveness",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


@app.get("/health")
async def health_check(request: Request):
    """Runtime/source readiness endpoint.

    Keep the historical root health URL, but make it readiness-aware so test
    harnesses do not start acceptance runs while the Harness runtime or source
    adapter is still degraded.
    """
    return await api_v1_health_check(request)


@app.get("/version")
async def version():
    """Version info endpoint."""
    return {
        "app_name": __app_name__,
        "version": __version__,
        "app_version": __version__,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {__app_name__}",
        "version": __version__,
        "docs": "/docs",
    }


def main():
    """Run the application."""
    settings = get_settings()
    uvicorn.run(
        "po_agent.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
    )


if __name__ == "__main__":
    main()
