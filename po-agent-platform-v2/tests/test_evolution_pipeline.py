"""Tests for Skill Evolution pipeline."""

import pytest

from po_agent.skill.registry import SkillRegistry
from po_agent.skill.models import SkillDefinition, SkillStatus
from po_agent.evaluation.metrics import SkillEvaluation
from po_agent.evolution.pipeline import SkillEvolutionPipeline
from po_agent.evolution.models import (
    ImprovementType,
    CandidateStatus,
)


class TestSkillEvolutionPipeline:
    """SkillEvolutionPipeline tests."""

    def test_init(self):
        """Test pipeline initialization."""
        registry = SkillRegistry()
        pipeline = SkillEvolutionPipeline(registry)

        assert pipeline.registry == registry
        assert pipeline.config is not None

    def test_analyze_all_skills_no_candidates(self):
        """Test analyzing skills with no candidates."""
        registry = SkillRegistry()
        evaluation = SkillEvaluation()

        pipeline = SkillEvolutionPipeline(registry, evaluation)

        candidates = pipeline.analyze_all_skills()

        assert candidates == []

    def test_analyze_all_skills_low_accuracy(self):
        """Test analyzing skills with low accuracy."""
        registry = SkillRegistry()
        evaluation = SkillEvaluation()

        # Record requests with low accuracy
        for _ in range(10):
            evaluation.record_request(
                skill_id="test_skill",
                skill_version="1.0.0",
                latency_ms=100,
                confidence=0.9,
                success=False,  # All failed = 0% accuracy
            )

        pipeline = SkillEvolutionPipeline(registry, evaluation)

        candidates = pipeline.analyze_all_skills()

        assert len(candidates) == 1
        assert candidates[0].improvement_type == ImprovementType.LOW_ACCURACY

    def test_analyze_all_skills_high_clarification(self):
        """Test analyzing skills with high clarification rate."""
        registry = SkillRegistry()
        evaluation = SkillEvaluation()

        # 70% success (7/10), 60% clarification (6/10)
        for i in range(10):
            evaluation.record_request(
                skill_id="test_skill",
                skill_version="1.0.0",
                latency_ms=100,
                confidence=0.9,
                success=i < 7,  # 7 success = 70% accuracy
                clarification_required=i >= 4,  # 6 clarification = 60%
            )

        pipeline = SkillEvolutionPipeline(registry, evaluation)

        candidates = pipeline.analyze_all_skills()

        # 70% accuracy is above threshold (0.7), so no accuracy candidate
        # 60% clarification is above threshold (0.3), so clarification candidate
        assert len(candidates) == 1
        assert candidates[0].improvement_type == ImprovementType.HIGH_CLARIFICATION_RATE

    def test_propose_candidate(self):
        """Test proposing a candidate."""
        registry = SkillRegistry()
        evaluation = SkillEvaluation()

        evaluation.record_request(
            skill_id="test_skill",
            skill_version="1.0.0",
            latency_ms=100,
            confidence=0.9,
            success=False,
        )

        pipeline = SkillEvolutionPipeline(registry, evaluation)
        candidates = pipeline.analyze_all_skills()

        candidate = pipeline.propose_candidate(candidates[0].candidate_id)

        assert candidate.status == CandidateStatus.PROPOSED

    def test_approve_candidate(self):
        """Test approving a candidate."""
        registry = SkillRegistry()
        evaluation = SkillEvaluation()

        evaluation.record_request(
            skill_id="test_skill",
            skill_version="1.0.0",
            latency_ms=100,
            confidence=0.9,
            success=False,
        )

        pipeline = SkillEvolutionPipeline(registry, evaluation)
        candidates = pipeline.analyze_all_skills()
        pipeline.propose_candidate(candidates[0].candidate_id)

        candidate = pipeline.approve_candidate(candidates[0].candidate_id, "admin")

        assert candidate.status == CandidateStatus.APPROVED
        assert candidate.approved_by == "admin"

    def test_run_full_pipeline(self):
        """Test running full pipeline."""
        registry = SkillRegistry()
        evaluation = SkillEvaluation()

        evaluation.record_request(
            skill_id="test_skill",
            skill_version="1.0.0",
            latency_ms=100,
            confidence=0.9,
            success=False,
        )

        pipeline = SkillEvolutionPipeline(registry, evaluation)
        result = pipeline.run_full_pipeline()

        assert result["total_analyzed"] == 1
        assert result["candidates_created"] == 1
        assert len(result["candidate_ids"]) == 1


class TestSkillEvolutionIntegration:
    """Integration tests for skill evolution."""

    def test_candidate_creation_from_metrics(self):
        """Test creating candidate from metrics."""
        from po_agent.evolution.models import SkillImprovementCandidate

        candidate = SkillImprovementCandidate(
            candidate_id="improve-1",
            skill_id="task_search",
            skill_version="1.0.0",
            improvement_type=ImprovementType.LOW_ACCURACY,
            threshold_value=0.7,
            current_value=0.5,
        )

        assert candidate.current_value < candidate.threshold_value
        assert candidate.improvement_type == ImprovementType.LOW_ACCURACY
