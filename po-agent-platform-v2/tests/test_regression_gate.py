"""Tests for Regression Gate with real SWTR data."""

import pytest

from po_agent.shadow.gate import (
    RegressionGate,
    RegressionGateRecord,
    GateStatus,
)


@pytest.fixture
def gate():
    """Create regression gate."""
    g = RegressionGate(db_path=":memory:")
    yield g
    g.close()


@pytest.fixture
def comparisons():
    """Sample comparison data."""
    return [
        {"passed_threshold": True},
        {"passed_threshold": True},
        {"passed_threshold": True},
        {"passed_threshold": False},
        {"passed_threshold": True},
    ]


class TestRegressionGateBasic:
    """Tests for basic regression gate operations."""

    def test_check_passed(self, gate: RegressionGate, comparisons):
        """Test gate check with high pass rate."""
        record = gate.check(
            prompt_name="task_summarizer",
            shadow_version=2,
            comparisons=comparisons,
            threshold=0.8,
            reviewed_by="Kalachanov.V.V",
        )

        assert record.pass_rate == 0.8  # 4/5
        assert record.threshold == 0.8
        assert record.gate_passed is True
        assert "Kalachanov" in record.reviewed_by

    def test_check_failed(self, gate: RegressionGate):
        """Test gate check with low pass rate."""
        low_pass_comparisons = [
            {"passed_threshold": True},
            {"passed_threshold": False},
            {"passed_threshold": False},
            {"passed_threshold": False},
        ]

        record = gate.check(
            prompt_name="task_summarizer",
            shadow_version=2,
            comparisons=low_pass_comparisons,
            threshold=0.8,
        )

        assert record.pass_rate == 0.25  # 1/4
        assert record.threshold == 0.8
        assert record.gate_passed is False
        assert "threshold" in record.decision_reason.lower()

    def test_check_no_comparisons(self, gate: RegressionGate):
        """Test gate check with no comparisons."""
        record = gate.check(
            prompt_name="task_summarizer",
            shadow_version=2,
            comparisons=[],
            threshold=0.8,
        )

        assert record.pass_rate == 0.0
        assert record.gate_passed is False
        assert "No comparisons" in record.decision_reason


class TestRegressionGateSWTR:
    """Tests for Regression Gate with real SWTR data."""

    def test_gate_with_real_team_member(self, gate: RegressionGate, comparisons):
        """Test gate with real team member review."""
        record = gate.check(
            prompt_name="sprint_explainer",
            shadow_version=3,
            comparisons=comparisons,
            threshold=0.8,
            reviewed_by="Garanin.R.V",  # Real team member
        )

        assert record.reviewed_by == "Garanin.R.V"

    def test_multiple_gate_checks_for_same_prompt(self, gate: RegressionGate, comparisons):
        """Test multiple gate checks for the same prompt."""
        gate.check(
            prompt_name="task_summarizer",
            shadow_version=2,
            comparisons=comparisons,
            threshold=0.8,
        )

        gate.check(
            prompt_name="task_summarizer",
            shadow_version=3,
            comparisons=comparisons,
            threshold=0.9,
            reviewed_by="Agataeva.A.Z",
        )

        gates = gate.get_by_prompt("task_summarizer")
        assert len(gates) == 2

    def test_gate_statistics_with_real_team(self, gate: RegressionGate):
        """Test gate statistics with real team members."""
        comparisons_high = [
            {"passed_threshold": True},
            {"passed_threshold": True},
            {"passed_threshold": True},
            {"passed_threshold": True},
        ]

        comparisons_low = [
            {"passed_threshold": True},
            {"passed_threshold": False},
        ]

        gate.check(
            prompt_name="velocity_calculator",
            shadow_version=2,
            comparisons=comparisons_high,
            threshold=0.8,
            reviewed_by="Kalachanov.V.V",
        )

        gate.check(
            prompt_name="velocity_calculator",
            shadow_version=3,
            comparisons=comparisons_low,
            threshold=0.8,
            reviewed_by="Dolgovskoy.E.N",
        )

        stats = gate.get_statistics("velocity_calculator")

        assert stats["total"] == 2
        assert stats["passed"] == 1
        assert stats["failed"] == 1
        assert stats["passed_rate"] == 0.5


class TestRegressionGateRealTeamIntegration:
    """Integration tests with real SWTR team data."""

    def test_full_gate_lifecycle(self, gate: RegressionGate):
        """Test full gate lifecycle with real team members."""
        # 1. High pass rate - passes gate
        high_comparisons = [
            {"passed_threshold": True},
            {"passed_threshold": True},
            {"passed_threshold": True},
            {"passed_threshold": True},
        ]

        record1 = gate.check(
            prompt_name="sprint_health_explainer",
            shadow_version=2,
            comparisons=high_comparisons,
            threshold=0.8,
            reviewed_by="Kalachanov.V.V",
        )

        assert record1.gate_passed is True

        # 2. Low pass rate - fails gate
        low_comparisons = [
            {"passed_threshold": True},
            {"passed_threshold": False},
            {"passed_threshold": False},
        ]

        record2 = gate.check(
            prompt_name="sprint_health_explainer",
            shadow_version=3,
            comparisons=low_comparisons,
            threshold=0.8,
            reviewed_by="Garanin.R.V",
        )

        assert record2.gate_passed is False

        # 3. Get latest for prompt
        latest = gate.get_latest("sprint_health_explainer", limit=5)
        assert len(latest) == 2
        assert latest[0].shadow_version == 3  # Latest first

    def test_gate_statistics_with_real_team_members(self, gate: RegressionGate):
        """Test gate statistics with multiple team members."""
        team_comparisons = [
            {"passed_threshold": True},
            {"passed_threshold": True},
            {"passed_threshold": True},
            {"passed_threshold": True},
            {"passed_threshold": True},
        ]

        # All team members review
        gate.check(
            prompt_name="task_quality_analyzer",
            shadow_version=2,
            comparisons=team_comparisons,
            threshold=0.8,
            reviewed_by="Kalachanov.V.V",
        )

        gate.check(
            prompt_name="task_quality_analyzer",
            shadow_version=3,
            comparisons=team_comparisons,
            threshold=0.8,
            reviewed_by="Garanin.R.V",
        )

        gate.check(
            prompt_name="task_quality_analyzer",
            shadow_version=4,
            comparisons=team_comparisons,
            threshold=0.8,
            reviewed_by="Agataeva.A.Z",
        )

        # All should pass
        passed = gate.get_passed()
        assert len(passed) == 3

        stats = gate.get_statistics("task_quality_analyzer")
        assert stats["passed_rate"] == 1.0

    def test_gate_with_threshold_varying(self, gate: RegressionGate):
        """Test gate with varying thresholds."""
        comparisons = [
            {"passed_threshold": True},
            {"passed_threshold": True},
            {"passed_threshold": False},
        ]

        # Threshold 0.5 - passes
        record1 = gate.check(
            prompt_name="test_prompt",
            shadow_version=1,
            comparisons=comparisons,
            threshold=0.5,
        )
        assert record1.gate_passed is True  # 2/3 = 0.67 > 0.5

        # Threshold 0.8 - fails
        record2 = gate.check(
            prompt_name="test_prompt",
            shadow_version=2,
            comparisons=comparisons,
            threshold=0.8,
        )
        assert record2.gate_passed is False  # 0.67 < 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
