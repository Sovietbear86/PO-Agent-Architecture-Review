"""AI PDLC Dashboard API for PO Agent Platform v2.

Provides monitoring endpoints for the entire AI PDLC process:
- GET /dashboard/stats - overall statistics
- GET /dashboard/prompts - prompts with versions
- GET /dashboard/promotions - promotion/rollback history
- GET /dashboard/gates - gate status
- GET /dashboard/failures - recent failures
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Optional

from po_agent.versions.prompt_registry import PromptRegistry
from po_agent.versions.registry import VersionRegistry
from po_agent.shadow.mode import ShadowModeStore
from po_agent.shadow.comparison import ComparisonEngine
from po_agent.shadow.gate import RegressionGate
from po_agent.shadow.approval import HumanApprovalGate
from po_agent.shadow.promotion import PromotionManager
from po_agent.improvement.candidate import ImprovementCandidateStore
from po_agent.evaluation.failure import FailureStore


class AIPDLCDashboard:
    """AI PDLC Dashboard with aggregated statistics."""

    def __init__(self, db_path: str = ":memory:"):
        """Initialize dashboard with all registries.

        Args:
            db_path: SQLite database path
        """
        self.db_path = db_path

        # Initialize all registries with same DB
        self.prompt_registry = PromptRegistry(db_path)
        self.version_registry = VersionRegistry(db_path)
        self.shadow_store = ShadowModeStore(db_path)
        self.comparison_engine = ComparisonEngine(db_path)
        self.regression_gate = RegressionGate(db_path)
        self.human_approval = HumanApprovalGate(db_path)
        self.promotion_manager = PromotionManager(db_path)
        self.improvement_store = ImprovementCandidateStore(db_path)
        self.failure_store = FailureStore()

    def get_stats(self) -> dict:
        """Get overall dashboard statistics.

        Returns:
            Dictionary with all statistics
        """
        return {
            "prompts": {
                "total_versions": len(self.prompt_registry.prompts),
                "active_versions": len(self.prompt_registry.get_all_active()),
                "candidates": len(self.prompt_registry.get_candidates()),
            },
            "versions": {
                "total": len(self.version_registry.versions),
                "active": len(self.version_registry.get_all_active()),
                "deprecated": len([v for v in self.version_registry.versions 
                                   if v.status == "deprecated"]),
            },
            "promotions": self.promotion_manager.get_statistics(),
            "gates": self.regression_gate.get_statistics(),
            "approvals": self.human_approval.get_statistics(),
            "failures": self.failure_store.get_failure_counts(),
            "improvements": {
                "total": len(self.improvement_store.candidates),
                "candidates": len(self.improvement_store.get_candidates()),
                "approved": len(self.improvement_store.get_approved()),
            },
            "shadow_modes": {
                "total": len(self.shadow_store.configs),
                "enabled": len(self.shadow_store.get_enabled()),
            },
            "comparisons": {
                "total": len(self.comparison_engine.comparisons),
                "passed": len([c for c in self.comparison_engine.comparisons
                              if c.result == "passed"]),
                "failed": len([c for c in self.comparison_engine.comparisons
                              if c.result == "failed"]),
            },
        }

    def get_prompts(self, limit: int = 50) -> list[dict]:
        """Get all prompts with versions.

        Args:
            limit: Maximum number of results

        Returns:
            List of prompt dictionaries
        """
        prompts = []
        seen = set()

        for entry in self.prompt_registry.prompts[:limit]:
            key = (entry.prompt_name, entry.version)
            if key not in seen:
                seen.add(key)
                prompts.append({
                    "prompt_name": entry.prompt_name,
                    "version": entry.version,
                    "status": entry.status,
                    "created_at": entry.created_at.isoformat(),
                })

        return prompts

    def get_promotions(self, limit: int = 50) -> list[dict]:
        """Get promotion/rollback history.

        Args:
            limit: Maximum number of results

        Returns:
            List of promotion dictionaries
        """
        return [p.to_dict() for p in self.promotion_manager.promotions[:limit]]

    def get_gates(self, limit: int = 50) -> list[dict]:
        """Get gate records.

        Args:
            limit: Maximum number of results

        Returns:
            List of gate dictionaries
        """
        return [g.to_dict() for g in self.regression_gate.gates[:limit]]

    def get_failures(self, limit: int = 50) -> list[dict]:
        """Get failure records.

        Args:
            limit: Maximum number of results

        Returns:
            List of failure dictionaries
        """
        return [f.to_dict() for f in self.failure_store.failures[:limit]]

    def get_improvements(self, limit: int = 50) -> list[dict]:
        """Get improvement candidates.

        Args:
            limit: Maximum number of results

        Returns:
            List of improvement dictionaries
        """
        return [c.to_dict() for c in self.improvement_store.candidates[:limit]]

    def get_shadow_modes(self, limit: int = 50) -> list[dict]:
        """Get shadow mode configurations.

        Args:
            limit: Maximum number of results

        Returns:
            List of shadow mode dictionaries
        """
        return [s.to_dict() for s in self.shadow_store.configs[:limit]]

    def get_comparison_stats(self, prompt_name: Optional[str] = None) -> dict:
        """Get comparison statistics.

        Args:
            prompt_name: Optional prompt name filter

        Returns:
            Dictionary with comparison statistics
        """
        if prompt_name:
            stats = self.comparison_engine.get_statistics(prompt_name)
        else:
            stats = self.comparison_engine.get_statistics()
        return stats

    def get_gate_stats(self, prompt_name: Optional[str] = None) -> dict:
        """Get gate statistics.

        Args:
            prompt_name: Optional prompt name filter

        Returns:
            Dictionary with gate statistics
        """
        if prompt_name:
            stats = self.regression_gate.get_statistics(prompt_name)
        else:
            stats = self.regression_gate.get_statistics()
        return stats

    def close(self) -> None:
        """Close all database connections."""
        self.prompt_registry.close()
        self.version_registry.close()
        self.shadow_store.close()
        self.comparison_engine.close()
        self.regression_gate.close()
        self.human_approval.close()
        self.promotion_manager.close()
        self.improvement_store.close()
        self.failure_store.close()
