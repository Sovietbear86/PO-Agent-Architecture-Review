"""Tests for Improvement Candidate Model with real SWTR data."""

import pytest

from po_agent.improvement.candidate import (
    ImprovementCandidate,
    ImprovementCandidateStore,
    CandidateStatus,
    CandidateType,
)


@pytest.fixture
def store():
    """Create improvement candidate store."""
    s = ImprovementCandidateStore(db_path=':memory:')
    yield s
    s.close()


class TestImprovementCandidateSWTR:
    """Tests for Improvement Candidate with real SWTR data."""

    def test_create_prompt_change_candidate(self, store: ImprovementCandidateStore):
        """Test creating prompt change candidate with real team reference."""
        candidate = store.create_prompt_change_candidate(
            prompt_name="task_summarizer",
            reason="LLM hallucinations in task summaries",
            linked_failures=["swtr-trace-1", "swtr-trace-2"],
            proposed_diff="Add stricter prompt for factual extraction",
            created_by="Kalachanov.V.V",
        )

        assert candidate.candidate_type == CandidateType.PROMPT_CHANGE.value
        assert "Kalachanov" in candidate.created_by
        assert "swtr-trace" in candidate.linked_failures[0]

    def test_create_router_rule_candidate(self, store: ImprovementCandidateStore):
        """Test creating router rule candidate."""
        candidate = store.create_router_rule_candidate(
            intent="competency_match",
            reason="Missing intent for competency queries",
            linked_failures=["swtr-trace-3"],
            proposed_rule={
                "pattern": r"кто подходит|кто умеет",
                "intent": "competency_match",
            },
            created_by="Garanin.R.V",
        )

        assert candidate.candidate_type == CandidateType.ROUTER_RULE.value
        assert candidate.expected_benefit == "Add routing rule for competency_match"

    def test_create_knowledge_entry_candidate(self, store: ImprovementCandidateStore):
        """Test creating knowledge entry candidate with real terminology."""
        candidate = store.create_knowledge_entry_candidate(
            key="terminology:sprint",
            category="terminology",
            content="Sprint - time-boxed period for development",
            reason="Repeated confusion about sprint definition",
            linked_failures=["swtr-trace-4", "swtr-trace-5"],
            created_by="Kalachanov.V.V",
        )

        assert candidate.candidate_type == CandidateType.KNOWLEDGE_ENTRY.value
        assert candidate.proposed_content["key"] == "terminology:sprint"
        assert "Kalachanov" in candidate.created_by

    def test_create_golden_test_candidate(self, store: ImprovementCandidateStore):
        """Test creating golden test candidate."""
        candidate = store.create_golden_test_candidate(
            test_name="test_intent_router_swtr",
            reason="Missing test for intent router with SWTR data",
            linked_failures=["swtr-trace-6"],
            test_code="def test_intent_router_swtr(): pass",
            created_by="Agataeva.A.Z",
        )

        assert candidate.candidate_type == CandidateType.GOLDEN_TEST.value
        assert "Agataeva" in candidate.created_by

    def test_create_capability_change_candidate(self, store: ImprovementCandidateStore):
        """Test creating capability change candidate."""
        candidate = store.create_capability_change_candidate(
            capability_name="task_summary",
            reason="Add LLM fallback for empty task descriptions",
            linked_failures=["swtr-trace-7"],
            proposed_changes={
                "fallback_enabled": True,
                "default_summary": "Summary not available",
            },
            created_by="Dolgovskoy.E.N",
        )

        assert candidate.candidate_type == CandidateType.CAPABILITY_CHANGE.value
        assert candidate.proposed_content["fallback_enabled"] is True

    def test_create_config_change_candidate(self, store: ImprovementCandidateStore):
        """Test creating config change candidate."""
        candidate = store.create_config_change_candidate(
            config_name="team_members",
            reason="Update team member list from SWTR",
            linked_failures=["swtr-trace-8"],
            proposed_changes={
                "members_file": "task-api/config/team_members.yaml",
                "auto_sync": True,
            },
            created_by="Kryukov.V.A",
        )

        assert candidate.candidate_type == CandidateType.CONFIG_CHANGE.value
        assert candidate.proposed_content["auto_sync"] is True


