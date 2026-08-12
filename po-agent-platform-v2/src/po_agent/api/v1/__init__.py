"""API version 1 routes for PO Agent Platform v2."""

import os
import time
import uuid

from fastapi import APIRouter, Request

from po_agent import __app_name__, __version__
from po_agent.config import get_settings
from po_agent.orchestration.orchestrator import POOrchestratorV1
from po_agent.history.store import OperationalHistory
from po_agent.feedback.store import FeedbackStore
from po_agent.llm.real import RealLLMClient

router = APIRouter()

# Global orchestrator instance
_orchestrator = None


def get_orchestrator():
    """Get or create orchestrator instance with real LLM client."""
    global _orchestrator
    if _orchestrator is None:
        # Try to get API key from environment or file
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            try:
                with open("/Users/kalachanov.v.v/.config/openai/api_key", "r") as f:
                    api_key = f.read().strip()
            except:
                api_key = None

        # Create LLM client (RealLLMClient or fallback to Mock)
        llm_client = None
        if api_key:
            try:
                llm_client = RealLLMClient(api_key=api_key)
            except Exception as e:
                print(f"Warning: Could not create RealLLMClient: {e}")

        _orchestrator = POOrchestratorV1(
            llm_client=llm_client,
            history_db_path=":memory:",
            feedback_db_path=":memory:",
        )
    return _orchestrator


@router.get("/health")
async def health_check(request: Request):
    """Health check endpoint with correlation ID."""
    settings = get_settings()
    correlation_id = request.headers.get(
        settings.correlation_id_header, str(uuid.uuid4())
    )
    return {
        "status": "healthy",
        "service": __app_name__,
        "correlation_id": correlation_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


@router.post("/query")
async def query_agent(request: Request):
    """Process query through PO Orchestrator."""
    from pydantic import BaseModel
    
    class QueryRequest(BaseModel):
        query: str
        session_id: str | None = None
    
    settings = get_settings()
    correlation_id = request.headers.get(
        settings.correlation_id_header, str(uuid.uuid4())
    )
    
    try:
        data = await request.json()
        query_req = QueryRequest(**data)
        
        orchestrator = get_orchestrator()
        result = await orchestrator.process_request(
            query=query_req.query,
            session_id=query_req.session_id,
        )
        
        return {
            "correlation_id": correlation_id,
            "intent": result["intent"],
            "intent_confidence": result["intent_confidence"],
            "response": result["response"],
            "evidence": result["evidence"],
        }
    except Exception as e:
        return {
            "correlation_id": correlation_id,
            "error": str(e),
            "response": "Sorry, I couldn't process your request.",
        }
