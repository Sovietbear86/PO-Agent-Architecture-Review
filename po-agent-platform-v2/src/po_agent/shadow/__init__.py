"""Shadow module for PO Agent Platform v2."""

from po_agent.shadow.mode import (
    ShadowModeEntry,
    ShadowModeStore,
    ShadowModeStatus,
)
from po_agent.shadow.comparison import (
    ComparisonEngine,
    ComparisonRecord,
    ComparisonResult,
)
from po_agent.shadow.gate import (
    RegressionGate,
    RegressionGateRecord,
    GateStatus,
)
from po_agent.shadow.approval import (
    HumanApprovalGate,
    HumanApprovalRecord,
    ApprovalStatus,
)
from po_agent.shadow.promotion import (
    PromotionManager,
    PromotionRecord,
    PromotionAction,
    PromotionStatus,
)

__all__ = [
    "ShadowModeEntry",
    "ShadowModeStore",
    "ShadowModeStatus",
    "ComparisonEngine",
    "ComparisonRecord",
    "ComparisonResult",
    "RegressionGate",
    "RegressionGateRecord",
    "GateStatus",
    "HumanApprovalGate",
    "HumanApprovalRecord",
    "ApprovalStatus",
    "PromotionManager",
    "PromotionRecord",
    "PromotionAction",
    "PromotionStatus",
]
