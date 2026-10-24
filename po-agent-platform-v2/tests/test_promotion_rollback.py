"""Tests for Promotion & Rollback with real SWTR data."""

import pytest

from po_agent.shadow.promotion import (
    PromotionManager,
    PromotionRecord,
    PromotionAction,
    PromotionStatus,
)


@pytest.fixture
def promotion_manager():
    """Create promotion manager."""
    m = PromotionManager(db_path=":memory:")
    yield m
    m.close()


class TestPromotionManagerBasic:
    """Tests for basic promotion manager operations."""

    def test_create_promotion(self, promotion_manager: PromotionManager):
        """Test creating a promotion."""
        record = promotion_manager.create_promotion(
            prompt_name="task_summarizer",
            from_version=1,
            to_version=2,
            requested_by="Kalachanov.V.V",
        )

        assert record.action_type == PromotionAction.PROMOTION.value
        assert record.prompt_name == "task_summarizer"
        assert record.from_version == 1
        assert record.to_version == 2
        assert "Kalachanov" in record.requested_by

    def test_create_rollback(self, promotion_manager: PromotionManager):
        """Test creating a rollback."""
        record = promotion_manager.create_rollback(
            prompt_name="task_summarizer",
            from_version=2,
            to_version=1,
            rollback_reason="High failure rate in shadow testing",
            requested_by="Garanin.R.V",
        )

        assert record.action_type == PromotionAction.ROLLBACK.value
        assert "High failure" in record.rollback_reason

    def test_approve_promotion(self, promotion_manager: PromotionManager):
        """Test approving a promotion."""
        record = promotion_manager.create_promotion(
            prompt_name="task_summarizer",
            from_version=1,
            to_version=2,
        )

        assert record.status == PromotionStatus.PENDING.value

        approved = promotion_manager.approve_promotion(
            record.id,
            approved_by="Kalachanov.V.V",
        )

        assert approved.status == PromotionStatus.COMPLETED.value
        assert approved.approved_by == "Kalachanov.V.V"
        assert approved.deployed_at is not None

    def test_fail_promotion(self, promotion_manager: PromotionManager):
        """Test failing a promotion."""
        record = promotion_manager.create_promotion(
            prompt_name="task_summarizer",
            from_version=1,
            to_version=2,
        )

        failed = promotion_manager.fail_promotion(
            record.id,
            reason="Connection timeout during deployment",
        )

        assert failed.status == PromotionStatus.FAILED.value
        assert "Connection timeout" in failed.rollback_reason


class TestPromotionManagerSWTR:
    """Tests for Promotion Manager with real SWTR data."""

    def test_promotion_with_real_team_member(self, promotion_manager: PromotionManager):
        """Test promotion with real team member."""
        record = promotion_manager.create_promotion(
            prompt_name="sprint_explainer",
            from_version=2,
            to_version=3,
            requested_by="Kalachanov.V.V",
        )

        assert record.requested_by == "Kalachanov.V.V"

    def test_rollback_with_real_reason(self, promotion_manager: PromotionManager):
        """Test rollback with real reason from team member."""
        record = promotion_manager.create_rollback(
            prompt_name="sprint_health_metrics",
            from_version=3,
            to_version=2,
            rollback_reason="Metrics calculation incorrect for DMS sprint",
            requested_by="Garanin.R.V",
        )

        assert "DMS sprint" in record.rollback_reason
        assert "Garanin" in record.requested_by

    def test_multiple_promotions_for_same_prompt(self, promotion_manager: PromotionManager):
        """Test multiple promotions for the same prompt."""
        promotion_manager.create_promotion(
            prompt_name="task_summarizer",
            from_version=1,
            to_version=2,
        )

        promotion_manager.create_promotion(
            prompt_name="task_summarizer",
            from_version=2,
            to_version=3,
        )

        promotions = promotion_manager.get_by_prompt("task_summarizer")
        assert len(promotions) == 2

    def test_promotion_statistics_with_real_team(self, promotion_manager: PromotionManager):
        """Test promotion statistics with real team members."""
        promotion_manager.create_promotion(
            prompt_name="velocity_calculator",
            from_version=1,
            to_version=2,
            requested_by="Kalachanov.V.V",
        )

        promotion_manager.create_rollback(
            prompt_name="velocity_calculator",
            from_version=2,
            to_version=1,
            rollback_reason="Backward compatibility issue",
            requested_by="Dolgovskoy.E.N",
        )

        stats = promotion_manager.get_statistics("velocity_calculator")

        assert stats["total"] == 2
        assert stats["promotions"] == 1
        assert stats["rollbacks"] == 1


