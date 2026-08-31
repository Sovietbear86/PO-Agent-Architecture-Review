"""Main entry point for FastAPI application."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import tasks, jira, swtr_sync, swtr_read
from app.exceptions.handlers import (
    validation_exception_handler,
    value_error_handler,
)


app = FastAPI(
    title="Task Tracker API",
    description="REST API for managing tasks (local + Jira)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    redirect_slashes=False,
)

# CORS middleware to allow React SPA (localhost:5173) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def require_space_for_version_search(request: Request, call_next):
    """Fail locally when the live MCP search_versions contract lacks required space.

    The current MCP-SWTR VersionSearchRequest requires `space`; letting an empty
    request reach MCP turns a caller contract error into a misleading 502. Keep
    the facade explicit and fail closed with HTTP 400 before any upstream call.
    """
    if request.method == "GET" and request.url.path == "/api/v1/swtr-read/versions":
        space = request.query_params.get("space")
        if not space or not space.strip():
            return JSONResponse(
                status_code=400,
                content={"detail": "space is required for search_versions"},
            )
    return await call_next(request)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler_wrapper(request, exc: RequestValidationError):
    """Wrapper for validation exception handler."""
    return await validation_exception_handler(request, exc)


@app.exception_handler(ValueError)
async def value_error_handler_wrapper(request, exc: ValueError):
    """Wrapper for ValueError handler."""
    return await value_error_handler(request, exc)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


app.include_router(tasks.router)
app.include_router(jira.router)
app.include_router(swtr_sync.router)
app.include_router(swtr_read.router)
