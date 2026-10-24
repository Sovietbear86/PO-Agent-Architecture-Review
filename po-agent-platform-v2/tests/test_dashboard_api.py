"""Tests for AI PDLC Dashboard API with real SWTR data."""

import pytest

from po_agent.dashboard.api import AIPDLCDashboard


@pytest.fixture
def dashboard():
    """Create AI PDLC dashboard."""
    d = AIPDLCDashboard(db_path=":memory:")
    yield d
    d.close()


class TestAIPDLCDashboardBasic:
    """Tests for basic dashboard operations."""

    def test_get_stats(self, dashboard: AIPDLCDashboard):
        """Test getting overall statistics."""
        stats = dashboard.get_stats()

        assert "prompts" in stats
        assert "versions" in stats
        assert "promotions" in stats
        assert "gates" in stats
        assert "approvals" in stats
        assert "failures" in stats
        assert "improvements" in stats
        assert "shadow_modes" in stats
        assert "comparisons" in stats

    def test_get_prompts(self, dashboard: AIPDLCDashboard):
        """Test getting prompts list."""
        # Add some prompts
        dashboard.prompt_registry.add_prompt(
            prompt_name="task_summarizer",
            version=1,
            content="Summary prompt",
        )
        dashboard.prompt_registry.add_prompt(
            prompt_name="sprint_explainer",
            version=1,
            content="Sprint prompt",
        )

        prompts = dashboard.get_prompts()

        assert len(prompts) == 2
        assert any(p["prompt_name"] == "task_summarizer" for p in prompts)
        assert any(p["prompt_name"] == "sprint_explainer" for p in prompts)

    def test_get_promotions(self, dashboard: AIPDLCDashboard):
        """Test getting promotions list."""
        # Add promotions
        dashboard.promotion_manager.create_promotion(
            prompt_name="task_summarizer",
            from_version=1,
            to_version=2,
        )

        promotions = dashboard.get_promotions()

        assert len(promotions) >= 1
        assert promotions[0]["action_type"] == "promotion"


class TestAIPDLCDashboardSWTR:
    """Tests for AI PDLC Dashboard with real SWTR data."""

    def test_dashboard_with_real_team_data(self, dashboard: AIPDLCDashboard):
        """Test dashboard with real team member references."""
        # Add various data with real team members
        dashboard.shadow_store.add_config(
            prompt_name="sprint_explainer",
            shadow_version=3,
            created_by="Kalachanov.V.V",
        )

        dashboard.promotion_manager.create_promotion(
            prompt_name="velocity_calculator",
            from_version=1,
            to_version=2,
            requested_by="Garanin.R.V",
        )

        dashboard.regression_gate.check(
            prompt_name="sprint_health",
            shadow_version=2,
            comparisons=[{"passed_threshold": True}],
            threshold=0.8,
            reviewed_by="Agataeva.A.Z",
        )

        stats = dashboard.get_stats()

        assert stats["promotions"]["total"] >= 1
        assert stats["gates"]["total"] >= 1

    def test_dashboard_with_multiple_team_members(self, dashboard: AIPDLCDashboard):
        """Test dashboard with multiple team members."""
        team_members = [
            ("task_summarizer", "Kalachanov.V.V"),
            ("sprint_explainer", "Garanin.R.V"),
            ("task_quality_analyzer", "Agataeva.A.Z"),
        ]

        for prompt_name, member in team_members:
            dashboard.shadow_store.add_config(
                prompt_name=prompt_name,
                shadow_version=2,
                created_by=member,
            )

        # Get shadow modes
        shadow_modes = dashboard.get_shadow_modes()
        shadow_names = [s["prompt_name"] for s in shadow_modes]

        assert "task_summarizer" in shadow_names
        assert "sprint_explainer" in shadow_names
        assert "task_quality_analyzer" in shadow_names

    def test_dashboard_comparison_stats(self, dashboard: AIPDLCDashboard):
        """Test dashboard comparison statistics."""
        # Add comparisons
        dashboard.comparison_engine.compare(
            config_id="config-1",
            prompt_name="task_summarizer",
            prod_version=1,
            shadow_version=2,
            prod_output="Same output",
            shadow_output="Same output",
            threshold=0.8,
        )

        dashboard.comparison_engine.compare(
            config_id="config-2",
            prompt_name="task_summarizer",
            prod_version=1,
            shadow_version=2,
            prod_output="Different",
            shadow_output="Output",
            threshold=0.8,
        )

        stats = dashboard.get_comparison_stats("task_summarizer")

        assert stats["total"] == 2
        assert stats["passed"] == 1
        assert stats["failed"] == 1


