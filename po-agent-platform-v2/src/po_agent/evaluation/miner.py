"""Failure Miner for PO Agent Platform v2.

Analyze historical failed/negative-feedback traces.

Output clusters such as:
- repeated routing confusion
- alias issue
- missing knowledge
- fragile prompt
- adapter mapping gap
- metric edge case

Do not modify production behavior.
Generate report only.
"""

from datetime import datetime
from typing import Optional


class FailureMinerReport:
    """Report from failure mining."""

    def __init__(
        self,
        total_failures: int,
        clusters: list[dict],
        timestamp: datetime = datetime.now(),
    ):
        """Initialize failure miner report.

        Args:
            total_failures: Total failures analyzed
            clusters: List of failure clusters
            timestamp: Mining timestamp
        """
        self.total_failures = total_failures
        self.clusters = clusters
        self.timestamp = timestamp

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_failures": self.total_failures,
            "clusters": self.clusters,
            "timestamp": self.timestamp.isoformat(),
        }


class FailureMiner:
    """Miner for failure patterns."""

    def __init__(self, failures: list[dict]):
        """Initialize failure miner.

        Args:
            failures: List of failure records
        """
        self.failures = failures

    def mine(self) -> FailureMinerReport:
        """Mine failures for patterns.

        Returns:
            Failure mining report
        """
        if not self.failures:
            return FailureMinerReport(
                total_failures=0,
                clusters=[],
            )

        clusters = []

        # Cluster 1: Repeated routing confusion
        routing_confusion = self._cluster_routing_confusion()
        if routing_confusion:
            clusters.append(routing_confusion)

        # Cluster 2: Adapter/Mapping issues
        adapter_issues = self._cluster_adapter_issues()
        if adapter_issues:
            clusters.append(adapter_issues)

        # Cluster 3: Missing knowledge
        missing_knowledge = self._cluster_missing_knowledge()
        if missing_knowledge:
            clusters.append(missing_knowledge)

        # Cluster 4: LLM schema issues
        llm_issues = self._cluster_llm_issues()
        if llm_issues:
            clusters.append(llm_issues)

        # Cluster 5: Empty sprint edge case
        empty_sprint = self._cluster_empty_sprint()
        if empty_sprint:
            clusters.append(empty_sprint)

        # Cluster 6: Entity extraction issues
        entity_issues = self._cluster_entity_extraction()
        if entity_issues:
            clusters.append(entity_issues)

        return FailureMinerReport(
            total_failures=len(self.failures),
            clusters=clusters,
        )

    def _cluster_routing_confusion(self) -> Optional[dict]:
        """Cluster routing confusion failures.

        Returns:
            Cluster info or None
        """
        routing_failures = [
            f for f in self.failures
            if f.get("category") == "ROUTING_ERROR"
        ]

        if not routing_failures:
            return None

        return {
            "cluster_id": "routing_confusion",
            "category": "ROUTING_ERROR",
            "count": len(routing_failures),
            "description": "Repeated routing confusion - user queries not matching expected intents",
            "examples": [f.get("query", "")[:100] for f in routing_failures[:3]],
            "recommendation": "Review router patterns and add missing intent definitions",
        }

    def _cluster_adapter_issues(self) -> Optional[dict]:
        """Cluster adapter/mapping issues.

        Returns:
            Cluster info or None
        """
        adapter_failures = [
            f for f in self.failures
            if f.get("category") in ["ADAPTER_ERROR", "DATA_MAPPING_ERROR"]
        ]

        if not adapter_failures:
            return None

        return {
            "cluster_id": "adapter_mapping",
            "category": "ADAPTER_ERROR / DATA_MAPPING_ERROR",
            "count": len(adapter_failures),
            "description": "Adapter or data mapping failures",
            "examples": [f.get("error_message", "")[:100] for f in adapter_failures[:3]],
            "recommendation": "Review adapter connection and data transformation logic",
        }

    def _cluster_missing_knowledge(self) -> Optional[dict]:
        """Cluster missing knowledge failures.

        Returns:
            Cluster info or None
        """
        knowledge_failures = [
            f for f in self.failures
            if f.get("category") == "MISSING_EVIDENCE"
        ]

        if not knowledge_failures:
            return None

        return {
            "cluster_id": "missing_knowledge",
            "category": "MISSING_EVIDENCE",
            "count": len(knowledge_failures),
            "description": "Missing data/knowledge for query",
            "examples": [f.get("error_message", "")[:100] for f in knowledge_failures[:3]],
            "recommendation": "Add data sources or clarify expected data availability",
        }

    def _cluster_llm_issues(self) -> Optional[dict]:
        """Cluster LLM schema issues.

        Returns:
            Cluster info or None
        """
        llm_failures = [
            f for f in self.failures
            if f.get("category") in ["LLM_SCHEMA_ERROR", "LLM_HALLUCINATION"]
        ]

        if not llm_failures:
            return None

        return {
            "cluster_id": "llm_schema",
            "category": "LLM_SCHEMA_ERROR / LLM_HALLUCINATION",
            "count": len(llm_failures),
            "description": "LLM schema validation or hallucination issues",
            "examples": [f.get("error_message", "")[:100] for f in llm_failures[:3]],
            "recommendation": "Add schema validation or use structured outputs",
        }

    def _cluster_empty_sprint(self) -> Optional[dict]:
        """Cluster empty sprint edge cases.

        Returns:
            Cluster info or None
        """
        empty_sprint = [
            f for f in self.failures
            if "empty" in f.get("error_message", "").lower()
            or "no data" in f.get("error_message", "").lower()
            or "sprint" in f.get("error_message", "").lower()
        ]

        if len(empty_sprint) < 2:
            return None

        return {
            "cluster_id": "empty_sprint",
            "category": "EDGE_CASE",
            "count": len(empty_sprint),
            "description": "Empty sprint or missing sprint data edge cases",
            "examples": [f.get("error_message", "")[:100] for f in empty_sprint[:3]],
            "recommendation": "Add handling for empty sprint scenarios",
        }

    def _cluster_entity_extraction(self) -> Optional[dict]:
        """Cluster entity extraction issues.

        Returns:
            Cluster info or None
        """
        entity_failures = [
            f for f in self.failures
            if f.get("category") == "ENTITY_EXTRACTION_ERROR"
        ]

        if not entity_failures:
            return None

        return {
            "cluster_id": "entity_extraction",
            "category": "ENTITY_EXTRACTION_ERROR",
            "count": len(entity_failures),
            "description": "Entity extraction failures",
            "examples": [f.get("error_message", "")[:100] for f in entity_failures[:3]],
            "recommendation": "Review entity extraction patterns",
        }
