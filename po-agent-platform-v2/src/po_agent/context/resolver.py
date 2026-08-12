"""Context Resolver for PO Agent Platform v2.

Resolves context from query, session memory, and entities.
Implements precedence policy:
current_request > clarification_answer > session_memory > 
deterministic_lookup > approved_curated_memory > default
"""

import re
from datetime import date
from typing import Optional, List, Dict, Any

from po_agent.domain.models import AttachmentType
from po_agent.memory.session_memory import SessionMemory
from po_agent.models.resolved_context import (
    ResolvedContext,
    ContextSource,
    ContextConflict,
)


class ContextResolver:
    """Resolve context from query, session, and entities.

    Implements precedence policy:
    1. current_request (explicit user input)
    2. clarification_answer (answer from clarification loop)
    3. session_memory (previous conversation state)
    4. deterministic_lookup (code-based lookup)
    5. approved_curated_memory (approved aliases)
    6. default (fallback value)
    """

    def __init__(
        self,
        session_memory: Optional[SessionMemory] = None,
        available_products: Optional[List[str]] = None,
        available_sprints: Optional[List[str]] = None,
    ):
        """Initialize context resolver.

        Args:
            session_memory: Session memory for state persistence
            available_products: List of available product IDs
            available_sprints: List of available sprint IDs
        """
        self.session_memory = session_memory or SessionMemory()
        self.available_products = available_products or []
        self.available_sprints = available_sprints or []

    async def resolve(
        self,
        query: str,
        entities: List[Dict[str, Any]],
        intents: List[str],
        session_id: Optional[str] = None,
    ) -> ResolvedContext:
        """Resolve context from query and entities.

        Args:
            query: User query
            entities: Extracted entities
            intents: Classified intents
            session_id: Session ID for tracking

        Returns:
            ResolvedContext with all fields resolved
        """
        context = ResolvedContext(query=query, session_id=session_id)

        # Step 1: Extract from query (highest priority)
        self._extract_from_query(context, query, entities)

        # Step 2: Fall back to session memory
        self._extract_from_session_memory(context)

        # Step 3: Fall back to deterministic lookup
        self._extract_from_deterministic_lookup(context)

        # Step 5: Check for missing/ambiguous fields
        self._validate_context(context, intents)

        return context

    def _extract_from_query(
        self,
        context: ResolvedContext,
        query: str,
        entities: List[Dict[str, Any]],
    ) -> None:
        """Extract context from query entities (highest priority)."""
        query_lower = query.lower()

        for entity in entities:
            entity_type = entity.get("type", "")
            entity_value = entity.get("value", "")

            if entity_type == "product":
                context.set_value("product", entity_value, ContextSource.CURRENT_REQUEST)

            elif entity_type == "sprint":
                # Normalize "current_sprint" placeholder
                if entity_value == "current_sprint":
                    context.set_value("sprint_id", "current_sprint", ContextSource.CURRENT_REQUEST)
                else:
                    context.set_value("sprint_id", entity_value, ContextSource.CURRENT_REQUEST)

            elif entity_type == "release":
                context.set_value("release_id", entity_value, ContextSource.CURRENT_REQUEST)

            elif entity_type == "task_key":
                context.set_value("task_id", entity_value, ContextSource.CURRENT_REQUEST)

            elif entity_type == "member":
                # Try to normalize member login
                normalized = self._normalize_member(entity_value)
                if normalized:
                    context.set_value("member_login", normalized, ContextSource.CURRENT_REQUEST)

            elif entity_type == "date":
                # Handle date range
                if entity_value.startswith("period:"):
                    period = entity_value.replace("period:", "")
                    start, end = self._parse_date_period(period)
                    context.set_value("date_range_start", start, ContextSource.CURRENT_REQUEST)
                    context.set_value("date_range_end", end, ContextSource.CURRENT_REQUEST)

        # Extract attachment type from query
        attachment_type = self._extract_attachment_type(query_lower)
        if attachment_type:
            context.set_value("attachment_type", attachment_type, ContextSource.CURRENT_REQUEST)

    def _extract_from_session_memory(self, context: ResolvedContext) -> None:
        """Extract context from session memory (lower priority)."""
        # Product
        if context.product is None:
            product = self.session_memory.get("current_product")
            if product:
                context.set_value("product", product, ContextSource.SESSION_MEMORY)

        # Sprint
        if context.sprint_id is None:
            sprint = self.session_memory.get("current_sprint")
            if sprint:
                context.set_value("sprint_id", sprint, ContextSource.SESSION_MEMORY)
        
        # Handle "current_sprint" special value - look up from available sprints
        if context.sprint_id == "current_sprint" and self.available_sprints:
            # Use the most recent sprint from available sprints
            # In real implementation, would need actual sprint dates
            context.set_value("sprint_id", self.available_sprints[0], ContextSource.DETERMINISTIC_LOOKUP)

        # Member
        if context.member_login is None:
            member = self.session_memory.get("selected_member")
            if member:
                context.set_value("member_login", member, ContextSource.SESSION_MEMORY)

        # Release
        if context.release_id is None:
            release = self.session_memory.get("current_release")
            if release:
                context.set_value("release_id", release, ContextSource.SESSION_MEMORY)

    def _extract_from_deterministic_lookup(self, context: ResolvedContext) -> None:
        """Extract context from deterministic lookup (lower priority)."""
        # If only one product available, use it
        if context.product is None and len(self.available_products) == 1:
            context.set_value("product", self.available_products[0], ContextSource.DETERMINISTIC_LOOKUP)

        # If only one sprint available, use it
        if context.sprint_id is None and len(self.available_sprints) == 1:
            context.set_value("sprint_id", self.available_sprints[0], ContextSource.DETERMINISTIC_LOOKUP)

    def _validate_context(self, context: ResolvedContext, intents: List[str]) -> None:
        """Validate context and mark missing/ambiguous fields."""
        # Define required fields per intent
        # For task_search: either member_login OR sprint_id (not both required)
        # If sprint_id is present, can show all sprint tasks
        # If member_login is present, can show tasks for that member across all sprints
        required_by_intent = {
            "task_search": [],  # No required fields - either sprint_id or member_login works
            "sprint_health": ["sprint_id"],
            "velocity": ["product", "member_login"],
            "team_workload": ["product", "member_login"],
            "release_health": ["release_id"],
            "task_summary": ["task_id"],
            "competency_match": ["task_id", "member_login"],
            "help": [],
        }

        required_fields = []
        for intent in intents:
            required_fields.extend(required_by_intent.get(intent, []))

        # Check for missing fields
        for field in required_fields:
            value, _ = context.get_value(field)
            if value is None:
                context.mark_missing(field)

        # Set needs_clarification if missing required fields
        if context.missing_fields:
            context.needs_clarification = True
            context.confidence = 0.0
        elif context.ambiguous_fields:
            context.needs_clarification = True
            context.confidence = 0.5
        else:
            context.confidence = 0.9

    def _normalize_member(self, value: str) -> Optional[str]:
        """Normalize member value to login format."""
        # If value already matches login format (A.A.A), return as is
        login_pattern = r"^[A-Z]+\.[A-Z]+\.[A-Z]+$"
        if re.match(login_pattern, value):
            return value

        # For Cyrillic surnames or plain names, just return as-is
        # In real implementation, would use team config for transliteration
        return value

    def _extract_attachment_type(self, query_lower: str) -> Optional[AttachmentType]:
        """Extract attachment type from query."""
        type_map = {
            "excel": AttachmentType.EXCEL,
            "spreadsheet": AttachmentType.EXCEL,
            "xls": AttachmentType.EXCEL,
            "word": AttachmentType.WORD,
            "doc": AttachmentType.WORD,
            "pdf": AttachmentType.PDF,
            "msg": AttachmentType.MSG,
            "email": AttachmentType.MSG,
            "image": AttachmentType.IMAGE,
            "photo": AttachmentType.IMAGE,
            "png": AttachmentType.IMAGE,
            "jpg": AttachmentType.IMAGE,
            "jpeg": AttachmentType.IMAGE,
        }

        for keyword, att_type in type_map.items():
            if keyword in query_lower:
                return att_type

        return None

    def _parse_date_period(self, period: str) -> tuple[Optional[date], Optional[date]]:
        """Parse date period string."""
        # Simple implementation - can be enhanced
        # Expected format: "last 30 days", "2024-01-01 to 2024-02-01", etc.
        return None, None


# Export for convenience
__all__ = ["ContextResolver", "ContextSource"]
