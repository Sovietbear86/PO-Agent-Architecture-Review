"""Failure Taxonomy for PO Agent Platform v2.

Create failure categories:

- ROUTING_ERROR
- ENTITY_EXTRACTION_ERROR
- ADAPTER_ERROR
- DATA_MAPPING_ERROR
- METRIC_ERROR
- MISSING_EVIDENCE
- LLM_SCHEMA_ERROR
- LLM_HALLUCINATION
- KNOWLEDGE_ERROR
- PROMPT_FAILURE
- CAPABILITY_ERROR
- UNKNOWN

Create classifier based on deterministic signals first.
Optional LLM-assisted categorization later.
"""

from enum import Enum
from typing import Optional


class FailureCategory(Enum):
    """Category of failure."""
    ROUTING_ERROR = "ROUTING_ERROR"
    ENTITY_EXTRACTION_ERROR = "ENTITY_EXTRACTION_ERROR"
    ADAPTER_ERROR = "ADAPTER_ERROR"
    DATA_MAPPING_ERROR = "DATA_MAPPING_ERROR"
    METRIC_ERROR = "METRIC_ERROR"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    LLM_SCHEMA_ERROR = "LLM_SCHEMA_ERROR"
    LLM_HALLUCINATION = "LLM_HALLUCINATION"
    KNOWLEDGE_ERROR = "KNOWLEDGE_ERROR"
    PROMPT_FAILURE = "PROMPT_FAILURE"
    CAPABILITY_ERROR = "CAPABILITY_ERROR"
    UNKNOWN = "UNKNOWN"


class FailureClassifier:
    """Classifier for failures based on deterministic signals."""

    def classify(
        self,
        error_message: str,
        intent: Optional[str],
        entities: list,
        capability: Optional[str],
    ) -> FailureCategory:
        """Classify failure based on signals.

        Args:
            error_message: Error message text
            intent: Classified intent (if any)
            entities: Extracted entities
            capability: Capability that failed (if any)

        Returns:
            Failure category
        """
        error_lower = error_message.lower()

        # Check for routing errors
        if "intent" in error_lower and "unknown" in error_lower:
            return FailureCategory.ROUTING_ERROR

        # Check for entity extraction errors
        if "entity" in error_lower or "extract" in error_lower:
            return FailureCategory.ENTITY_EXTRACTION_ERROR

        # Check for adapter errors
        if "adapter" in error_lower or "swtr" in error_lower or "as21" in error_lower:
            if "unavailable" in error_lower or "timeout" in error_lower or "connection" in error_lower:
                return FailureCategory.ADAPTER_ERROR

        # Check for LLM schema errors (must check before DATA_MAPPING)
        if "json" in error_lower and ("parse" in error_lower or "format" in error_lower):
            return FailureCategory.LLM_SCHEMA_ERROR

        # Check for data mapping errors
        if "mapping" in error_lower or "transform" in error_lower or "parse" in error_lower:
            return FailureCategory.DATA_MAPPING_ERROR

        # Check for metric errors
        if "metric" in error_lower or "calculate" in error_lower:
            return FailureCategory.METRIC_ERROR

        # Check for missing evidence
        if "evidence" in error_lower or "no data" in error_lower or "not found" in error_lower:
            return FailureCategory.MISSING_EVIDENCE

        # Check for LLM schema errors
        if "json" in error_lower and ("parse" in error_lower or "format" in error_lower):
            return FailureCategory.LLM_SCHEMA_ERROR

        # Check for LLM hallucination
        if "hallucinat" in error_lower or "invent" in error_lower or "false" in error_lower:
            return FailureCategory.LLM_HALLUCINATION

        # Check for knowledge errors
        if "knowledge" in error_lower or "unknown" in error_lower or "unknown intent" in error_lower:
            return FailureCategory.KNOWLEDGE_ERROR

        # Check for prompt failures
        if "prompt" in error_lower or "template" in error_lower:
            return FailureCategory.PROMPT_FAILURE

        # Check for capability errors
        if capability or "capability" in error_lower:
            return FailureCategory.CAPABILITY_ERROR

        # Default to unknown
        return FailureCategory.UNKNOWN

    def extract_failure_reason(
        self,
        error_message: str,
    ) -> str:
        """Extract failure reason from error message.

        Args:
            error_message: Error message text

        Returns:
            Cleaned failure reason
        """
        # Remove stack traces and technical details
        lines = error_message.split("\n")
        # Keep only first few lines or relevant parts
        return lines[0] if lines else error_message


class FailureStore:
    """Store for classified failures."""

    def __init__(self):
        """Initialize failure store."""
        self.failures: list[dict] = []

    def add_failure(
        self,
        trace_id: str,
        error_message: str,
        intent: Optional[str],
        entities: list,
        capability: Optional[str],
        category: Optional[FailureCategory] = None,
    ) -> dict:
        """Add a failure to the store.

        Args:
            trace_id: Source trace ID
            error_message: Error message
            intent: Classified intent
            entities: Extracted entities
            capability: Failed capability
            category: Pre-classified category (optional)

        Returns:
            Failure record
        """
        if category is None:
            classifier = FailureClassifier()
            category = classifier.classify(error_message, intent, entities, capability)

        record = {
            "trace_id": trace_id,
            "error_message": error_message,
            "intent": intent,
            "entities": entities,
            "capability": capability,
            "category": category.value,
            "category_enum": category,
            "reason": FailureClassifier().extract_failure_reason(error_message),
        }

        self.failures.append(record)
        return record

    def get_failures_by_category(
        self,
        category: FailureCategory,
    ) -> list[dict]:
        """Get failures by category.

        Args:
            category: Failure category

        Returns:
            List of failure records
        """
        return [
            f for f in self.failures
            if f["category"] == category.value
        ]

    def get_all_failures(self) -> list[dict]:
        """Get all failures.

        Returns:
            List of failure records
        """
        return self.failures.copy()

    def get_failure_counts(self) -> dict[str, int]:
        """Get failure counts by category.

        Returns:
            Dictionary of category -> count
        """
        counts: dict[str, int] = {}
        for failure in self.failures:
            category = failure["category"]
            counts[category] = counts.get(category, 0) + 1
        return counts

    def close(self) -> None:
        """Close database connection."""
        if hasattr(self, "_conn") and self._conn:
            self._conn.close()
        """Get failure counts by category.

        Returns:
            Dictionary of category -> count
        """
        counts: dict[str, int] = {}
        for failure in self.failures:
            category = failure["category"]
            counts[category] = counts.get(category, 0) + 1
        return counts