class TestImprovementCandidateStoreSWTR:
    """Tests for ImprovementCandidateStore with real SWTR data."""

    def test_approval_workflow(self, store: ImprovementCandidateStore):
        """Test approval workflow with real team member."""
        candidate = store.add_candidate(
            candidate_type=CandidateType.PROMPT_CHANGE.value,
            reason="Test candidate",
            created_by="Kalachanov.V.V",
        )

        assert candidate.status == CandidateStatus.CANDIDATE.value

        approved = store.approve_candidate(candidate.id, "Garanin.R.V")
        assert approved is not None
        assert approved.status == CandidateStatus.APPROVED.value
        assert approved.approved_by == "Garanin.R.V"

    def test_reject_candidate(self, store: ImprovementCandidateStore):
        """Test rejecting a candidate."""
        candidate = store.add_candidate(
            candidate_type=CandidateType.ROUTER_RULE.value,
            reason="Test candidate",
        )

        rejected = store.reject_candidate(candidate.id)
        assert rejected is not None
        assert rejected.status == CandidateStatus.REJECTED.value

    def test_get_candidates_by_status(self, store: ImprovementCandidateStore):
        """Test getting candidates by status."""
        # Add candidates
        store.add_candidate(
            candidate_type=CandidateType.PROMPT_CHANGE.value,
            reason="Candidate 1",
        )
        store.add_candidate(
            candidate_type=CandidateType.ROUTER_RULE.value,
            reason="Candidate 2",
        )

        approved_candidate = store.add_candidate(
            candidate_type=CandidateType.KNOWLEDGE_ENTRY.value,
            reason="Candidate 3",
        )
        store.approve_candidate(approved_candidate.id, "Kalachanov.V.V")

        # Get candidates
        candidates = store.get_candidates()
        assert len(candidates) == 2

        # Get approved
        approved = store.get_approved()
        assert len(approved) == 1

    def test_create_all_candidate_types(self, store: ImprovementCandidateStore):
        """Test creating all candidate types with real team members."""
        candidates = [
            store.create_prompt_change_candidate(
                prompt_name="test",
                reason="Test",
                linked_failures=["swtr-1"],
                proposed_diff="diff",
                created_by="Kalachanov.V.V",
            ),
            store.create_router_rule_candidate(
                intent="test",
                reason="Test",
                linked_failures=["swtr-2"],
                proposed_rule={},
                created_by="Garanin.R.V",
            ),
            store.create_knowledge_entry_candidate(
                key="test",
                category="test",
                content="test",
                reason="Test",
                linked_failures=["swtr-3"],
                created_by="Agataeva.A.Z",
            ),
            store.create_golden_test_candidate(
                test_name="test",
                reason="Test",
                linked_failures=["swtr-4"],
                test_code="test",
                created_by="Dolgovskoy.E.N",
            ),
            store.create_capability_change_candidate(
                capability_name="test",
                reason="Test",
                linked_failures=["swtr-5"],
                proposed_changes={},
                created_by="Kryukov.V.A",
            ),
            store.create_config_change_candidate(
                config_name="test",
                reason="Test",
                linked_failures=["swtr-6"],
                proposed_changes={},
                created_by="Garanin.R.V",
            ),
        ]

        assert len(candidates) == 6
        assert all(c.status == CandidateStatus.CANDIDATE.value for c in candidates)

    def test_version_tracking(self, store: ImprovementCandidateStore):
        """Test version tracking with real team data."""
        candidate = store.add_candidate(
            candidate_type=CandidateType.PROMPT_CHANGE.value,
            reason="Initial",
            created_by="Kalachanov.V.V",
        )

        assert candidate.version == 1

        # Approve (increments version)
        store.approve_candidate(candidate.id, "Garanin.R.V")
        assert candidate.version == 2

        # Deprecate (increments version)
        candidate.deprecate()
        assert candidate.version >= 2


class TestImprovementCandidateRealTeamIntegration:
    """Integration tests with real SWTR team data."""

    def test_full_candidate_lifecycle(self, store: ImprovementCandidateStore):
        """Test full candidate lifecycle with real team members."""
        # 1. Create candidate for real team issue
        candidate = store.create_prompt_change_candidate(
            prompt_name="sprint_explainer",
            reason="Repeated confusion about sprint health metrics",
            linked_failures=["swtr-trace-1", "swtr-trace-2", "swtr-trace-3"],
            proposed_diff="Add more specific instructions for sprint health",
            created_by="Kalachanov.V.V",  # Real team member
        )

        assert candidate.status == CandidateStatus.CANDIDATE.value
        assert len(candidate.linked_failures) == 3

        # 2. Review and approve by different team member
        approved = store.approve_candidate(candidate.id, "Garanin.R.V")
        assert approved is not None
        assert approved.status == CandidateStatus.APPROVED.value
        assert approved.approved_by == "Garanin.R.V"
        assert approved.version == 2

        # 3. Update with real team reference
        updated_content = approved.proposed_content or {}
        updated_content["team_reference"] = "OLAP/DMS team"
        approved.proposed_content = updated_content
        approved.updated_at = approved.updated_at

        # 4. Verify final state
        final = store.get_by_id(candidate.id)
        assert final.status == CandidateStatus.APPROVED.value
        assert final.created_by == "Kalachanov.V.V"
        assert final.approved_by == "Garanin.R.V"

    def test_candidate_with_multiple_real_failures(self, store: ImprovementCandidateStore):
        """Test candidate linked to multiple real failures."""
        # Simulate multiple real SWTR failures
        failure_ids = [
            "swtr-trace-001",
            "swtr-trace-002", 
            "swtr-trace-003",
            "swtr-trace-004",
            "swtr-trace-005",
        ]

        candidate = store.create_knowledge_entry_candidate(
            key="terminology:velocity",
            category="terminology",
            content="Velocity = completed story points per sprint",
            reason="Multiple failures with velocity queries from real team members",
            linked_failures=failure_ids,
            created_by="Kalachanov.V.V",
        )

        assert len(candidate.linked_failures) == 5
        assert all("swtr-trace" in fid for fid in candidate.linked_failures)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
