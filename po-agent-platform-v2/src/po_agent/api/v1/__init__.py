"""API version 1 routes for PO Agent Platform v2."""

import logging
import time
import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from po_agent import __app_name__
from po_agent.adapters import AS21SourceError
from po_agent.config import get_settings
from po_agent.harness import HarnessRequest, HarnessRuntime
from po_agent.harness.dialogue_runtime import LLMJsonSemanticInterpreter
from po_agent.harness.runtime_factory import RuntimeBundle, build_runtime_bundle
from po_agent.llm.real import RealLLMClient
from po_agent.ops.as21_diagnostics import build_as21_diagnostics

logger = logging.getLogger(__name__)
router = APIRouter()

_runtime: HarnessRuntime | None = None
_bundle: RuntimeBundle | None = None
_runtime_init_error: str | None = None


class QueryRequest(BaseModel):
    query: str
    session_id: str | None = None


class FeedbackRequest(BaseModel):
    rating: str
    correction: str | None = None
    expected_intent: str | None = None
    expected_entity: str | None = None
    comment: str | None = None


class SemanticLearningRequest(BaseModel):
    term: str
    meaning: str
    source_trace_id: str
    scope: str = "global"


def get_runtime_bundle() -> RuntimeBundle:
    """Build the process-wide runtime from explicit environment settings.

    Construction errors are logged with traceback and remembered for health/query
    diagnostics. They are never allowed to surface as an opaque HTTP 500.
    """
    global _bundle, _runtime, _runtime_init_error
    if _bundle is None:
        settings = get_settings()
        interpreter = None
        try:
            if settings.semantic_llm_enabled and settings.llm_api_key:
                llm = RealLLMClient(
                    api_key=settings.llm_api_key,
                    base_url=settings.llm_api_base_url,
                    model=settings.llm_model_name,
                    verify=settings.llm_tls_verify,
                )
                interpreter = LLMJsonSemanticInterpreter(llm, model=settings.llm_model_name)
            _bundle = build_runtime_bundle(
                settings.as21_mode,
                task_api_base_url=settings.task_api_base_url,
                task_api_timeout_seconds=settings.task_api_timeout_seconds,
                team_config_path=settings.team_config_path,
                semantic_interpreter=interpreter,
                learned_semantics_path=settings.learned_semantics_path,
                agent_core_v3_enabled=settings.agent_core_v3_enabled,
                agent_core_v4_enabled=settings.agent_core_v4_enabled,
            )
            _runtime = _bundle.runtime
            _runtime_init_error = None
        except Exception as exc:
            _runtime_init_error = f"{type(exc).__name__}: {exc}"
            logger.exception("PO Agent runtime initialization failed")
            raise
    return _bundle


def get_runtime() -> HarnessRuntime:
    global _runtime
    if _runtime is not None:
        return _runtime
    return get_runtime_bundle().runtime


def set_runtime(runtime: HarnessRuntime | None) -> None:
    """Override/reset runtime for tests. Resetting also clears the runtime bundle."""
    global _runtime, _bundle, _runtime_init_error
    _runtime = runtime
    _bundle = None
    _runtime_init_error = None


def _decorate_v4_response(response: dict, bundle: RuntimeBundle) -> dict:
    """Attach presentation metadata without letting UI contracts control execution."""
    response["runtime"] = "agent_core_v4"
    runtime = bundle.v4_runtime
    skill = response.get("skill")
    skill_id = str(skill.get("id") or "").strip() if isinstance(skill, dict) else ""
    contract = runtime.ui_contract(skill_id) if runtime is not None and skill_id and hasattr(runtime, "ui_contract") else None
    response["ui"] = contract.compact() if contract is not None else None
    if runtime is not None and hasattr(runtime, "plugin_ids"):
        response["plugin_ids"] = list(runtime.plugin_ids)
    return response


def _v4_failure_response(session_id: str, exc: Exception) -> dict:
    return {
        "status": "FAILED",
        "answer": "Agent Core v4 завершил выполнение fail-closed из-за внутренней ошибки.",
        "question": None,
        "options": [],
        "clarification_id": None,
        "intent": "skill_native_v4",
        "skill": None,
        "data": {"_agent_core_v4": {"exception_type": type(exc).__name__}},
        "evidence": [],
        "warnings": ["v4_internal_error"],
        "trace_id": str(uuid.uuid4()),
        "session_id": session_id,
        "latency_ms": 0.0,
        "runtime": "agent_core_v4",
        "ui": None,
    }


