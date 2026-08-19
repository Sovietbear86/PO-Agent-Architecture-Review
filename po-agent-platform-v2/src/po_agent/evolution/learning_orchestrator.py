"""Controlled orchestration for Learning Loop 012.

This module connects candidate discovery with baseline/candidate evaluation evidence.
It intentionally has no method that mutates or promotes a production skill.
"""
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

from po_agent.evolution.learning_loop import EvaluationSnapshot, LearningLoop, PromotionDecision
from po_agent.evolution.models import SkillImprovementCandidate
from po_agent.evolution.pipeline import SkillEvolutionPipeline


@dataclass(frozen=True)
class CandidateEvaluationArtifact:
    candidate_id: str
    skill_id: str
    skill_version: str
    baseline: EvaluationSnapshot
    candidate: EvaluationSnapshot
    decision: PromotionDecision
    evidence: Dict[str, Any]


class ControlledLearningOrchestrator:
    """Build evidence for a candidate and stop at the human approval boundary."""

    def __init__(self, pipeline: SkillEvolutionPipeline, learning_loop: Optional[LearningLoop] = None):
        self.pipeline = pipeline
        self.learning_loop = learning_loop or LearningLoop()
        self._artifacts: Dict[str, CandidateEvaluationArtifact] = {}

    def register_candidate(self, candidate: SkillImprovementCandidate) -> SkillImprovementCandidate:
        # Candidate storage remains owned by the pre-existing pipeline.
        self.pipeline._candidates[candidate.candidate_id] = candidate
        return candidate

    def evaluate_candidate(
        self,
        candidate_id: str,
        baseline: EvaluationSnapshot,
        candidate: EvaluationSnapshot,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> CandidateEvaluationArtifact:
        improvement = self.pipeline._candidates.get(candidate_id)
        if improvement is None:
            raise KeyError(f"unknown candidate: {candidate_id}")

        decision = self.learning_loop.compare(baseline, candidate)
        artifact = CandidateEvaluationArtifact(
            candidate_id=candidate_id,
            skill_id=improvement.skill_id,
            skill_version=improvement.skill_version,
            baseline=baseline,
            candidate=candidate,
            decision=decision,
            evidence=dict(evidence or {}),
        )
        self._artifacts[candidate_id] = artifact
        return artifact

    def get_artifact(self, candidate_id: str) -> Optional[CandidateEvaluationArtifact]:
        return self._artifacts.get(candidate_id)

    def request_human_approval(self, candidate_id: str) -> CandidateEvaluationArtifact:
        """Return evidence for review; this method never approves or promotes."""
        artifact = self._artifacts.get(candidate_id)
        if artifact is None:
            raise KeyError(f"candidate has no evaluation artifact: {candidate_id}")
        return artifact

    def can_promote(self, candidate_id: str, human_approved: bool = False) -> bool:
        artifact = self._artifacts.get(candidate_id)
        if artifact is None:
            return False
        return self.learning_loop.can_promote(artifact.decision, human_approved=human_approved)


__all__ = ["CandidateEvaluationArtifact", "ControlledLearningOrchestrator"]
