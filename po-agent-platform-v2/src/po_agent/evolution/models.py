"""Skill Evolution models for PO Agent Platform v2.

Supports:
- Skill improvement candidate detection
- Automatic version bumping
- Human-in-the-loop approval workflow
- Feedback-driven improvements

Improvement types:
- low_accuracy: accuracy below threshold
- high_clarification_rate: too many clarification requests
- low_rating: user ratings below threshold
- high_error_rate: too many failures
- high_latency: latency above threshold
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import BaseModel


class ImprovementType(Enum):
    """Type of skill improvement."""
    LOW_ACCURACY = "low_accuracy"
    HIGH_CLARIFICATION_RATE = "high_clarification_rate"
    LOW_RATING = "low_rating"
    HIGH_ERROR_RATE = "high_error_rate"
    HIGH_LATENCY = "high_latency"
    HIGH_CONFIDENCE_VARIANCE = "high_confidence_variance"


class CandidateStatus(Enum):
    """Status of improvement candidate."""
    IDENTIFIED = "identified"
    ANALYZED = "analyzed"
    PROPOSED = "proposed"
    APPROVED = "approved"
    IMPLEMENTED = "implemented"
    REJECTED = "rejected"


class SkillImprovementCandidate(BaseModel):
    """Candidate for skill improvement.

    Created when metrics indicate skill needs improvement.
    """

    candidate_id: str
    skill_id: str
    skill_version: str
    improvement_type: ImprovementType
    threshold_value: float
    current_value: float
    feedback_samples: List[Dict[str, Any]] = []
    metric_samples: List[Dict[str, Any]] = []
    suggested_changes: Dict[str, Any] = {}
    created_at: datetime = datetime.now()
    analyzed_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    implemented_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    created_by: Optional[str] = None
    analyzed_by: Optional[str] = None
    approved_by: Optional[str] = None
    implemented_by: Optional[str] = None
    rejected_by: Optional[str] = None
    status: CandidateStatus = CandidateStatus.IDENTIFIED

    def analyze(self, analyzed_by: Optional[str] = None) -> None:
        """Move to analyzed status."""
        self.status = CandidateStatus.ANALYZED
        self.analyzed_at = datetime.now()
        self.analyzed_by = analyzed_by

    def propose(self) -> None:
        """Move to proposed status (ready for approval)."""
        self.status = CandidateStatus.PROPOSED

    def approve(self, approved_by: str) -> None:
        """Approve improvement."""
        self.status = CandidateStatus.APPROVED
        self.approved_at = datetime.now()
        self.approved_by = approved_by

    def implement(self, implemented_by: str, new_version: str) -> None:
        """Mark improvement as implemented."""
        self.status = CandidateStatus.IMPLEMENTED
        self.implemented_at = datetime.now()
        self.implemented_by = implemented_by
        self.skill_version = new_version

    def reject(self, rejected_by: str, reason: Optional[str] = None) -> None:
        """Reject improvement."""
        self.status = CandidateStatus.REJECTED
        self.rejected_at = datetime.now()
        self.rejected_by = rejected_by
        if reason:
            self.suggested_changes["rejection_reason"] = reason


class EvolutionThresholds(BaseModel):
    """Thresholds for improvement detection."""
    accuracy_threshold: float = 0.7
    clarification_rate_threshold: float = 0.3
    rating_threshold: float = 3.0
    error_rate_threshold: float = 0.15
    latency_threshold_ms: float = 500.0
    confidence_variance_threshold: float = 0.3


class SkillEvolutionConfig(BaseModel):
    """Configuration for skill evolution pipeline."""
    thresholds: EvolutionThresholds = EvolutionThresholds()
    min_samples_for_analysis: int = 10
    max_candidates_per_skill: int = 5
    auto_approve_rating: Optional[int] = 4  # If rating >= this, auto-approve
    human_approval_required: bool = True


# Export for convenience
__all__ = [
    "ImprovementType",
    "CandidateStatus",
    "SkillImprovementCandidate",
    "EvolutionThresholds",
    "SkillEvolutionConfig",
]