@router.get("/health")
async def health_check(request: Request):
    settings = get_settings()
    correlation_id = request.headers.get(settings.correlation_id_header, str(uuid.uuid4()))
    try:
        bundle = get_runtime_bundle()
    except Exception:
        return {
            "status": "degraded",
            "service": __app_name__,
            "runtime": "harness-dialogue-v2",
            "browser_runtime": "unavailable",
            "adapter": settings.as21_mode,
            "semantic_mode": "qwen-llm" if settings.semantic_llm_enabled and settings.llm_api_key else "fail-closed",
            "agent_core_v3_enabled": settings.agent_core_v3_enabled,
            "agent_core_v4_enabled": settings.agent_core_v4_enabled,
            "agent_core_v4_ready": False,
            "source_status": "unknown",
            "runtime_init_error": _runtime_init_error,
            "correlation_id": correlation_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    source_status = "healthy"
    source_error = None
    if bundle.mode == "task-api":
        try:
            await bundle.adapter.search_tasks("", max_results=1)
        except AS21SourceError as exc:
            source_status = "degraded"
            source_error = type(exc).__name__

    readiness = bundle.readiness.summary()
    semantic_mode = "qwen-llm" if settings.semantic_llm_enabled and settings.llm_api_key else "fail-closed"
    v4_ready = settings.agent_core_v4_enabled and bundle.v4_runtime is not None
    return {
        "status": "healthy" if source_status == "healthy" else "degraded",
        "service": __app_name__,
        "runtime": "harness-dialogue-v2",
        "browser_runtime": "agent_core_v4" if v4_ready else "legacy_harness",
        "adapter": bundle.mode,
        "semantic_mode": semantic_mode,
        "agent_core_v3_enabled": settings.agent_core_v3_enabled,
        "agent_core_v4_enabled": settings.agent_core_v4_enabled,
        "agent_core_v4_ready": bundle.v4_runtime is not None,
        "v4_plugin_ids": list(bundle.v4_runtime.plugin_ids) if v4_ready and hasattr(bundle.v4_runtime, "plugin_ids") else [],
        "source_status": source_status,
        "source_error": source_error,
        "runtime_init_error": None,
        "source_facts": list(bundle.readiness.available_facts),
        "skill_readiness": readiness,
        "correlation_id": correlation_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


@router.get("/ops/as21-diagnostics")
async def as21_diagnostics():
    """Non-secret runtime diagnostic for AS21/SWTR connectivity and wiring."""
    return await build_as21_diagnostics(get_settings())


@router.post("/query")
async def query_agent(payload: QueryRequest, request: Request):
    """Browser/API query entrypoint.

    When V4 is explicitly enabled and ready, the same public endpoint executes the
    pluginized V4 runtime. The frontend never chooses skills, capabilities or source
    routes. If V4 is disabled/not ready, the existing Harness path is preserved.
    """
    settings = get_settings()
    correlation_id = request.headers.get(settings.correlation_id_header, str(uuid.uuid4()))
    session_id = payload.session_id or request.headers.get("X-Session-Id") or str(uuid.uuid4())
    bundle = get_runtime_bundle()
    use_v4 = settings.agent_core_v4_enabled and bundle.v4_runtime is not None
    try:
        if use_v4:
            result = await bundle.v4_runtime.process(HarnessRequest(query=payload.query, session_id=session_id))
            response = _decorate_v4_response(result.to_dict(), bundle)
        else:
            result = await get_runtime().process(HarnessRequest(query=payload.query, session_id=session_id))
            response = result.to_dict()
            response["runtime"] = "legacy_harness"
            response["ui"] = None
    except Exception as exc:
        logger.exception("PO Agent query failed", extra={"correlation_id": correlation_id, "session_id": session_id})
        if use_v4:
            response = _v4_failure_response(session_id, exc)
        else:
            response = {
                "status": "FAILED",
                "answer": "Внутренняя ошибка Harness. Выполнение остановлено без интерпретации результата как успешного.",
                "question": None,
                "options": [],
                "clarification_id": None,
                "intent": None,
                "skill": None,
                "data": {
                    "_harness": {
                        "execution_ready": False,
                        "runtime_init_error": _runtime_init_error,
                        "exception_type": type(exc).__name__,
                    }
                },
                "evidence": [],
                "warnings": ["harness_internal_error"],
                "trace_id": str(uuid.uuid4()),
                "session_id": session_id,
                "latency_ms": 0.0,
                "runtime": "legacy_harness",
                "ui": None,
            }
    response["correlation_id"] = correlation_id
    return response


@router.post("/query-v4")
async def query_agent_v4(payload: QueryRequest, request: Request):
    """Explicit V4 endpoint retained for independent A/B/C and rollback QA."""
    settings = get_settings()
    correlation_id = request.headers.get(settings.correlation_id_header, str(uuid.uuid4()))
    session_id = payload.session_id or request.headers.get("X-Session-Id") or str(uuid.uuid4())
    bundle = get_runtime_bundle()
    if not settings.agent_core_v4_enabled or bundle.v4_runtime is None:
        raise HTTPException(status_code=503, detail="Agent Core v4 POC is not enabled/ready")
    try:
        result = await bundle.v4_runtime.process(HarnessRequest(query=payload.query, session_id=session_id))
        response = _decorate_v4_response(result.to_dict(), bundle)
    except Exception as exc:
        logger.exception("Agent Core v4 query failed", extra={"correlation_id": correlation_id, "session_id": session_id})
        response = _v4_failure_response(session_id, exc)
    response["correlation_id"] = correlation_id
    return response


@router.post("/feedback/{trace_id}")
async def submit_feedback(trace_id: str, payload: FeedbackRequest):
    runtime = get_runtime()
    if not hasattr(runtime, "submit_feedback"):
        raise HTTPException(status_code=501, detail="feedback is unavailable for this runtime")
    try:
        record = runtime.submit_feedback(
            trace_id,
            payload.rating,
            correction=payload.correction,
            expected_intent=payload.expected_intent,
            expected_entity=payload.expected_entity,
            comment=payload.comment,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"feedback_id": record.feedback_id, "trace_id": trace_id, "status": "recorded"}


@router.post("/learning/semantic")
async def learn_semantic(payload: SemanticLearningRequest):
    bundle = get_runtime_bundle()
    if bundle.semantics is None:
        raise HTTPException(status_code=501, detail="learned semantics store is unavailable")
    rule = bundle.semantics.learn_explicit_definition(
        term=payload.term,
        meaning=payload.meaning,
        source_trace_id=payload.source_trace_id,
        scope=payload.scope,
    )
    return {
        "rule_id": rule.rule_id,
        "term": rule.term,
        "meaning": rule.meaning,
        "scope": rule.scope,
        "version": rule.version,
        "status": rule.status,
    }
