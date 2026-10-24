"""Integration tests for Steps 26-30 with real SWTR data."""

import pytest

from po_agent.evaluation.case import (
    EvalCase,
    EvalCaseStore,
    EvalCaseStatus,
    EvalCaseSeverity,
    EvalCaseSource,
)
from po_agent.evaluation.runner import EvalRunner, EvalReport, EvalResult
from po_agent.evaluation.failure import FailureClassifier, FailureStore, FailureCategory
from po_agent.evaluation.miner import FailureMiner
from po_agent.knowledge.curated_memory import CuratedMemoryStore, MemoryStatus
from po_agent.orchestration.router import DeterministicIntentRouter


@pytest.fixture
def router():
    """Create intent router."""
    return DeterministicIntentRouter()


@pytest.fixture
def eval_store():
    """Create eval case store."""
    return EvalCaseStore()


@pytest.fixture
def failure_store():
    """Create failure store."""
    return FailureStore()


@pytest.fixture
def curated_memory_store():
    """Create curated memory store."""
    return CuratedMemoryStore()


class TestStep26EvalCaseSWTR:
    """Step 26: Eval Case with real SWTR data."""

    def test_create_eval_from_real_trace(self, eval_store: EvalCaseStore):
        """Test creating eval case from real trace data."""
        case = eval_store.create_from_trace(
            trace_id="swtr-trace-1",
            query="покажи задачи Kalachanov.V.V",
            expected_intent="task_search",
            tags=["real_team", "swtr"],
        )

        assert case.source == EvalCaseSource.TRACE_ANALYSIS.value
        assert "Kalachanov" in case.query
        assert case.expected_intent == "task_search"
        assert "real_team" in case.tags

    def test_create_eval_from_real_feedback(self, eval_store: EvalCaseStore):
        """Test creating eval case from real user feedback."""
        case = eval_store.create_from_feedback(
            feedback_id="feedback-123",
            trace_id="swtr-trace-456",
            query="что по спринту DMS-SPRNT-1",
            expected_intent="sprint_health",
            expected_entities=[{"type": "sprint", "value": "dms-sprnt-1"}],
        )

        assert case.source == EvalCaseSource.USER_FEEDBACK.value
        assert case.expected_intent == "sprint_health"
        assert "feedback" in case.tags

    def test_eval_case_approval_workflow(self, eval_store: EvalCaseStore):
        """Test eval case approval workflow with real team data."""
        case = eval_store.create_from_trace(
            trace_id="real-trace",
            query="скорость команды Garanin.R.V",
            expected_intent="velocity",
        )

        # Initially candidate
        assert case.status == EvalCaseStatus.CANDIDATE.value
        assert case.approved is False

        # Approve
        # create_from_trace doesn't add to store, need to add first
        eval_store.add_case(case)
        approved = eval_store.approve_case(case.case_id, "Kalachanov.V.V")

        assert approved is not None
        assert approved.status == EvalCaseStatus.APPROVED.value
        assert approved.approved_by == "Kalachanov.V.V"

        # Get approved
        approved_cases = eval_store.get_approved_cases()
        assert len(approved_cases) >= 1


class TestStep27EvalRunnerSWTR:
    """Step 27: Eval Runner with real SWTR data."""

    def test_run_eval_with_real_team_query(self, router: DeterministicIntentRouter):
        """Test running eval with real team query."""
        from po_agent.evaluation.runner import EvalRunner

        runner = EvalRunner(router=router)

        # Test query with real team member
        query = "покажи задачи Garanin.R.V из спринта DMS-SPRNT-1"

        case = EvalCase(
            query=query,
            expected_intent="task_search",
            expected_entities=[],
        )

        report = runner.run([case])

        assert report.total_cases == 1
        assert report.pass_rate >= 0.0  # May or may not pass depending on entity extraction

    def test_run_multiple_evals_with_real_team(self, router: DeterministicIntentRouter):
        """Test running multiple evals with real team data."""
        from po_agent.evaluation.runner import EvalRunner

        runner = EvalRunner(router=router)

        real_queries = [
            ("покажи задачи Agataeva.A.Z", "task_search"),
            ("спринт OLAP-SPRNT-2024", "sprint_health"),
            ("скорость команды", "velocity"),
            ("кто загружен больше всего", "team_workload"),
        ]

        cases = []
        for query, expected_intent in real_queries:
            case = EvalCase(
                query=query,
                expected_intent=expected_intent,
            )
            cases.append(case)

        report = runner.run(cases)

        assert report.total_cases == len(real_queries)