class TestPromotionManagerRealTeamIntegration:
    """Integration tests with real SWTR team data."""

    def test_full_promotion_lifecycle(self, promotion_manager: PromotionManager):
        """Test full promotion lifecycle with real team members."""
        # 1. Kalachanov.V.V requests promotion
        record1 = promotion_manager.create_promotion(
            prompt_name="sprint_health_explainer",
            from_version=2,
            to_version=3,
            requested_by="Kalachanov.V.V",
        )

        assert record1.status == PromotionStatus.PENDING.value

        # 2. Garanin.R.V approves
        approved = promotion_manager.approve_promotion(
            record1.id,
            approved_by="Garanin.R.V",
        )

        assert approved.status == PromotionStatus.COMPLETED.value

        # 3. Agataeva.A.Z requests rollback
        record2 = promotion_manager.create_rollback(
            prompt_name="sprint_health_explainer",
            from_version=3,
            to_version=2,
            rollback_reason="Unexpected behavior in production",
            requested_by="Agataeva.A.Z",
        )

        # 4. Dolgovskoy.E.N approves rollback
        approved_rollback = promotion_manager.approve_promotion(
            record2.id,
            approved_by="Dolgovskoy.E.N",
        )

        assert approved_rollback.status == PromotionStatus.COMPLETED.value

    def test_multiple_team_members_promoting(self, promotion_manager: PromotionManager):
        """Test multiple team members promoting different prompts."""
        team_members = [
            ("task_summarizer", 1, 2, "Kalachanov.V.V"),
            ("sprint_explainer", 2, 3, "Garanin.R.V"),
            ("task_quality_analyzer", 1, 2, "Agataeva.A.Z"),
        ]

        for prompt, from_v, to_v, requested_by in team_members:
            promotion_manager.create_promotion(
                prompt_name=prompt,
                from_version=from_v,
                to_version=to_v,
                requested_by=requested_by,
            )

        # Verify all team members
        for prompt, _, _, requested_by in team_members:
            records = promotion_manager.get_by_prompt(prompt)
            assert len(records) == 1
            assert records[0].requested_by == requested_by

    def test_statistics_with_multiple_actions(self, promotion_manager: PromotionManager):
        """Test statistics with multiple promotion types."""
        # Promotions
        promotion_manager.create_promotion(
            prompt_name="task_summarizer",
            from_version=1,
            to_version=2,
        )
        promotion_manager.create_promotion(
            prompt_name="task_summarizer",
            from_version=2,
            to_version=3,
        )

        # Rollbacks
        promotion_manager.create_rollback(
            prompt_name="sprint_explainer",
            from_version=2,
            to_version=1,
            rollback_reason="Testing rollback",
        )

        stats = promotion_manager.get_statistics()

        assert stats["total"] == 3
        assert stats["promotions"] == 2
        assert stats["rollbacks"] == 1
        assert stats["pending"] == 3  # All pending initially
        assert stats["completed"] == 0

    def test_latest_promotions_with_real_team(self, promotion_manager: PromotionManager):
        """Test getting latest promotions with real team members."""
        # Create multiple promotions for same prompt
        for i in range(5):
            promotion_manager.create_promotion(
                prompt_name="task_summarizer",
                from_version=i,
                to_version=i + 1,
                requested_by=f"TeamMember{i}.V.V",
            )

        latest = promotion_manager.get_latest("task_summarizer", limit=3)
        assert len(latest) == 3

        # Check most recent first
        assert latest[0].to_version == 5
        assert latest[1].to_version == 4
        assert latest[2].to_version == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
