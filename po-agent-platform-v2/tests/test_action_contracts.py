"""Tests for Action Contracts with real SWTR data."""

import pytest

from po_agent.contracts.actions import (
    ActionProposal,
    AuditRecord,
    ActionManager,
    ActionStatus,
    ActionType,
)


@pytest.fixture
def action_manager():
    """Create action manager."""
    m = ActionManager(db_path=":memory:")
    yield m
    m.close()


class TestActionContractsBasic:
    """Tests for basic action contracts operations."""

    def test_create_proposal(self, action_manager: ActionManager):
        """Test creating an action proposal."""
        proposal = action_manager.create_proposal(
            action_type=ActionType.CREATE_TASK.value,
            target="WMB-123",
            details={"title": "Test task", "description": "Test"},
            requested_by="Kalachanov.V.V",
        )

        assert proposal.action_type == ActionType.CREATE_TASK.value
        assert proposal.target == "WMB-123"
        assert "Kalachanov" in proposal.requested_by
        assert proposal.status == ActionStatus.PROPOSAL.value

    def test_confirm_proposal(self, action_manager: ActionManager):
        """Test confirming a proposal."""
        proposal = action_manager.create_proposal(
            action_type=ActionType.UPDATE_TASK.value,
            target="WMB-123",
            details={"title": "Updated title"},
        )

        proposal.confirm(confirmed_by="Garanin.R.V", reason="Approved after review")

        assert proposal.status == ActionStatus.CONFIRMED.value
        assert proposal.confirmed_by == "Garanin.R.V"

    def test_reject_proposal(self, action_manager: ActionManager):
        """Test rejecting a proposal."""
        proposal = action_manager.create_proposal(
            action_type=ActionType.DELETE_TASK.value,
            target="WMB-123",
            details={},
        )

        proposal.reject(confirmed_by="Agataeva.A.Z", reason="Task still in progress")

        assert proposal.status == ActionStatus.REJECTED.value
        assert "still in progress" in proposal.details["rejection_reason"]

    def test_execute_proposal(self, action_manager: ActionManager):
        """Test executing a proposal."""
        proposal = action_manager.create_proposal(
            action_type=ActionType.CREATE_TASK.value,
            target="WMB-123",
            details={"title": "Test task"},
        )

        proposal.execute(success=True, result={"id": "WMB-123", "status": "created"})

        assert proposal.status == ActionStatus.EXECUTED.value
        assert proposal.result["status"] == "created"

    def test_log_audit_record(self, action_manager: ActionManager):
        """Test logging an audit record."""
        proposal = action_manager.create_proposal(
            action_type=ActionType.CREATE_TASK.value,
            target="WMB-123",
            details={},
        )

        audit = action_manager.log_audit(
            action_id=proposal.id,
            user_id="Kalachanov.V.V",
            action_type=ActionType.CREATE_TASK.value,
            status="executed",
            details={"task_id": "WMB-123"},
        )

        assert audit.action_id == proposal.id
        assert audit.user_id == "Kalachanov.V.V"
        assert audit.status == "executed"


class TestActionContractsSWTR:
    """Tests for Action Contracts with real SWTR data."""

    def test_proposal_with_real_team_member(self, action_manager: ActionManager):
        """Test proposal with real team member."""
        proposal = action_manager.create_proposal(
            action_type=ActionType.UPDATE_TASK.value,
            target="DMS-456",
            details={"status": "in_progress"},
            requested_by="Kalachanov.V.V",
        )

        assert proposal.requested_by == "Kalachanov.V.V"

    def test_audit_with_multiple_team_members(self, action_manager: ActionManager):
        """Test audit with multiple team members."""
        proposal = action_manager.create_proposal(
            action_type=ActionType.CREATE_ROLLBACK.value,
            target="sprint_health_metrics",
            details={"from": 2, "to": 1},
            requested_by="Kalachanov.V.V",
        )

        # Confirm by Garanin.R.V
        proposal.confirm(confirmed_by="Garanin.R.V")
        audit1 = action_manager.log_audit(
            action_id=proposal.id,
            user_id="Garanin.R.V",
            action_type="confirm",
            status="confirmed",
        )

        # Execute by Agataeva.A.Z
        proposal.execute(success=True, result={"rolled_back_to": 1})
        audit2 = action_manager.log_audit(
            action_id=proposal.id,
            user_id="Agataeva.A.Z",
            action_type="execute",
            status="executed",
        )

        assert audit1.user_id == "Garanin.R.V"
        assert audit2.user_id == "Agataeva.A.Z"

    def test_multiple_proposals_from_different_members(self, action_manager: ActionManager):
        """Test multiple proposals from different team members."""
        proposals = [
            action_manager.create_proposal(
                action_type=ActionType.CREATE_TASK.value,
                target=f"WMB-{i}",
                details={"title": f"Task {i}"},
                requested_by="Kalachanov.V.V",
            ) for i in range(3)
        ]

        proposals += [
            action_manager.create_proposal(
                action_type=ActionType.UPDATE_TASK.value,
                target=f"DMS-{i}",
                details={"status": "done"},
                requested_by="Garanin.R.V",
            ) for i in range(3, 6)
        ]

        assert len(action_manager.proposals) == 6

        # Verify each proposer
        kalachanov_props = [p for p in action_manager.proposals if p.requested_by == "Kalachanov.V.V"]
        garanin_props = [p for p in action_manager.proposals if p.requested_by == "Garanin.R.V"]

        assert len(kalachanov_props) == 3
        assert len(garanin_props) == 3


