"""Skill Evolution Pipeline for PO Agent Platform v2.

Automatic detection of skill improvement candidates based on metrics.

Features:
- Analyze metrics for improvement opportunities
- Generate improvement candidates
- Support human-in-the-loop approval
- Integrate with SkillRegistry for version management
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from po_agent.skill.registry import SkillRegistry
from po_agent.skill.models import SkillDefinition, SkillStatus
from po_agent.evaluation.metrics import SkillEvaluation, SkillMetrics
from po_agent.evolution.models import (
    ImprovementType,
    CandidateStatus,
    SkillImprovementCandidate,
    EvolutionThresholds,
    SkillEvolutionConfig,
)


class SkillEvolutionPipeline:
    """Pipeline for skill improvement and evolution.

    Workflow:
    1. Collect metrics for all skills
    2. Check against thresholds
    3. Generate improvement candidates
    4. Analyze candidates (optional)
    5. Propose to human for approval
    6. On approval, create new version
    """

    def __init__(
        self,
        skill_registry: SkillRegistry,
        skill_evaluation: Optional[SkillEvaluation] = None,
        config: Optional[SkillEvolutionConfig] = None,
    ):
        """Initialize evolution pipeline.

        Args:
            skill_registry: Skill registry with skills
            skill_evaluation: Evaluation metrics storage
            config: Evolution configuration
        """
        self.registry = skill_registry
        self.evaluation = skill_evaluation or SkillEvaluation()
        self.config = config or SkillEvolutionConfig()
        self._candidates: Dict[str, SkillImprovementCandidate] = {}

    def analyze_all_skills(self) -> List[SkillImprovementCandidate]:
        """Analyze all skills for improvement opportunities.

        Returns:
            List of improvement candidates
        """
        candidates = []
        all_metrics = self.evaluation.get_all_skills_metrics()

        for metrics in all_metrics:
            candidate = self._check_skill_metrics(metrics)
            if candidate:
                candidates.append(candidate)

        return candidates

    def _check_skill_metrics(
        self,
        metrics: SkillMetrics,
    ) -> Optional[SkillImprovementCandidate]:
        """Check if skill needs improvement based on metrics.

        Args:
            metrics: Skill metrics

        Returns:
            Improvement candidate or None
        """
        thresholds = self.config.thresholds

        # Check low accuracy
        if metrics.accuracy < thresholds.accuracy_threshold:
            return self._create_candidate(
                skill_id=metrics.skill_id,
                skill_version=metrics.skill_version,
                improvement_type=ImprovementType.LOW_ACCURACY,
                threshold_value=thresholds.accuracy_threshold,
                current_value=metrics.accuracy,
            )

        # Check high clarification rate
        if metrics.clarification_rate > thresholds.clarification_rate_threshold:
            return self._create_candidate(
                skill_id=metrics.skill_id,
                skill_version=metrics.skill_version,
                improvement_type=ImprovementType.HIGH_CLARIFICATION_RATE,
                threshold_value=thresholds.clarification_rate_threshold,
                current_value=metrics.clarification_rate,
            )

        # Check low rating
        if metrics.avg_rating > 0 and metrics.avg_rating < thresholds.rating_threshold:
            return self._create_candidate(
                skill_id=metrics.skill_id,
                skill_version=metrics.skill_version,
                improvement_type=ImprovementType.LOW_RATING,
                threshold_value=thresholds.rating_threshold,
                current_value=metrics.avg_rating,
            )

        # Check high error rate
        if metrics.error_rate > thresholds.error_rate_threshold:
            return self._create_candidate(
                skill_id=metrics.skill_id,
                skill_version=metrics.skill_version,
                improvement_type=ImprovementType.HIGH_ERROR_RATE,
                threshold_value=thresholds.error_rate_threshold,
                current_value=metrics.error_rate,
            )

        # Check high latency
        if metrics.avg_latency_ms > thresholds.latency_threshold_ms:
            return self._create_candidate(
                skill_id=metrics.skill_id,
                skill_version=metrics.skill_version,
                improvement_type=ImprovementType.HIGH_LATENCY,
                threshold_value=thresholds.latency_threshold_ms,
                current_value=metrics.avg_latency_ms,
            )

        return None

    def _create_candidate(
        self,
        skill_id: str,
        skill_version: str,
        improvement_type: ImprovementType,
        threshold_value: float,
        current_value: float,
    ) -> SkillImprovementCandidate:
        """Create improvement candidate.

        Args:
            skill_id: Skill ID
            skill_version: Skill version
            improvement_type: Type of improvement
            threshold_value: Threshold value
            current_value: Current value

        Returns:
            Improvement candidate
        """
        candidate = SkillImprovementCandidate(
            candidate_id=f"improve-{skill_id}-{uuid.uuid4().hex[:8]}",
            skill_id=skill_id,
            skill_version=skill_version,
            improvement_type=improvement_type,
            threshold_value=threshold_value,
            current_value=current_value,
            suggested_changes={
                "improvement_type": improvement_type.value,
                "current_value": current_value,
                "target_value": threshold_value,
            },
        )

        self._candidates[candidate.candidate_id] = candidate
        return candidate

    def analyze_candidate(self, candidate_id: str) -> Optional[SkillImprovementCandidate]:
        """Analyze improvement candidate.

        Args:
            candidate_id: Candidate ID

        Returns:
            Candidate with analysis
        """
        candidate = self._candidates.get(candidate_id)
        if not candidate:
            return None

        candidate.analyze()
        return candidate

    def propose_candidate(
        self,
        candidate_id: str,
    ) -> Optional[SkillImprovementCandidate]:
        """Propose candidate for approval.

        Args:
            candidate_id: Candidate ID

        Returns:
            Proposed candidate or None
        """
        candidate = self._candidates.get(candidate_id)
        if not candidate:
            return None

        candidate.propose()
        return candidate

    def approve_candidate(
        self,
        candidate_id: str,
        approved_by: str,
    ) -> Optional[SkillImprovementCandidate]:
        """Approve improvement candidate.

        Args:
            candidate_id: Candidate ID
            approved_by: User who approved

        Returns:
            Approved candidate or None
        """
        candidate = self._candidates.get(candidate_id)
        if not candidate:
            return None

        candidate.approve(approved_by)
        return candidate

    def implement_improvement(
        self,
        candidate_id: str,
        implemented_by: str,
        new_version: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Implement approved improvement.

        Args:
            candidate_id: Candidate ID
            implemented_by: User who implemented
            new_version: New version (auto-generated if not provided)

        Returns:
            Dict with new skill info or None
        """
        candidate = self._candidates.get(candidate_id)
        if not candidate:
            return None

        if candidate.status != CandidateStatus.APPROVED:
            return None

        # Get base skill
        base_skill = self.registry.get_active_skill(candidate.skill_id)
        if base_skill is None:
            return None

        # Generate new version if not provided
        if not new_version:
            # Increment patch version
            parts = base_skill.version.split(".")
            new_version = f"{parts[0]}.{parts[1]}.{int(parts[2]) + 1}"

        # Create new skill version
        new_skill = self.registry.register_new_version(
            skill_id=candidate.skill_id,
            new_version=new_version,
            changes=f"Improvement: {candidate.improvement_type.value}",
            approved_by=implemented_by,
        )

        if new_skill:
            candidate.implement(implemented_by, new_version)
            return {
                "candidate_id": candidate_id,
                "new_skill_id": new_skill.skill_id,
                "new_skill_version": new_skill.version,
            }

        return None

    def reject_candidate(
        self,
        candidate_id: str,
        rejected_by: str,
        reason: Optional[str] = None,
    ) -> Optional[SkillImprovementCandidate]:
        """Reject improvement candidate.

        Args:
            candidate_id: Candidate ID
            rejected_by: User who rejected
            reason: Reason for rejection

        Returns:
            Rejected candidate or None
        """
        candidate = self._candidates.get(candidate_id)
        if not candidate:
            return None

        candidate.reject(rejected_by, reason)
        return candidate

    def get_candidates_by_skill(
        self,
        skill_id: str,
    ) -> List[SkillImprovementCandidate]:
        """Get all candidates for a skill.

        Args:
            skill_id: Skill ID

        Returns:
            List of candidates
        """
        return [
            c for c in self._candidates.values()
            if c.skill_id == skill_id
        ]

    def get_candidates_by_status(
        self,
        status: CandidateStatus,
    ) -> List[SkillImprovementCandidate]:
        """Get candidates by status.

        Args:
            status: Candidate status

        Returns:
            List of candidates
        """
        return [
            c for c in self._candidates.values()
            if c.status == status
        ]

    def run_full_pipeline(
        self,
    ) -> Dict[str, Any]:
        """Run full evolution pipeline.

        Returns:
            Pipeline results
        """
        # Analyze all skills
        candidates = self.analyze_all_skills()

        # Propose all candidates
        for candidate in candidates:
            self.propose_candidate(candidate.candidate_id)

        return {
            "total_analyzed": len(candidates),
            "candidates_created": len(candidates),
            "candidate_ids": [c.candidate_id for c in candidates],
        }


# Export for convenience
__all__ = ["SkillEvolutionPipeline"]
