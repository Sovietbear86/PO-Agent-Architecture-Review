"""Tests for Legacy Comparison."""

import pytest
from po_agent.legacy.comparison import (
    LegacyComparison,
    FeatureComparison,
    ComparisonResult,
    generate_legacy_comparison,
)


class TestLegacyComparison:
    """Tests for legacy comparison functionality."""

    def test_create_comparison(self):
        """Test creating a comparison."""
        comparison = LegacyComparison()
        assert comparison is not None

    def test_compare_feature_match(self):
        """Test comparing a matching feature."""
        comparison = LegacyComparison()
        result = comparison.compare_feature(
            feature_name="task_management",
            legacy_present=True,
            v21_present=True,
        )
        assert result.result == ComparisonResult.MATCHES
        assert result.legacy_present
        assert result.v21_present

    def test_compare_feature_missing(self):
        """Test comparing a missing feature."""
        comparison = LegacyComparison()
        result = comparison.compare_feature(
            feature_name="frontend_spa",
            legacy_present=False,
            v21_present=True,
        )
        assert result.result == ComparisonResult.SUPERSEDED
        assert not result.legacy_present
        assert result.v21_present

    def test_compare_api(self):
        """Test comparing an API endpoint."""
        comparison = LegacyComparison()
        result = comparison.compare_api(
            endpoint="/api/v1/tasks",
            legacy_exists=True,
            v21_exists=True,
        )
        assert result.result == ComparisonResult.MATCHES
        assert result.legacy_exists
        assert result.v21_exists

    def test_compare_data_model(self):
        """Test comparing data models."""
        comparison = LegacyComparison()
        result = comparison.compare_data_model(
            model_name="Task",
            legacy_fields=["id", "title", "status"],
            v21_fields=["id", "title", "status", "assignee"],
        )
        assert result.compatibility == "superset"
        assert len(result.v21_fields) > len(result.legacy_fields)

    def test_generate_legacy_comparison(self):
        """Test generating full legacy comparison."""
        comparison = generate_legacy_comparison()
        report = comparison.generate_report()

        assert "overall_status" in report
        assert "features" in report
        assert "apis" in report
        assert "data_models" in report

        # Check some expected features
        feature_names = [f["feature_name"] for f in report["features"]]
        assert "task_management" in feature_names
        assert "frontend_spa" in feature_names

    def test_overall_status(self):
        """Test overall status generation."""
        comparison = LegacyComparison()

        # Add some features
        comparison.compare_feature("existing", True, True)
        comparison.compare_feature("improved", False, True)
        comparison.compare_feature("removed", True, False)

        status = comparison.get_overall_status()
        assert "PENDING" in status or "IMPROVED" in status


class TestLegacyFeatureMap:
    """Tests for legacy feature mapping."""

    def test_legacy_features_included(self):
        """Test that legacy features are mapped."""
        comparison = generate_legacy_comparison()
        report = comparison.generate_report()

        legacy_features = {"task_management", "team_analysis", "sprint_metrics", "llm_integration"}
        feature_names = {f["feature_name"] for f in report["features"]}

        for feature in legacy_features:
            assert feature in feature_names

    def test_v21_features_added(self):
        """Test that v2.1 features are mapped."""
        comparison = generate_legacy_comparison()
        report = comparison.generate_report()

        feature_names = {f["feature_name"] for f in report["features"]}
        # Check that frontend_spa was added in v2.1
        assert "frontend_spa" in feature_names

    def test_api_compatibility(self):
        """Test API compatibility."""
        comparison = generate_legacy_comparison()
        report = comparison.generate_report()

        # All main APIs should be compatible
        api_endpoints = {a["endpoint"] for a in report["apis"]}
        assert "/api/v1/tasks" in api_endpoints
        assert "/api/v1/sprints" in api_endpoints

    def test_data_model_compatibility(self):
        """Test data model compatibility."""
        comparison = generate_legacy_comparison()
        report = comparison.generate_report()

        data_models = {d["model_name"] for d in report["data_models"]}
        assert "Task" in data_models
        assert "TeamMember" in data_models


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
