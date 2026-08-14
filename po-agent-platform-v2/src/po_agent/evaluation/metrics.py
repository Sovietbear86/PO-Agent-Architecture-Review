"""Skill Evaluation Metrics for PO Agent Platform v2.

Metrics for tracking skill performance over time.

Metrics:
- accuracy: percentage of correct answers
- latency_ms: average latency
- confidence: average intent confidence
- coverage: percentage of requests handled by skill
- clarification_rate: percentage of requests needing clarification
- error_rate: percentage of failed executions
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class SkillMetrics(BaseModel):
    """Skill performance metrics."""
    skill_id: str
    skill_version: str
    timestamp: datetime
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    clarification_required: int = 0
    avg_latency_ms: float = 0.0
    avg_confidence: float = 0.0
    ratings: List[int] = []  # 1-5 skill ratings

    @property
    def accuracy(self) -> float:
        """Calculate accuracy."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

    @property
    def error_rate(self) -> float:
        """Calculate error rate."""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests

    @property
    def clarification_rate(self) -> float:
        """Calculate clarification rate."""
        if self.total_requests == 0:
            return 0.0
        return self.clarification_required / self.total_requests

    @property
    def avg_rating(self) -> float:
        """Calculate average rating."""
        if not self.ratings:
            return 0.0
        return sum(self.ratings) / len(self.ratings)


class SkillEvaluation:
    """Skill evaluation and metrics tracking."""

    def __init__(self):
        """Initialize skill evaluation."""
        self._metrics: Dict[str, Dict[str, SkillMetrics]] = {}
        self._evaluated_at: Optional[str] = None

    def record_request(
        self,
        skill_id: str,
        skill_version: str,
        latency_ms: float,
        confidence: float,
        success: bool,
        clarification_required: bool = False,
    ) -> None:
        """Record a request.

        Args:
            skill_id: Skill ID
            skill_version: Skill version
            latency_ms: Request latency
            confidence: Intent confidence
            success: Whether request succeeded
            clarification_required: Whether clarification was needed
        """
        key = f"{skill_id}:{skill_version}"

        if key not in self._metrics:
            self._metrics[key] = {}

        if skill_version not in self._metrics[key]:
            self._metrics[key][skill_version] = SkillMetrics(
                skill_id=skill_id,
                skill_version=skill_version,
                timestamp=datetime.now(),
            )

        metrics = self._metrics[key][skill_version]
        metrics.total_requests += 1

        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1

        if clarification_required:
            metrics.clarification_required += 1

        # Update average latency (running average)
        metrics.avg_latency_ms = (
            (metrics.avg_latency_ms * (metrics.total_requests - 1) + latency_ms)
            / metrics.total_requests
        )

        # Update average confidence
        metrics.avg_confidence = (
            (metrics.avg_confidence * (metrics.total_requests - 1) + confidence)
            / metrics.total_requests
        )

    def record_rating(
        self,
        skill_id: str,
        skill_version: str,
        rating: int,
    ) -> None:
        """Record a skill rating.

        Args:
            skill_id: Skill ID
            skill_version: Skill version
            rating: 1-5 rating
        """
        key = f"{skill_id}:{skill_version}"

        if key in self._metrics and skill_version in self._metrics[key]:
            self._metrics[key][skill_version].ratings.append(rating)

    def get_skill_metrics(self, skill_id: str) -> Optional[SkillMetrics]:
        """Get metrics for a skill.

        Args:
            skill_id: Skill ID

        Returns:
            Latest version metrics or None
        """
        if skill_id not in self._metrics:
            return None

        # Get latest version
        versions = self._metrics[skill_id]
        if not versions:
            return None

        # Return latest version
        latest_version = max(versions.keys())
        return versions[latest_version]

    def get_all_skills_metrics(self) -> List[SkillMetrics]:
        """Get metrics for all skills.

        Returns:
            List of skill metrics (latest version per skill)
        """
        metrics_list = []

        for skill_id, versions in self._metrics.items():
            if versions:
                latest_version = max(versions.keys())
                metrics_list.append(versions[latest_version])

        return metrics_list

    def get_skill_summary(self, skill_id: str) -> Dict[str, Any]:
        """Get summary of skill metrics.

        Args:
            skill_id: Skill ID

        Returns:
            Summary dict
        """
        metrics = self.get_skill_metrics(skill_id)

        if metrics is None:
            return {
                "skill_id": skill_id,
                "error": "No metrics found",
            }

        return {
            "skill_id": metrics.skill_id,
            "skill_version": metrics.skill_version,
            "total_requests": metrics.total_requests,
            "accuracy": metrics.accuracy,
            "error_rate": metrics.error_rate,
            "clarification_rate": metrics.clarification_rate,
            "avg_latency_ms": metrics.avg_latency_ms,
            "avg_confidence": metrics.avg_confidence,
            "avg_rating": metrics.avg_rating,
        }


# Export for convenience
__all__ = [
    "SkillMetrics",
    "SkillEvaluation",
]