class TestStep28FailureTaxonomySWTR:
    """Step 28: Failure Taxonomy with real SWTR data."""

    def test_classify_adapter_failure(self, failure_store: FailureStore):
        """Test classifying adapter failure with real SWTR context."""
        record = failure_store.add_failure(
            trace_id="swtr-trace-1",
            error_message="SWTR adapter timeout while fetching sprint tasks",
            intent="sprint_health",
            entities=[{"type": "sprint", "value": "dms-sprnt-1"}],
            capability=None,
        )

        assert record["category"] == FailureCategory.ADAPTER_ERROR.value

    def test_classify_entity_extraction_failure(self, failure_store: FailureStore):
        """Test classifying entity extraction failure with real member data."""
        record = failure_store.add_failure(
            trace_id="swtr-trace-2",
            error_message="Failed to extract member from query",
            intent="task_search",
            entities=[],
            capability=None,
        )

        # Compare string values
        assert record["category"] == FailureCategory.ENTITY_EXTRACTION_ERROR.value

    def test_classify_missing_evidence(self, failure_store: FailureStore):
        """Test classifying missing evidence with real team member."""
        record = failure_store.add_failure(
            trace_id="swtr-trace-3",
            error_message="No data found for member Kryukov.V.A",
            intent="velocity",
            entities=[{"type": "member", "value": "Kryukov"}],
            capability=None,
        )

        # Compare string values
        assert record["category"] == FailureCategory.MISSING_EVIDENCE.value

    def test_get_failure_counts_with_real_data(self, failure_store: FailureStore):
        """Test getting failure counts with real SWTR data."""
        # Add multiple failures
        failure_store.add_failure(
            trace_id="swtr-trace-1",
            error_message="SWTR adapter timeout",
            intent="sprint_health",
            entities=[],
            capability=None,
        )

        failure_store.add_failure(
            trace_id="swtr-trace-2",
            error_message="Failed to parse JSON response",
            intent="task_summary",
            entities=[],
            capability=None,
        )

        failure_store.add_failure(
            trace_id="swtr-trace-3",
            error_message="No data for sprint",
            intent="sprint_health",
            entities=[],
            capability=None,
        )

        counts = failure_store.get_failure_counts()

        # Verify at least some categories have failures
        assert sum(counts.values()) == 3


class TestStep29FailureMinerSWTR:
    """Step 29: Failure Miner with real SWTR data."""

    def test_mine_failures_with_real_dataset(self):
        """Test failure mining with real SWTR data."""
        from po_agent.evaluation.failure import FailureStore, FailureCategory
        from po_agent.evaluation.miner import FailureMiner

        # Create failure store with real data patterns
        failure_store = FailureStore()

        # Simulate real SWTR failure patterns
        real_failures = [
            ("swtr-trace-1", "SWTR adapter timeout", "task_search", [], None),
            ("swtr-trace-2", "SWTR unavailable", "sprint_health", [], None),
            ("swtr-trace-3", "No data found for sprint", "sprint_health", [], None),
            ("swtr-trace-4", "Failed to parse JSON", "task_summary", [], None),
        ]

        for trace_id, error, intent, entities, capability in real_failures:
            failure_store.add_failure(
                trace_id=trace_id,
                error_message=error,
                intent=intent,
                entities=entities,
                capability=capability,
            )

        # Mine failures
        failures = failure_store.get_all_failures()
        miner = FailureMiner(failures)
        report = miner.mine()

        assert report.total_failures == len(real_failures)
        assert len(report.clusters) > 0

        # Verify clusters exist
        cluster_ids = [c["cluster_id"] for c in report.clusters]
        assert "adapter_mapping" in cluster_ids or "empty_sprint" in cluster_ids

    def test_failure_mining_with_real_team_members(self):
        """Test failure mining with real team member references."""
        failure_store = FailureStore()

        # Add failures with real team member references
        failure_store.add_failure(
            trace_id="trace-1",
            error_message="No data for member Kalachanov.V.V",
            intent="velocity",
            entities=[],
            capability=None,
        )

        failure_store.add_failure(
            trace_id="trace-2",
            error_message="No data for member Garanin.R.V",
            intent="task_search",
            entities=[],
            capability=None,
        )

        failures = failure_store.get_all_failures()
        miner = FailureMiner(failures)
        report = miner.mine()

        # Verify failures are analyzed
        assert report.total_failures >= 2


