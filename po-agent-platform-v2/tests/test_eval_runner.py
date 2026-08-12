"""Tests for Eval Runner."""

import pytest

from po_agent.evaluation.case import EvalCase, EvalCaseStore, EvalCaseStatus
from po_agent.evaluation.runner import EvalRunner, EvalReport, EvalResult


@pytest.fixture
def runner():
    """Create eval runner."""
    from po_agent.orchestration.router import DeterministicIntentRouter
    return EvalRunner(router=DeterministicIntentRouter())


@pytest.fixture
def store():
    """Create eval case store."""
    return EvalCaseStore()


class TestEvalRunnerBasic:
    """Tests for basic eval runner operations."""

    def test_run_single_case(
        self,
        runner: EvalRunner,
        store: EvalCaseStore,
    ):
        """Test running a single eval case."""
        case = store.create_from_trace(
            trace_id="trace-1",
            query="покажи задачи",
            expected_intent="task_search",
        )

        report = runner.run([case])

        assert isinstance(report, EvalReport)
        assert report.total_cases == 1
        assert report.passed_cases == 1
        assert report.pass_rate == 100.0
        assert len(report.results) == 1

    def test_run_multiple_cases(
        self,
        runner: EvalRunner,
        store: EvalCaseStore,
    ):
        """Test running multiple eval cases."""
        cases = [
            store.create_from_trace(
                trace_id=f"trace-{i}",
                query=f"query {i}",
                expected_intent="help",
            )
            for i in range(3)
        ]

        report = runner.run(cases)

        assert report.total_cases == 3
        assert report.passed_cases == 3

    def test_run_with_failures(
        self,
        runner: EvalRunner,
        store: EvalCaseStore,
    ):
        """Test running cases that should fail."""
        # Create case with wrong expected intent
        case = store.create_from_trace(
            trace_id="trace-1",
            query="что умеешь",
            expected_intent="task_search",  # Wrong - should be help
        )

        report = runner.run([case])

        assert report.total_cases == 1
        assert report.passed_cases == 0
        assert report.pass_rate == 0.0

    def test_result_format(
        self,
        runner: EvalRunner,
        store: EvalCaseStore,
    ):
        """Test result format."""
        case = store.create_from_trace(
            trace_id="trace-1",
            query="что умеешь",
            expected_intent="help",
        )

        report = runner.run([case])

        result = report.results[0]
        assert isinstance(result, EvalResult)
        assert result.case_id is not None
        assert result.test_type == "overall"
        assert result.passed is True
        assert result.score == 1.0


class TestEvalRunnerEntities:
    """Tests for entity extraction evaluation."""

    def test_entities_match(
        self,
        runner: EvalRunner,
        store: EvalCaseStore,
    ):
        """Test when entities match."""
        # The pattern matches the full value including the word "спринт"
        case = EvalCase(
            query="спринт dms-sprnt-1",
            expected_intent="sprint_health",
            expected_entities=[{"type": "sprint", "value": "спринт dms-sprnt-1"}],
        )

        report = runner.run([case])

        assert report.passed_cases == 1

    def test_entities_partial_match(
        self,
        runner: EvalRunner,
        store: EvalCaseStore,
    ):
        """Test when only partial entities match."""
        case = EvalCase(
            query="спринт DMS-SPRNT-1",
            expected_intent="sprint_health",
            expected_entities=[
                {"type": "sprint", "value": "DMS-SPRNT-1"},
                {"type": "member", "value": "Kalachanov"},
            ],
        )

        report = runner.run([case])

        # Should fail because not all expected entities found
        assert report.passed_cases == 0


class TestEvalRunnerMultiCapability:
    """Tests for multi-capability eval runner."""

    def test_capability_test(self):
        """Test multi-capability eval."""
        from po_agent.evaluation.runner import MultiCapabilityEvalRunner

        runner = MultiCapabilityEvalRunner()
        result = runner.run_capability(
            capability_name="task_search",
            input_data={"query": "test"},
            expected_output={"type": "task_search"},
        )

        assert result.test_type == "capability"
        assert result.passed is True

    def test_llm_schema_test(self):
        """Test LLM schema validation."""
        from po_agent.evaluation.runner import MultiCapabilityEvalRunner

        runner = MultiCapabilityEvalRunner()
        result = runner.run_llm_schema_test(
            prompt="test prompt",
            expected_schema={"type": "object"},
        )

        assert result.test_type == "llm_schema"
        assert result.passed is True


class TestEvalRunnerIntegration:
    """Integration tests for eval runner."""

    def test_full_eval_pipeline(
        self,
        runner: EvalRunner,
        store: EvalCaseStore,
    ):
        """Test full eval pipeline."""
        # Create various test cases
        cases = [
            store.create_from_trace(
                trace_id="trace-1",
                query="покажи задачи",
                expected_intent="task_search",
            ),
            store.create_from_trace(
                trace_id="trace-2",
                query="спринт DMS-SPRNT-1",
                expected_intent="sprint_health",
            ),
            store.create_from_trace(
                trace_id="trace-3",
                query="что умеешь",
                expected_intent="help",
            ),
        ]

        report = runner.run(cases)

        assert report.total_cases == 3
        assert report.pass_rate == 100.0
        assert report.run_id is not None
        assert report.timestamp is not None
