"""Tests for Skill Evolution models and pipeline."""

import pytest

from po_agent.evolution.models import (
    ImprovementType,
    CandidateStatus,
    SkillImprovementCandidate,
    EvolutionThresholds,
    SkillEvolutionConfig,
)


class TestImprovementType:
    """ImprovementType enum tests."""

    def test_all_improvement_types(self):
        """Test all improvement types."""
        assert ImprovementType.LOW_ACCURACY.value == "low_accuracy"
        assert ImprovementType.HIGH_CLARIFICATION_RATE.value == "high_clarification_rate"
        assert ImprovementType.LOW_RATING.value == "low_rating"
        assert ImprovementType.HIGH_ERROR_RATE.value == "high_error_rate"
        assert ImprovementType.HIGH_LATENCY.value == "high_latency"
        assert ImprovementType.HIGH_CONFIDENCE_VARIANCE.value == "high_confidence_variance"


class TestCandidateStatus:
    """CandidateStatus enum tests."""

    def test_all_statuses(self):
        """Test all candidate statuses."""
        assert CandidateStatus.IDENTIFIED.value == "identified"
        assert CandidateStatus.ANALYZED.value == "analyzed"
        assert CandidateStatus.PROPOSED.value == "proposed"
        assert CandidateStatus.APPROVED.value == "approved"
        assert CandidateStatus.IMPLEMENTED.value == "implemented"
        assert CandidateStatus.REJECTED.value == "rejected"


class TestSkillImprovementCandidate:
    """SkillImprovementCandidate model tests."""

    def test_create_candidate(self):
        """Test creating a candidate."""
        candidate = SkillImprovementCandidate(
            candidate_id="improve-test-1",
            skill_id="task_search",
            skill_version="1.0.0",
            improvement_type=ImprovementType.LOW_ACCURACY,
            threshold_value=0.7,
            current_value=0.5,
        )

        assert candidate.candidate_id == "improve-test-1"
        assert candidate.skill_id == "task_search"
        assert candidate.improvement_type == ImprovementType.LOW_ACCURACY
        assert candidate.status == CandidateStatus.IDENTIFIED

    def test_analyze_candidate(self):
        """Test analyzing a candidate."""
        candidate = SkillImprovementCandidate(
            candidate_id="improve-test-2",
            skill_id="task_search",
            skill_version="1.0.0",
            improvement_type=ImprovementType.LOW_ACCURACY,
            threshold_value=0.7,
            current_value=0.5,
        )

        candidate.analyze(analyzed_by="admin")

        assert candidate.status == CandidateStatus.ANALYZED
        assert candidate.analyzed_by == "admin"
        assert candidate.analyzed_at is not None

    def test_propose_candidate(self):
        """Test proposing a candidate."""
        candidate = SkillImprovementCandidate(
            candidate_id="improve-test-3",
            skill_id="task_search",
            skill_version="1.0.0",
            improvement_type=ImprovementType.LOW_ACCURACY,
            threshold_value=0.7,
            current_value=0.5,
        )

        candidate.propose()

        assert candidate.status == CandidateStatus.PROPOSED

    def test_approve_candidate(self):
        """Test approving a candidate."""
        candidate = SkillImprovementCandidate(
            candidate_id="improve-test-4",
            skill_id="task_search",
            skill_version="1.0.0",
            improvement_type=ImprovementType.LOW_ACCURACY,
            threshold_value=0.7,
            current_value=0.5,
        )

        candidate.approve(approved_by="admin")

        assert candidate.status == CandidateStatus.APPROVED
        assert candidate.approved_by == "admin"
        assert candidate.approved_at is not None

    def test_implement_improvement(self):
        """Test implementing improvement."""
        candidate = SkillImprovementCandidate(
            candidate_id="improve-test-5",
            skill_id="task_search",
            skill_version="1.0.0",
            improvement_type=ImprovementType.LOW_ACCURACY,
            threshold_value=0.7,
            current_value=0.5,
        )

        candidate.implement(implemented_by="dev", new_version="1.1.0")

        assert candidate.status == CandidateStatus.IMPLEMENTED
        assert candidate.implemented_by == "dev"
        assert candidate.implemented_at is not None
        assert candidate.skill_version == "1.1.0"

    def test_reject_candidate(self):
        """Test rejecting a candidate."""
        candidate = SkillImprovementCandidate(
            candidate_id="improve-test-6",
            skill_id="task_search",
            skill_version="1.0.0",
            improvement_type=ImprovementType.LOW_ACCURACY,
            threshold_value=0.7,
            current_value=0.5,
        )

        candidate.reject(rejected_by="pm", reason="Not needed")

        assert candidate.status == CandidateStatus.REJECTED
        assert candidate.rejected_by == "pm"
        assert candidate.rejected_at is not None
        assert "rejection_reason" in candidate.suggested_changes


class TestEvolutionThresholds:
    """EvolutionThresholds tests."""

    def test_default_thresholds(self):
        """Test default threshold values."""
        thresholds = EvolutionThresholds()

        assert thresholds.accuracy_threshold == 0.7
        assert thresholds.clarification_rate_threshold == 0.3
        assert thresholds.rating_threshold == 3.0
        assert thresholds.error_rate_threshold == 0.15
        assert thresholds.latency_threshold_ms == 500.0

    def test_custom_thresholds(self):
        """Test custom threshold values."""
        thresholds = EvolutionThresholds(
            accuracy_threshold=0.8,
            error_rate_threshold=0.1,
        )

        assert thresholds.accuracy_threshold == 0.8
        assert thresholds.error_rate_threshold == 0.1


class TestSkillEvolutionConfig:
    """SkillEvolutionConfig tests."""

    def test_default_config(self):
        """Test default configuration."""
        config = SkillEvolutionConfig()

        assert config.thresholds.accuracy_threshold == 0.7
        assert config.min_samples_for_analysis == 10
        assert config.max_candidates_per_skill == 5
        assert config.human_approval_required is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = SkillEvolutionConfig(
            min_samples_for_analysis=20,
            human_approval_required=False,
        )

        assert config.min_samples_for_analysis == 20
        assert config.human_approval_required is False


class TestFeedbackAnalyzer:
    """FeedbackAnalyzer tests."""

    def test_analyze_positive_feedback(self):
        """Test analyzing positive feedback."""
        from po_agent.evolution.feedback_analyzer import FeedbackAnalyzer

        analyzer = FeedbackAnalyzer()

        result = analyzer.analyze_text("Отлично, очень помогло!")

        assert result["is_negative"] is False
        assert result["positive_count"] > 0

    def test_analyze_negative_feedback(self):
        """Test analyzing negative feedback."""
        from po_agent.evolution.feedback_analyzer import FeedbackAnalyzer

        analyzer = FeedbackAnalyzer()

        result = analyzer.analyze_text("Неправильно, ошибка!")

        assert result["is_negative"] is True
        assert result["negative_count"] > 0

    def test_identify_improvement_intent(self):
        """Test identifying improvement intent."""
        from po_agent.evolution.feedback_analyzer import FeedbackAnalyzer

        analyzer = FeedbackAnalyzer()

        result = analyzer.analyze_text("Не понял, объясни проще")

        assert "clarification" in result["improvement_intents"]
