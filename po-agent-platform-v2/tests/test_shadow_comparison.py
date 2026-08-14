"""Tests for Shadow Mode Comparison Engine with real SWTR data."""

import pytest

from po_agent.shadow.comparison import (
    ComparisonEngine,
    ComparisonRecord,
    ComparisonResult,
)


@pytest.fixture
def engine():
    """Create comparison engine."""
    e = ComparisonEngine(db_path=":memory:")
    yield e
    e.close()


class TestComparisonEngineBasic:
    """Tests for basic comparison engine operations."""

    def test_compare_pass(self, engine: ComparisonEngine):
        """Test comparing identical outputs."""
        record = engine.compare(
            config_id="config-1",
            prompt_name="task_summarizer",
            prod_version=1,
            shadow_version=2,
            prod_output="This is a task summary",
            shadow_output="This is a task summary",
            threshold=0.8,
        )

        assert record.similarity_score == 1.0
        assert record.passed_threshold is True
        assert record.result == ComparisonResult.PASSED.value

    def test_compare_fail(self, engine: ComparisonEngine):
        """Test comparing different outputs."""
        record = engine.compare(
            config_id="config-1",
            prompt_name="task_summarizer",
            prod_version=1,
            shadow_version=2,
            prod_output="Short summary",
            shadow_output="This is a completely different summary",
            threshold=0.8,
        )

        assert record.similarity_score < 0.8
        assert record.passed_threshold is False
        assert record.result == ComparisonResult.FAILED.value

    def test_get_statistics(self, engine: ComparisonEngine):
        """Test getting statistics."""
        # Add some comparisons
        engine.compare(
            config_id="config-1",
            prompt_name="task_summarizer",
            prod_version=1,
            shadow_version=2,
            prod_output="Same output",
            shadow_output="Same output",
            threshold=0.8,
        )

        engine.compare(
            config_id="config-1",
            prompt_name="task_summarizer",
            prod_version=1,
            shadow_version=2,
            prod_output="Different",
            shadow_output="Output",
            threshold=0.8,
        )

        stats = engine.get_statistics("task_summarizer")

        assert stats["total"] == 2
        assert stats["passed"] == 1
        assert stats["failed"] == 1
        assert stats["passed_rate"] == 0.5


class TestComparisonEngineSWTR:
    """Tests for Comparison Engine with real SWTR data."""

    def test_compare_with_real_team_data(self, engine: ComparisonEngine):
        """Test comparison with real team member reference."""
        record = engine.compare(
            config_id="config-kalachanov-1",
            prompt_name="sprint_explainer",
            prod_version=2,
            shadow_version=3,
            prod_output="Sprint health metrics: velocity, predictability, blockers",
            shadow_output="Sprint health metrics: velocity, predictability, blockers, risk",
            threshold=0.7,
        )

        assert record.config_id == "config-kalachanov-1"
        assert record.similarity_score >= 0.7  # High similarity for similar text

    def test_multiple_comparisons_for_same_prompt(self, engine: ComparisonEngine):
        """Test multiple comparisons for the same prompt."""
        prompts = [
            ("task_summarizer", "Summary A", "Summary A"),
            ("sprint_explainer", "Metrics: velocity, predictability", "Metrics: velocity, predictability, blockers"),
            ("task_quality_analyzer", "Quality score: high", "Quality score: medium"),
        ]

        for i, (prompt, prod, shadow) in enumerate(prompts):
            engine.compare(
                config_id=f"config-{i}",
                prompt_name=prompt,
                prod_version=1,
                shadow_version=2,
                prod_output=prod,
                shadow_output=shadow,
                threshold=0.6,
            )

        # Get latest for each prompt
        for prompt in ["task_summarizer", "sprint_explainer", "task_quality_analyzer"]:
            latest = engine.get_latest(prompt, limit=1)
            assert len(latest) == 1

    def test_comparison_statistics_with_real_team(self, engine: ComparisonEngine):
        """Test comparison statistics with real team members."""
        # Add comparisons
        engine.compare(
            config_id="config-1",
            prompt_name="velocity_calculator",
            prod_version=1,
            shadow_version=2,
            prod_output="Velocity: 45 points",
            shadow_output="Velocity: 45 points",
            threshold=0.8,
        )

        engine.compare(
            config_id="config-2",
            prompt_name="velocity_calculator",
            prod_version=1,
            shadow_version=2,
            prod_output="Velocity: 40 points",
            shadow_output="Velocity: 35 points",
            threshold=0.8,
        )

        stats = engine.get_statistics("velocity_calculator")

        assert stats["total"] == 2
        assert stats["passed_rate"] == 0.5


class TestComparisonEngineRealTeamIntegration:
    """Integration tests with real SWTR team data."""

    def test_full_comparison_lifecycle(self, engine: ComparisonEngine):
        """Test full comparison lifecycle with real team members."""
        # 1. Compare with high similarity (pass)
        record1 = engine.compare(
            config_id="config-kalachanov-1",
            prompt_name="sprint_health_explainer",
            prod_version=2,
            shadow_version=3,
            prod_output="Sprint health: velocity 45, predictability 90%, blockers 2",
            shadow_output="Sprint health: velocity 45, predictability 90%, blockers 2",
            threshold=0.8,
        )

        assert record1.result == ComparisonResult.PASSED.value

        # 2. Compare with low similarity (fail)
        record2 = engine.compare(
            config_id="config-kalachanov-1",
            prompt_name="sprint_health_explainer",
            prod_version=2,
            shadow_version=3,
            prod_output="Health: good",
            shadow_output="Detailed health metrics: velocity 45, predictability 90%",
            threshold=0.8,
        )

        assert record2.result == ComparisonResult.FAILED.value

        # 3. Get statistics
        stats = engine.get_statistics("sprint_health_explainer")
        assert stats["total"] == 2
        assert stats["passed"] == 1
        assert stats["failed"] == 1

    def test_comparison_threshold_with_real_team_members(self, engine: ComparisonEngine):
        """Test comparison with different thresholds and real team members."""
        test_cases = [
            (0.9, "High similarity text", "High similarity text", True),
            (0.95, "High similarity text", "High similarity text", True),
            (0.5, "Different content", "Different content", True),
        ]

        for threshold, prod, shadow, expected_passed in test_cases:
            record = engine.compare(
                config_id="config-garanin-1",
                prompt_name="test_prompt",
                prod_version=1,
                shadow_version=2,
                prod_output=prod,
                shadow_output=shadow,
                threshold=threshold,
            )

            assert record.passed_threshold == expected_passed
            assert (record.result == ComparisonResult.PASSED.value) == expected_passed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
