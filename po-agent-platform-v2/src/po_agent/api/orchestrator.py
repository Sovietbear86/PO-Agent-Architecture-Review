"""FastAPI Orchestrator API for PO Agent Platform v2.

HTTP API endpoints:
- GET /api/v1/health - Health check
- GET /api/v1/dashboard/stats - Dashboard statistics
- GET /api/v1/prompts - List prompts
- POST /api/v1/promotions/promote - Create promotion
- POST /api/v1/promotions/rollback - Create rollback
- POST /api/v1/shadow/config - Create shadow config
- POST /api/v1/shadow/comparison - Create comparison
- POST /api/v1/gates/check - Check regression gate
- POST /api/v1/approvals/request - Request approval
- GET /api/v1/failures - List failures
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from po_agent.dashboard.api import AIPDLCDashboard
from po_agent.shadow.mode import ShadowModeStore
from po_agent.shadow.comparison import ComparisonEngine
from po_agent.shadow.gate import RegressionGate
from po_agent.shadow.promotion import PromotionManager
from po_agent.shadow.approval import HumanApprovalGate
from po_agent.evaluation.failure import FailureStore


# Pydantic models for request/response
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime


class DashboardStats(BaseModel):
    prompts: dict
    versions: dict
    promotions: dict
    gates: dict
    approvals: dict
    failures: dict
    improvements: dict
    shadow_modes: dict
    comparisons: dict


class PromptResponse(BaseModel):
    prompt_name: str
    version: int
    status: str
    created_at: str


class PromotionRequest(BaseModel):
    prompt_name: str
    from_version: int
    to_version: int
    requested_by: Optional[str] = None


class RollbackRequest(BaseModel):
    prompt_name: str
    from_version: int
    to_version: int
    rollback_reason: str
    requested_by: Optional[str] = None


class ShadowConfigRequest(BaseModel):
    prompt_name: str
    shadow_version: int
    comparison_threshold: float = 0.9
    enabled: bool = True
    created_by: Optional[str] = None


class ComparisonRequest(BaseModel):
    config_id: str
    prompt_name: str
    prod_version: int
    shadow_version: int
    prod_output: str
    shadow_output: str
    threshold: float = 0.8


class GateCheckRequest(BaseModel):
    prompt_name: str
    shadow_version: int
    comparisons: List[dict]
    threshold: float = 0.8
    reviewed_by: Optional[str] = None


class ApprovalRequest(BaseModel):
    gate_record_id: str
    prompt_name: str
    shadow_version: int
    requested_by: Optional[str] = None
    approval_reason: Optional[str] = None


class FailureResponse(BaseModel):
    id: str
    trace_id: str
    error_message: str
    intent: Optional[str]
    entities: Optional[dict]
    capability: Optional[str]
    category: str
    timestamp: str


# Global instances for shared state (used in testing)
_dashboard = None
_promotion_manager = None
_shadow_store = None
_comparison_engine = None
_regression_gate = None
_approval_gate = None
_failure_store = None


def get_dashboard():
    """Get dashboard instance (single shared instance for testing)."""
    global _dashboard
    if _dashboard is None:
        _dashboard = AIPDLCDashboard()
    return _dashboard


def get_shadow_store():
    """Get shadow store instance (single shared instance for testing)."""
    global _shadow_store
    if _shadow_store is None:
        _shadow_store = ShadowModeStore()
    return _shadow_store


def get_comparison_engine():
    """Get comparison engine instance (single shared instance for testing)."""
    global _comparison_engine
    if _comparison_engine is None:
        _comparison_engine = ComparisonEngine()
    return _comparison_engine


def get_regression_gate():
    """Get regression gate instance (single shared instance for testing)."""
    global _regression_gate
    if _regression_gate is None:
        _regression_gate = RegressionGate()
    return _regression_gate


def get_promotion_manager():
    """Get promotion manager instance (single shared instance for testing)."""
    global _promotion_manager
    if _promotion_manager is None:
        _promotion_manager = PromotionManager()
    return _promotion_manager


def get_approval_gate():
    """Get human approval gate instance (single shared instance for testing)."""
    global _approval_gate
    if _approval_gate is None:
        _approval_gate = HumanApprovalGate()
    return _approval_gate


def get_failure_store():
    """Get failure store instance (single shared instance for testing)."""
    global _failure_store
    if _failure_store is None:
        _failure_store = FailureStore()
    return _failure_store


# Create FastAPI app
app = FastAPI(
    title="PO Agent Platform Orchestrator API",
    description="API for managing AI PDLC processes",
    version="1.0.0",
)


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", timestamp=datetime.now())


@app.get("/api/v1/dashboard/stats")
async def get_dashboard_stats():
    """Get overall dashboard statistics."""
    dashboard = get_dashboard()
    try:
        return dashboard.get_stats()
    finally:
        pass  # Shared instance for testing


@app.get("/api/v1/prompts")
async def list_prompts(
    limit: int = Query(50, le=100),
):
    """List all prompts with versions."""
    dashboard = get_dashboard()
    try:
        prompts = dashboard.get_prompts(limit=limit)
        return {"prompts": prompts, "total": len(prompts)}
    finally:
        pass  # Shared instance for testing


@app.post("/api/v1/promotions/promote")
async def create_promotion(
    request: PromotionRequest,
):
    """Create a promotion record."""
    promotion_manager = get_promotion_manager()
    try:
        record = promotion_manager.create_promotion(
            prompt_name=request.prompt_name,
            from_version=request.from_version,
            to_version=request.to_version,
            requested_by=request.requested_by,
        )
        return {"promotion": record.to_dict()}
    finally:
        pass  # Shared instance for testing


@app.post("/api/v1/promotions/rollback")
async def create_rollback(
    request: RollbackRequest,
):
    """Create a rollback record."""
    promotion_manager = get_promotion_manager()
    try:
        record = promotion_manager.create_rollback(
            prompt_name=request.prompt_name,
            from_version=request.from_version,
            to_version=request.to_version,
            rollback_reason=request.rollback_reason,
            requested_by=request.requested_by,
        )
        return {"rollback": record.to_dict()}
    finally:
        pass  # Shared instance for testing


@app.post("/api/v1/shadow/config")
async def create_shadow_config(
    request: ShadowConfigRequest,
):
    """Create a shadow mode configuration."""
    shadow_store = get_shadow_store()
    try:
        record = shadow_store.add_config(
            prompt_name=request.prompt_name,
            shadow_version=request.shadow_version,
            comparison_threshold=request.comparison_threshold,
            enabled=request.enabled,
            created_by=request.created_by,
        )
        return {"shadow_config": record.to_dict()}
    finally:
        pass  # Shared instance for testing


@app.post("/api/v1/shadow/comparison")
async def create_comparison(
    request: ComparisonRequest,
):
    """Create a comparison record."""
    comparison_engine = get_comparison_engine()
    try:
        record = comparison_engine.compare(
            config_id=request.config_id,
            prompt_name=request.prompt_name,
            prod_version=request.prod_version,
            shadow_version=request.shadow_version,
            prod_output=request.prod_output,
            shadow_output=request.shadow_output,
            threshold=request.threshold,
        )
        return {"comparison": record.to_dict()}
    finally:
        pass  # Shared instance for testing


@app.post("/api/v1/gates/check")
async def check_gate(
    request: GateCheckRequest,
):
    """Check regression gate."""
    regression_gate = get_regression_gate()
    try:
        record = regression_gate.check(
            prompt_name=request.prompt_name,
            shadow_version=request.shadow_version,
            comparisons=request.comparisons,
            threshold=request.threshold,
            reviewed_by=request.reviewed_by,
        )
        return {"gate_result": record.to_dict()}
    finally:
        pass  # Shared instance for testing


@app.post("/api/v1/approvals/request")
async def request_approval(
    request: ApprovalRequest,
):
    """Request human approval."""
    approval_gate = get_approval_gate()
    try:
        record = approval_gate.request_approval(
            gate_record_id=request.gate_record_id,
            prompt_name=request.prompt_name,
            shadow_version=request.shadow_version,
            requested_by=request.requested_by,
            approval_reason=request.approval_reason,
        )
        return {"approval_request": record.to_dict()}
    finally:
        pass  # Shared instance for testing


@app.get("/api/v1/failures")
async def list_failures(
    limit: int = Query(50, le=100),
):
    """List failure records."""
    failure_store = get_failure_store()
    try:
        failures = failure_store.get_all_failures()
        return {
            "failures": [f.to_dict() for f in failures[:limit]],
            "total": len(failures),
        }
    finally:
        pass  # Shared instance for testing


@app.get("/api/v1/gates")
async def list_gates(
    limit: int = Query(50, le=100),
):
    """List gate records."""
    regression_gate = get_regression_gate()
    try:
        return {
            "gates": [g.to_dict() for g in regression_gate.gates[:limit]],
            "total": len(regression_gate.gates),
        }
    finally:
        pass  # Shared instance for testing


@app.get("/api/v1/approvals")
async def list_approvals(
    limit: int = Query(50, le=100),
):
    """List approval records."""
    approval_gate = get_approval_gate()
    try:
        return {
            "approvals": [a.to_dict() for a in approval_gate.approvals[:limit]],
            "total": len(approval_gate.approvals),
        }
    finally:
        pass  # Shared instance for testing


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
