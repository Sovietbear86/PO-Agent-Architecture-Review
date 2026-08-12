"""Legacy comparison report for PO Agent Platform v2.1 vs s21-team-performance-agent.

This module provides comparison utilities to analyze differences between
the new PO Agent Platform v2.1 and the legacy s21-team-performance-agent.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ComparisonResult(Enum):
    """Result of comparison."""
    MATCHES = "matches"
    SUPERSEDED = "superseded"
    IMPROVED = "improved"
    MISSING = "missing"
    DIFFERENT = "different"


@dataclass
class FeatureComparison:
    """Comparison result for a single feature."""
    feature_name: str
    legacy_present: bool
    v21_present: bool
    result: ComparisonResult
    notes: str = ""


@dataclass
class APIDifference:
    """API difference report."""
    endpoint: str
    legacy_exists: bool
    v21_exists: bool
    result: ComparisonResult
    notes: str = ""


@dataclass
class DataModelComparison:
    """Data model comparison."""
    model_name: str
    legacy_fields: list[str]
    v21_fields: list[str]
    compatibility: str  # "compatible", "superset", "subset", "incompatible"


class LegacyComparison:
    """Compare PO Agent Platform v2.1 with legacy s21-team-performance-agent."""

    def __init__(self):
        """Initialize comparison."""
        self.features: list[FeatureComparison] = []
        self.apis: list[APIDifference] = []
        self.data_models: list[DataModelComparison] = []

    def compare_feature(self, feature_name: str, legacy_present: bool, v21_present: bool, notes: str = "") -> FeatureComparison:
        """Compare a feature between legacy and v2.1."""
        if legacy_present and v21_present:
            result = ComparisonResult.MATCHES
        elif legacy_present and not v21_present:
            result = ComparisonResult.MISSING
        elif not legacy_present and v21_present:
            result = ComparisonResult.SUPERSEDED
        else:
            result = ComparisonResult.DIFFERENT

        comparison = FeatureComparison(
            feature_name=feature_name,
            legacy_present=legacy_present,
            v21_present=v21_present,
            result=result,
            notes=notes,
        )
        self.features.append(comparison)
        return comparison

    def compare_api(self, endpoint: str, legacy_exists: bool, v21_exists: bool, notes: str = "") -> APIDifference:
        """Compare an API endpoint."""
        if legacy_exists and v21_exists:
            result = ComparisonResult.MATCHES
        elif legacy_exists and not v21_exists:
            result = ComparisonResult.MISSING
        elif not legacy_exists and v21_exists:
            result = ComparisonResult.SUPERSEDED
        else:
            result = ComparisonResult.DIFFERENT

        diff = APIDifference(
            endpoint=endpoint,
            legacy_exists=legacy_exists,
            v21_exists=v21_exists,
            result=result,
            notes=notes,
        )
        self.apis.append(diff)
        return diff

    def compare_data_model(self, model_name: str, legacy_fields: list[str], v21_fields: list[str]) -> DataModelComparison:
        """Compare data models."""
        legacy_set = set(legacy_fields)
        v21_set = set(v21_fields)

        if legacy_set == v21_set:
            compatibility = "compatible"
        elif v21_set.issuperset(legacy_set):
            compatibility = "superset"
        elif v21_set.issubset(legacy_set):
            compatibility = "subset"
        else:
            compatibility = "incompatible"

        comparison = DataModelComparison(
            model_name=model_name,
            legacy_fields=legacy_fields,
            v21_fields=v21_fields,
            compatibility=compatibility,
        )
        self.data_models.append(comparison)
        return comparison

    def get_overall_status(self) -> str:
        """Get overall comparison status."""
        matches = sum(1 for f in self.features if f.result == ComparisonResult.MATCHES)
        missing = sum(1 for f in self.features if f.result == ComparisonResult.MISSING)
        improved = sum(1 for f in self.features if f.result == ComparisonResult.SUPERSEDED)

        if missing > 0:
            return f"PENDING_MIGRATION: {missing} features missing"
        elif improved > 0:
            return f"IMPROVED: {improved} features enhanced"
        else:
            return "FULLY_COMPATIBLE"

    def generate_report(self) -> dict:
        """Generate comparison report."""
        return {
            "overall_status": self.get_overall_status(),
            "features": [f.__dict__ for f in self.features],
            "apis": [a.__dict__ for a in self.apis],
            "data_models": [d.__dict__ for d in self.data_models],
        }


# Known comparisons
LEGACY_FEATURES = {
    "task_management": True,
    "team_analysis": True,
    "sprint_metrics": True,
    "quality_assessment": True,
    "llm_integration": True,
    "curated_memory": True,
    "mcp_server": True,
    "fastapi_backend": True,
    "frontend_spa": False,
}

V21_FEATURES = {
    "task_management": True,
    "team_analysis": True,
    "sprint_metrics": True,
    "quality_assessment": True,
    "llm_integration": True,
    "curated_memory": True,
    "mcp_server": True,
    "fastapi_backend": True,
    "frontend_spa": True,
    "knowledge_layer": True,
    "action_contracts": True,
    "shadow_mode": True,
    "human_approval": True,
    "promotion_rollback": True,
    "prompt_registry": True,
    "version_history": True,
    "agent_history": True,
    "regression_suite": True,
}


def generate_legacy_comparison() -> LegacyComparison:
    """Generate legacy comparison report."""
    comparison = LegacyComparison()

    # Compare features
    for feature in LEGACY_FEATURES:
        comparison.compare_feature(
            feature_name=feature,
            legacy_present=LEGACY_FEATURES.get(feature, False),
            v21_present=V21_FEATURES.get(feature, False),
        )

    # Compare APIs
    comparison.compare_api("/api/v1/tasks", True, True, notes="Fully compatible")
    comparison.compare_api("/api/v1/tasks/{id}", True, True, notes="Fully compatible")
    comparison.compare_api("/api/v1/sprints", True, True, notes="Fully compatible")
    comparison.compare_api("/api/v1/team", True, True, notes="Fully compatible")
    comparison.compare_api("/api/v1/quality", True, True, notes="Fully compatible")
    comparison.compare_api("/api/v1/mcp", True, True, notes="MCP compatible")

    # Compare data models
    comparison.compare_data_model("Task", ["id", "title", "description", "assignee", "status", "created_at", "updated_at", "deadline"], ["id", "title", "description", "assignee", "status", "created_at", "updated_at", "deadline"])
    comparison.compare_data_model("TeamMember", ["login", "name", "role", "capacity_hours", "skills", "team_affiliation"], ["login", "name", "role", "capacity_hours", "skills", "team_affiliation"])

    return comparison