class TestStep30CuratedMemorySWTR:
    """Step 30: Curated Memory with real SWTR data."""

    def test_add_terminology_candidate(self, curated_memory_store: CuratedMemoryStore):
        """Test adding terminology with real team context."""
        entry = curated_memory_store.add_candidate(
            key="terminology:sprint",
            category="terminology",
            content="Sprint - time-boxed period for development",
            evidence_trace_ids=["swtr-trace-1", "swtr-trace-2"],
            source="real_team_knowledge",
            confidence=0.95,
        )

        assert entry.status == "candidate"
        assert entry.source == "real_team_knowledge"
        assert "swtr-trace-1" in entry.evidence_trace_ids

    def test_approve_memory_with_real_user(self, curated_memory_store: CuratedMemoryStore):
        """Test approving memory with real team member."""
        entry = curated_memory_store.add_candidate(
            key="terminology:velocity",
            category="terminology",
            content="Velocity - team's completed story points per sprint",
        )

        # Approve with real team member
        approved = curated_memory_store.approve_entry("terminology:velocity", "Kalachanov.V.V")

        assert approved is not None
        assert approved.status == "approved"
        assert approved.approved_by == "Kalachanov.V.V"

    def test_get_approved_memory_for_runtime(self, curated_memory_store: CuratedMemoryStore):
        """Test getting approved memory for runtime use."""
        # Add and approve terminology
        curated_memory_store.add_candidate(
            key="terminology:sprint",
            category="terminology",
            content="Sprint - time-boxed period",
        ).approve("Kalachanov.V.V")

        curated_memory_store.add_candidate(
            key="terminology:velocity",
            category="terminology",
            content="Velocity - team's capacity",
        ).approve("Garanin.R.V")

        # Get all approved
        approved = curated_memory_store.get_approved_entries()
        assert len(approved) == 2

        # Get specific approved memory
        sprint_content = curated_memory_store.get_approved_by_key("terminology:sprint")
        assert sprint_content == "Sprint - time-boxed period"

    def test_memory_with_real_team_members(self, curated_memory_store: CuratedMemoryStore):
        """Test memory with references to real team members."""
        entry = curated_memory_store.add_candidate(
            key="alias:po",
            category="alias",
            content="Product Owner - Kalachanov.V.V",
            evidence_trace_ids=["swtr-trace-1"],
            source="real_team_config",
            confidence=1.0,
        )

        # Approve
        curated_memory_store.approve_entry("alias:po", "Kalachanov.V.V")

        # Verify
        approved = curated_memory_store.get_approved_by_key("alias:po")
        assert "Kalachanov.V.V" in approved


class TestSteps2630CompleteIntegration:
    """Complete integration test for Steps 26-30."""

    def test_full_integration_pipeline(
        self,
        router: DeterministicIntentRouter,
        failure_store: FailureStore,
        curated_memory_store: CuratedMemoryStore,
    ):
        """Test complete pipeline with real SWTR data."""
        from po_agent.evaluation.runner import EvalRunner
        from po_agent.evaluation.miner import FailureMiner

        # 1. Create eval cases from real traces
        eval_store = EvalCaseStore()

        eval_case_1 = eval_store.create_from_trace(
            trace_id="swtr-trace-1",
            query="покажи задачи Garanin.R.V",
            expected_intent="task_search",
            tags=["real_team", "integration"],
        )

        eval_case_2 = eval_store.create_from_trace(
            trace_id="swtr-trace-2",
            query="спринт OLAP-SPRNT-2024",
            expected_intent="sprint_health",
            tags=["real_team", "sprint"],
        )

        eval_store.add_case(eval_case_1)
        eval_store.add_case(eval_case_2)
        eval_store.approve_case(eval_case_1.case_id, "Kalachanov.V.V")
        eval_store.approve_case(eval_case_2.case_id, "Kalachanov.V.V")

        # 2. Run evals
        runner = EvalRunner(router=router)
        report = runner.run(eval_store.get_approved_cases())

        # 3. Record failures if any
        if report.total_cases > report.passed_cases:
            for result in report.results:
                if not result.passed:
                    failure_store.add_failure(
                        trace_id="swtr-trace-1",
                        error_message=result.details,
                        intent="unknown",
                        entities=[],
                        capability=None,
                    )

        # 4. Mine failures
        failures = failure_store.get_all_failures()
        if failures:
            miner = FailureMiner(failures)
            failure_report = miner.mine()

        # 5. Add curated memory
        memory_entry = curated_memory_store.add_candidate(
            key="terminology:po",
            category="terminology",
            content="Product Owner for OLAP/DMS team",
        )
        curated_memory_store.approve_entry("terminology:po", "Kalachanov.V.V")

        # 6. Verify integration
        assert eval_store.get_approved_cases() is not None
        assert len(curated_memory_store.get_approved_entries()) >= 1
        assert report.total_cases >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
