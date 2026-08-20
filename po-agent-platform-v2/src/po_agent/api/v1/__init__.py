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
            "adapter": settings.as21_mode,
            "semantic_mode": "qwen-llm" if settings.semantic_llm_enabled and settings.llm_api_key else "conservative-fallback",
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
    semantic_mode = "qwen-llm" if settings.semantic_llm_enabled and settings.llm_api_key else "conservative-fallback"
    return {
        "status": "healthy" if source_status == "healthy" else "degraded",
        "service": __app_name__,
        "runtime": "harness-dialogue-v2",
        "adapter": bundle.mode,
        "semantic_mode": semantic_mode,
        "source_status": source_status,
        "source_error": source_error,
        "runtime_init_error": None,
        "source_facts": list(bundle.readiness.available_facts),
        "skill_readiness": readiness,
        "correlation_id": correlation_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


@router.post("/query")
async def query_agent(payload: QueryRequest, request: Request):
    settings = get_settings()
    correlation_id = request.headers.get(settings.correlation_id_header, str(uuid.uuid4()))
    session_id = payload.session_id or str(uuid.uuid4())
    try:
        result = await get_runtime().process(HarnessRequest(query=payload.query, session_id=session_id))
        response = result.to_dict()
    except Exception as exc:
        # A Harness endpoint must fail closed as a typed response, never as an
        # opaque web-server 500. The traceback remains in server logs for QA.
        logger.exception("PO Agent query failed", extra={"correlation_id": correlation_id, "session_id": session_id})
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
        }
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
