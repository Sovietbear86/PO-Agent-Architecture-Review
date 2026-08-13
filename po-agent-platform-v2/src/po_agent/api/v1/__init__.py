"""API version 1 routes for PO Agent Platform v2."""

import time
import uuid

from fastapi import APIRouter, Request
from pydantic import BaseModel

from po_agent import __app_name__
from po_agent.adapters import AS21SourceError
from po_agent.config import get_settings
from po_agent.harness import HarnessRequest, HarnessRuntime
from po_agent.harness.runtime_factory import RuntimeBundle, build_runtime_bundle

router = APIRouter()

_runtime: HarnessRuntime | None = None
_bundle: RuntimeBundle | None = None


class QueryRequest(BaseModel):
    query: str
    session_id: str | None = None


def get_runtime_bundle() -> RuntimeBundle:
    """Build the process-wide runtime from explicit environment settings."""
    global _bundle, _runtime
    if _bundle is None:
        settings = get_settings()
        _bundle = build_runtime_bundle(
            settings.as21_mode,
            task_api_base_url=settings.task_api_base_url,
            task_api_timeout_seconds=settings.task_api_timeout_seconds,
            team_config_path=settings.team_config_path,
        )
        _runtime = _bundle.runtime
    return _bundle


def get_runtime() -> HarnessRuntime:
    global _runtime
    if _runtime is not None:
        return _runtime
    return get_runtime_bundle().runtime


def set_runtime(runtime: HarnessRuntime | None) -> None:
    """Override/reset runtime for tests. Resetting also clears the runtime bundle."""
    global _runtime, _bundle
    _runtime = runtime
    _bundle = None


@router.get("/health")
async def health_check(request: Request):
    """Report application health, configured source and source readiness.

    For task-api mode the endpoint performs a tiny read probe. Failure is
    surfaced as degraded source health and is never interpreted as an empty
    portfolio.
    """
    settings = get_settings()
    correlation_id = request.headers.get(
        settings.correlation_id_header, str(uuid.uuid4())
    )
    bundle = get_runtime_bundle()
    source_status = "healthy"
    source_error = None
    if bundle.mode == "task-api":
        try:
            await bundle.adapter.search_tasks("", max_results=1)
        except AS21SourceError as exc:
            source_status = "degraded"
            source_error = type(exc).__name__

    readiness = bundle.readiness.summary()
    return {
        "status": "healthy" if source_status == "healthy" else "degraded",
        "service": __app_name__,
        "runtime": "harness-recovery",
        "adapter": bundle.mode,
        "source_status": source_status,
        "source_error": source_error,
        "source_facts": list(bundle.readiness.available_facts),
        "skill_readiness": readiness,
        "correlation_id": correlation_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


@router.post("/query")
async def query_agent(payload: QueryRequest, request: Request):
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
