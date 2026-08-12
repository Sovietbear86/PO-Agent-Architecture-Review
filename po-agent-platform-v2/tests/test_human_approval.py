"""Tests for Human Approval Gate with real SWTR data."""

import pytest

from po_agent.shadow.approval import (
    HumanApprovalGate,
    HumanApprovalRecord,
    ApprovalStatus,
)


@pytest.fixture
def approval_gate():
    """Create human approval gate."""
    g = HumanApprovalGate(db_path=":memory:")
    yield g
    g.close()


class TestHumanApprovalGateBasic:
    """Tests for basic human approval gate operations."""

    def test_request_approval(self, approval_gate: HumanApprovalGate):
        """Test requesting approval."""
        record = approval_gate.request_approval(
            gate_record_id="gate-1",
            prompt_name="task_summarizer",
            shadow_version=2,
            requested_by="Kalachanov.V.V",
            approval_reason="Testing new prompt version",
        )

        assert record.gate_record_id == "gate-1"
        assert record.prompt_name == "task_summarizer"
        assert record.shadow_version == 2
        assert record.status == ApprovalStatus.PENDING.value
        assert "Kalachanov" in record.requested_by

    def test_approve_record(self, approval_gate: HumanApprovalGate):
        """Test approving a record."""
        record = approval_gate.request_approval(
            gate_record_id="gate-1",
            prompt_name="task_summarizer",
            shadow_version=2,
        )

        assert record.status == ApprovalStatus.PENDING.value

        approved = approval_gate.approve(
            record.id,
            approved_by="Garanin.R.V",
            reason="Approved after testing",
        )

        assert approved is not None
        assert approved.status == ApprovalStatus.APPROVED.value
        assert approved.approved_by == "Garanin.R.V"
        assert "Approved after" in approved.approval_reason

    def test_reject_record(self, approval_gate: HumanApprovalGate):
        """Test rejecting a record."""
        record = approval_gate.request_approval(
            gate_record_id="gate-1",
            prompt_name="task_summarizer",
            shadow_version=2,
        )

        rejected = approval_gate.reject(
            record.id,
            approved_by="Kalachanov.V.V",
            reason="Failed comparison tests",
        )

        assert rejected.status == ApprovalStatus.REJECTED.value
        assert "Failed comparison" in rejected.approval_reason


class TestHumanApprovalGateSWTR:
    """Tests for Human Approval Gate with real SWTR data."""

    def test_approval_with_real_team_member(self, approval_gate: HumanApprovalGate):
        """Test approval with real team member."""
        record = approval_gate.request_approval(
            gate_record_id="gate-kalachanov-1",
            prompt_name="sprint_explainer",
            shadow_version=3,
            requested_by="Kalachanov.V.V",
            approval_reason="Requesting approval for sprint explainer v3",
        )

        assert record.requested_by == "Kalachanov.V.V"

    def test_multiple_approvals_for_same_prompt(self, approval_gate: HumanApprovalGate):
        """Test multiple approvals for the same prompt."""
        # Request approvals
        approval_gate.request_approval(
            gate_record_id="gate-1",
            prompt_name="task_summarizer",
            shadow_version=2,
            requested_by="Kalachanov.V.V",
        )

        approval_gate.request_approval(
            gate_record_id="gate-2",
            prompt_name="task_summarizer",
            shadow_version=3,
            requested_by="Garanin.R.V",
        )

        approvals = approval_gate.get_by_prompt("task_summarizer")
        assert len(approvals) == 2

    def test_approval_statistics_with_real_team(self, approval_gate: HumanApprovalGate):
        """Test approval statistics with real team members."""
        # Create approvals
        approval_gate.request_approval(
            gate_record_id="gate-1",
            prompt_name="velocity_calculator",
            shadow_version=2,
            requested_by="Kalachanov.V.V",
        )

        # Store the first record ID and approve it
        first_record_id = approval_gate.get_pending()[0].id
        approval_gate.approve(
            first_record_id,
            approved_by="Garanin.R.V",
        )

        approval_gate.request_approval(
            gate_record_id="gate-2",
            prompt_name="velocity_calculator",
            shadow_version=3,
            requested_by="Agataeva.A.Z",
        )

        stats = approval_gate.get_statistics("velocity_calculator")

        assert stats["total"] == 2
        assert stats["approved"] == 1
        assert stats["pending"] == 1
        assert stats["approval_rate"] == 0.5


class TestHumanApprovalGateRealTeamIntegration:
    """Integration tests with real SWTR team data."""

    def test_full_approval_lifecycle(self, approval_gate: HumanApprovalGate):
        """Test full approval lifecycle with real team members."""
        # 1. Request approval from Kalachanov.V.V
        record1 = approval_gate.request_approval(
            gate_record_id="gate-kalachanov-1",
            prompt_name="sprint_health_explainer",
            shadow_version=2,
            requested_by="Kalachanov.V.V",
            approval_reason="Testing new sprint health metrics",
        )

        assert record1.status == ApprovalStatus.PENDING.value
        assert "Kalachanov" in record1.requested_by

        # 2. Garanin.R.V approves
        approved = approval_gate.approve(
            record1.id,
            approved_by="Garanin.R.V",
            reason="Approved after successful shadow testing",
        )

        assert approved.status == ApprovalStatus.APPROVED.value
        assert "Garanin" in approved.approved_by

        # 3. Agataeva.A.Z requests another approval
        record2 = approval_gate.request_approval(
            gate_record_id="gate-agataeva-1",
            prompt_name="sprint_health_explainer",
            shadow_version=3,
            requested_by="Agataeva.A.Z",
            approval_reason="Adding risk analysis to sprint metrics",
        )

        # 4. Reject by Dolgovskoy.E.N
        rejected = approval_gate.reject(
            record2.id,
            approved_by="Dolgovskoy.E.N",
            reason="Risk analysis not properly implemented",
        )

        assert rejected.status == ApprovalStatus.REJECTED.value

    def test_multiple_team_members_approving(self, approval_gate: HumanApprovalGate):
        """Test multiple team members approving different prompts."""
        prompts = [
            ("task_summarizer", "Kalachanov.V.V", "Garanin.R.V"),
            ("sprint_explainer", "Garanin.R.V", "Agataeva.A.Z"),
            ("task_quality_analyzer", "Agataeva.A.Z", "Dolgovskoy.E.N"),
        ]

        record_ids = []
        for prompt, requested_by, approved_by in prompts:
            record = approval_gate.request_approval(
                gate_record_id=f"gate-{prompt}",
                prompt_name=prompt,
                shadow_version=2,
                requested_by=requested_by,
            )
            record_ids.append((record.id, approved_by, requested_by))
        
        for record_id, approved_by, _ in record_ids:
            approval_gate.approve(
                record_id,
                approved_by=approved_by,
            )

        # Verify all approved
        approved = approval_gate.get_approved()
        assert len(approved) == 3

        # Verify team members
        requesters = {r.requested_by for r in approved}
        assert "Kalachanov.V.V" in requesters
        assert "Garanin.R.V" in requesters
        assert "Agataeva.A.Z" in requesters


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
