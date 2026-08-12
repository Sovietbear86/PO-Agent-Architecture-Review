"""Clarification Engine for PO Agent Platform v2.

Generates clarification questions when context is missing or ambiguous.

Behavior:
- If required context missing: return NEEDS_CLARIFICATION with question
- If ambiguous context: return NEEDS_CLARIFICATION with options
- If safe default exists: use default, no clarification needed
- If value in session memory: use session value, no clarification needed

Options generation:
- Code-based (products list, sprints list) - PREFERRED
- Default values - SECONDARY
- LLM-generated - NOT USED (to prevent hallucination)

Example questions:
- "По какому продукту показать velocity — OLP или DataMarts?"
- "Какой спринт интересует — DMS-SPRNT-1 или OLP-SPRNT-3?"
"""

from typing import Optional, List, Dict, Any

from po_agent.context.resolver import ContextResolver
from po_agent.models.resolved_context import ResolvedContext, ContextSource
from po_agent.memory.session_memory import SessionMemory
from po_agent.clarification.models import (
    ClarificationRequest,
    ClarificationOption,
    ClarificationResponse,
    ClarificationStatus,
)


class ClarificationEngine:
    """Engine for generating clarification questions.

    Rules:
    - Ask only when necessary (missing required fields, ambiguous values)
    - Provide code-based options when possible
    - Never use LLM for option generation
    - Skip clarification if safe default exists or value in session memory
    """

    def __init__(
        self,
        session_memory: Optional[SessionMemory] = None,
        available_products: Optional[List[str]] = None,
        available_sprints: Optional[List[str]] = None,
    ):
        """Initialize clarification engine.

        Args:
            session_memory: Session memory for existing values
            available_products: List of available product IDs
            available_sprints: List of available sprint IDs
        """
        self.session_memory = session_memory or SessionMemory()
        self.available_products = available_products or []
        self.available_sprints = available_sprints or []

    def needs_clarification(
        self,
        context: ResolvedContext,
        required_fields: List[str],
    ) -> Optional[ClarificationRequest]:
        """Determine if clarification is needed and generate request.

        Args:
            context: Current resolved context
            required_fields: List of required field names

        Returns:
            ClarificationRequest if needed, None otherwise
        """
        # If context has all required fields, no clarification needed
        if not context.needs_clarification:
            return None

        # Get first missing/ambiguous field
        missing_field = self._get_priority_missing_field(context, required_fields)
        if missing_field is None:
            return None

        # Check if value exists in session memory (no clarification needed)
        if self._has_session_value(missing_field):
            return None

        # Generate question
        question = self._generate_question(missing_field)

        # Generate options if available
        options = self._generate_options(missing_field)

        return ClarificationRequest(
            reason=f"Missing field: {missing_field}",
            missing_fields=[missing_field],
            question=question,
            options=options,
            original_intent=context.to_dict().get("intent"),
            original_query=context.query or "",
        )

    def _get_priority_missing_field(
        self,
        context: ResolvedContext,
        required_fields: List[str],
    ) -> Optional[str]:
        """Get highest priority missing field.

        Args:
            context: Resolved context
            required_fields: Required fields

        Returns:
            Field name or None
        """
        # Check ambiguous fields first (higher priority)
        for field in context.ambiguous_fields:
            if field in required_fields:
                return field

        # Then check missing fields
        for field in context.missing_fields:
            if field in required_fields:
                return field

        return None

    def _has_session_value(self, field: str) -> bool:
        """Check if field has value in session memory.

        Args:
            field: Field name

        Returns:
            True if session has value
        """
        session_values = {
            "product": self.session_memory.get("current_product"),
            "sprint_id": self.session_memory.get("current_sprint"),
            "member_login": self.session_memory.get("selected_member"),
            "release_id": self.session_memory.get("current_release"),
        }
        return session_values.get(field) is not None

    def _generate_question(self, field: str) -> str:
        """Generate question for missing field.

        Args:
            field: Missing field name

        Returns:
            Question string
        """
        questions = {
            "product": "По какому продукту показать результаты?",
            "sprint_id": "Какой спринт интересует?",
            "member_login": "Какой участник команды?",
            "release_id": "Какой релиз интересует?",
            "task_id": "Какая задача интересует?",
            "date_range": "За какой период?",
            "attachment_type": "Какой тип вложения?",
        }
        return questions.get(field, f"Укажите значение для {field}")

    def _generate_options(self, field: str) -> List[ClarificationOption]:
        """Generate deterministic options for missing field.

        Args:
            field: Missing field name

        Returns:
            List of options
        """
        if field == "product" and self.available_products:
            return [
                ClarificationOption(
                    label=product,
                    value=product,
                )
                for product in self.available_products
            ]

        if field == "sprint_id" and self.available_sprints:
            return [
                ClarificationOption(
                    label=sprint,
                    value=sprint,
                )
                for sprint in self.available_sprints
            ]

        # Default options based on field
        defaults = {
            "product": [
                ClarificationOption(label="WMB", value="WMB"),
                ClarificationOption(label="OLP", value="OLP"),
            ],
            "sprint_id": [
                ClarificationOption(label="DMS-SPRNT-1", value="DMS-SPRNT-1"),
                ClarificationOption(label="OLP-SPRNT-1", value="OLP-SPRNT-1"),
            ],
        }
        return defaults.get(field, [])

    def process_answer(
        self,
        request: ClarificationRequest,
        answer: str,
        selected_option: Optional[str] = None,
    ) -> ClarificationResponse:
        """Process clarification answer.

        Args:
            request: Original clarification request
            answer: User's text answer
            selected_option: If user clicked a button

        Returns:
            ClarificationResponse
        """
        # If option selected, use it
        if selected_option:
            return ClarificationResponse.completed(
                resolution={
                    "field": request.missing_fields[0] if request.missing_fields else "unknown",
                    "value": selected_option,
                    "source": "clarification_answer",
                }
            )

        # Otherwise, use text answer
        return ClarificationResponse.completed(
            resolution={
                "field": request.missing_fields[0] if request.missing_fields else "unknown",
                "value": answer,
                "source": "clarification_answer",
            }
        )


# Export for convenience
__all__ = ["ClarificationEngine"]