class TestActionContractsRealTeamIntegration:
    """Integration tests with real SWTR team data."""

    def test_full_proposal_lifecycle(self, action_manager: ActionManager):
        """Test full proposal lifecycle with real team members."""
        # 1. Kalachanov.V.V creates proposal
        proposal = action_manager.create_proposal(
            action_type=ActionType.CREATE_PROMOTION.value,
            target="task_summarizer",
            details={"from_version": 1, "to_version": 2},
            requested_by="Kalachanov.V.V",
        )

        assert proposal.status == ActionStatus.PROPOSAL.value

        # 2. Garanin.R.V confirms
        proposal.confirm(confirmed_by="Garanin.R.V", reason="Approved for promotion")
        assert proposal.status == ActionStatus.CONFIRMED.value

        # 3. Execute
        proposal.execute(
            success=True,
            result={"promoted_version": 2},
        )
        assert proposal.status == ActionStatus.EXECUTED.value

        # 4. Log audit
        action_manager.log_audit(
            action_id=proposal.id,
            user_id="Dolgovskoy.E.N",
            action_type="audit",
            status="completed",
        )

    def test_multiple_team_members_proposing(self, action_manager: ActionManager):
        """Test multiple team members proposing actions."""
        team_members = [
            ("Kalachanov.V.V", ActionType.CREATE_TASK),
            ("Garanin.R.V", ActionType.UPDATE_TASK),
            ("Agataeva.A.Z", ActionType.CREATE_ROLLBACK),
            ("Dolgovskoy.E.N", ActionType.PROMPT_CHANGE),
        ]

        for member, action_type in team_members:
            proposal = action_manager.create_proposal(
                action_type=action_type.value,
                target=f"target-{member}",
                details={},
                requested_by=member,
            )
            proposal.confirm(confirmed_by="Kalachanov.V.V")

        stats = action_manager.get_statistics()
        assert stats["total"] == 4
        assert stats["confirmed"] == 4

    def test_audit_trail_with_real_team(self, action_manager: ActionManager):
        """Test audit trail with real team members."""
        proposal = action_manager.create_proposal(
            action_type=ActionType.CONFIG_CHANGE.value,
            target="quality_rules",
            details={"threshold": 0.9},
            requested_by="Kalachanov.V.V",
        )

        # Multiple audit records
        action_manager.log_audit(
            action_id=proposal.id,
            user_id="Kalachanov.V.V",
            action_type="proposal",
            status="created",
        )

        action_manager.log_audit(
            action_id=proposal.id,
            user_id="Garanin.R.V",
            action_type="confirmation",
            status="confirmed",
        )

        action_manager.log_audit(
            action_id=proposal.id,
            user_id="Agataeva.A.Z",
            action_type="execution",
            status="executed",
        )

        audit_records = action_manager.get_audit_records(proposal.id)
        assert len(audit_records) == 4

        # Verify team members
        users = {r.user_id for r in audit_records}
        assert "Kalachanov.V.V" in users
        assert "Garanin.R.V" in users
        assert "Agataeva.A.Z" in users

    def test_statistics_with_real_team(self, action_manager: ActionManager):
        """Test statistics with real team members."""
        # Create proposals from different team members
        for i in range(5):
            action_manager.create_proposal(
                action_type=ActionType.CREATE_TASK.value,
                target=f"WMB-{i}",
                details={},
                requested_by=["Kalachanov.V.V", "Garanin.R.V"][i % 2],
            )

        stats = action_manager.get_statistics()
        assert stats["total"] == 5
        assert stats.get("proposed", 0) == 5 or stats.get("proposal", 0) == 5
