"""API version 1 routes for PO Agent Platform v2.

The recovery branch deliberately exposes the new harness runtime through the
stable `/api/v1/query` contract. It runs with FakeAS21Adapter by default so the
vertical slice is executable without SWTR or an LLM.
"""

import time
import uuid

from fastapi import APIRouter, Request
from pydantic import BaseModel

from po_agent import __app_name__
from po_agent.config import get_settings
from po_agent.harness import HarnessRequest, HarnessRuntime, build_fake_runtime

router = APIRouter()

_runtime: HarnessRuntime | None = None


class QueryRequest(BaseModel):
    query: str
    session_id: str | None = None


def get_runtime() -> HarnessRuntime:
    """Return the process-wide recovery runtime.

    FakeAS21Adapter is intentional for the first acceptance gate. The real SWTR
    adapter will be injected here after the deterministic harness contract and
    UI vertical slice are green.
    """
    global _runtime
    if _runtime is None:
        _runtime = build_fake_runtime()
    return _runtime


def set_runtime(runtime: HarnessRuntime | None) -> None:
    """Override/reset runtime for tests and later dependency injection."""
    global _runtime
    _runtime = runtime


@router.get("/health")
async def health_check(request: Request):
    """Health check endpoint with correlation ID and recovery runtime mode."""
    settings = get_settings()
    correlation_id = request.headers.get(
        settings.correlation_id_header, str(uuid.uuid4())
    )
    return {
        "status": "healthy",
        "service": __app_name__,
        "runtime": "harness-recovery",
        "adapter": "fake-as21",
        "correlation_id": correlation_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


@router.post("/query")
async def query_agent(payload: QueryRequest, request: Request):
    """Process a query through the executable skill-driven Harness Core."""
    settings = get_settings()
    correlation_id = request.headers.get(
        settings.correlation_id_header, str(uuid.uuid4())
    )

    result = await get_runtime().process(
        HarnessRequest(query=payload.query, session_id=payload.session_id)
    )
    response = result.to_dict()
    response["correlation_id"] = correlation_id
    return response
