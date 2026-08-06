"""Global exception handlers."""
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": error["loc"][-1] if error["loc"] else "unknown",
            "message": error["msg"],
        })
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": errors},
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle HTTP exceptions."""
    if hasattr(exc, "status_code"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": getattr(exc, "detail", "An error occurred")},
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle ValueError exceptions from model updates."""
    return JSONResponse(
        status_code=400,
        content={"detail": "Bad Request", "errors": [{"field": "body", "message": str(exc)}]},
    )
