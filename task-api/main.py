"""Main entry point for FastAPI application."""
from fastapi import FastAPI
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
)

# CORS middleware to allow React SPA (localhost:5173) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