class TestAIPDLCDashboardRealTeamIntegration:
    """Integration tests with real SWTR team data."""

    def test_full_dashboard_lifecycle(self, dashboard: AIPDLCDashboard):
        """Test full dashboard lifecycle with real team members."""
        # 1. Kalachanov.V.V creates shadow mode
        dashboard.shadow_store.add_config(
            prompt_name="sprint_health_explainer",
            shadow_version=2,
            created_by="Kalachanov.V.V",
        )

        # 2. Run comparisons
        dashboard.comparison_engine.compare(
            config_id="shadow-1",
            prompt_name="sprint_health_explainer",
            prod_version=1,
            shadow_version=2,
            prod_output="Health: good",
            shadow_output="Health: good",
            threshold=0.8,
        )

        # 3. Garanin.R.V runs regression gate
        dashboard.regression_gate.check(
            prompt_name="sprint_health_explainer",
            shadow_version=2,
            comparisons=[{"passed_threshold": True}],
            threshold=0.8,
            reviewed_by="Garanin.R.V",
        )

        # 4. Agataeva.A.Z creates promotion
        dashboard.promotion_manager.create_promotion(
            prompt_name="sprint_health_explainer",
            from_version=1,
            to_version=2,
            requested_by="Agataeva.A.Z",
        )

        # 5. Get stats
        stats = dashboard.get_stats()

        assert stats["promotions"]["total"] >= 1
        assert stats["comparisons"]["total"] >= 1
        assert stats["gates"]["total"] >= 1

    def test_dashboard_with_all_team_members(self, dashboard: AIPDLCDashboard):
        """Test dashboard with all team members."""
        # Create data from all team members
        dashboard.shadow_store.add_config(
            prompt_name="task_summarizer",
            shadow_version=2,
            created_by="Kalachanov.V.V",
        )

        dashboard.shadow_store.add_config(
            prompt_name="sprint_explainer",
            shadow_version=3,
            created_by="Garanin.R.V",
        )

        dashboard.promotion_manager.create_promotion(
            prompt_name="task_quality_analyzer",
            from_version=1,
            to_version=2,
            requested_by="Agataeva.A.Z",
        )

        dashboard.promotion_manager.create_rollback(
            prompt_name="velocity_calculator",
            from_version=2,
            to_version=1,
            rollback_reason="Testing",
            requested_by="Dolgovskoy.E.N",
        )

        # Get all stats
        stats = dashboard.get_stats()

        assert stats["promotions"]["total"] >= 2
        assert stats["shadow_modes"]["total"] >= 2

    def test_dashboard_stats_aggregation(self, dashboard: AIPDLCDashboard):
        """Test dashboard stats aggregation."""
        # Add multiple types of data
        for i in range(3):
            dashboard.shadow_store.add_config(
                prompt_name=f"prompt_{i}",
                shadow_version=2,
                created_by=f"Member{i}.V.V",
            )

        for i in range(2):
            dashboard.promotion_manager.create_promotion(
                prompt_name=f"prompt_{i}",
                from_version=1,
                to_version=2,
            )

        stats = dashboard.get_stats()

        assert stats["shadow_modes"]["total"] == 3
        assert stats["promotions"]["total"] >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
