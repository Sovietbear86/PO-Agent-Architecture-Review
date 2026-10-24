"""Clarification Loop for PO Agent Platform v2.

Supports multi-step clarification interactions:
request -> NEEDS_CLARIFICATION -> user answer -> merge -> resolve -> execute

Features:
- Pending request storage with TTL
- Resume original request after answer
- No duplicate questions for same session
- Session memory integration

Usage:
    # Step 1: Initial request
    context = context_resolver.resolve(...)
    if context.needs_clarification:
        request = clarifier.needs_clarification(context)
        return ClarificationResponse.needs_clarification(...)

    # Step 2: User answer
    if session_memory.has("pending_request"):
        pending = session_memory.get("pending_request")
        # Merge answer with pending
        context = context_resolver.merge_answer(pending, answer)
        context = context_resolver.resolve(...)

    # Step 3: Execute
    if not context.needs_clarification:
        result = capability_executor.execute(context)
"""


import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from po_agent.memory.session_memory import SessionMemory
from po_agent.clarification.models import (
    ClarificationRequest,
    ClarificationResponse,
)


class ClarificationLoop:
    """Manages multi-step clarification interactions.

    Session Memory keys:
    - pending_request: {original_query, intent, missing_fields, clarification_id, created_at, expires_at}
    - clarification_state: {pending_clarification_id, current_question}
    """

    def __init__(
        self,
        session_memory: Optional[SessionMemory] = None,
        ttl_seconds: int = 3600,
    ):
        """Initialize clarification loop manager.

        Args:
            session_memory: Session memory for state persistence
            ttl_seconds: Pending request TTL in seconds
        """
        self.session_memory = session_memory or SessionMemory()
        self.ttl_seconds = ttl_seconds

    def start_clarification(
        self,
        clarification_request: ClarificationRequest,
    ) -> ClarificationResponse:
        """Start clarification and store pending request.

        Args:
            clarification_request: Clarification request

        Returns:
            ClarificationResponse
        """
        # Store pending request in session memory
        pending = {
            "original_query": clarification_request.original_query,
            "original_intent": clarification_request.original_intent,
            "missing_fields": clarification_request.missing_fields,
            "clarification_id": clarification_request.clarification_id,
            "created_at": clarification_request.created_at.isoformat(),
            "expires_at": clarification_request.expires_at.isoformat(),
            "options": [o.model_dump() for o in clarification_request.options],
        }

        self.session_memory.set("pending_request", pending)
        self.session_memory.set("clarification_state", {
            "pending_clarification_id": clarification_request.clarification_id,
            "current_question": clarification_request.question,
            "created_at": clarification_request.created_at.isoformat(),
        })

        return ClarificationResponse.needs_clarification(
            clarification_id=clarification_request.clarification_id,
            question=clarification_request.question,
            options=clarification_request.options,
            pending_request=pending,
        )

    def resume_request(
        self,
        answer: str,
        selected_option: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Resume pending request with user answer.

        Args:
            answer: User's text answer
            selected_option: If user clicked a button

        Returns:
            Merged request dict or None if no pending request
        """
        pending = self.session_memory.get("pending_request")
        if pending is None:
            return None

        # Check if expired
        created_at = datetime.fromisoformat(pending["created_at"])
        expires_at = datetime.fromisoformat(pending["expires_at"])
        if datetime.now() > expires_at:
            self.session_memory.delete("pending_request")
            self.session_memory.delete("clarification_state")
            return None

        # Merge answer with pending
        merged = {
            **pending,
            "answer": answer,
            "selected_option": selected_option,
            "merged_at": datetime.now().isoformat(),
        }

        # Update session memory
        self.session_memory.set("pending_request", merged)
        self.session_memory.delete("clarification_state")

        return merged

    def clear_pending(self) -> bool:
        """Clear pending clarification.

        Returns:
            True if pending was cleared
        """
        result = self.session_memory.delete("pending_request")
        self.session_memory.delete("clarification_state")
        return result

    def get_pending(self) -> Optional[Dict[str, Any]]:
        """Get current pending request.

        Returns:
            Pending request or None
        """
        pending = self.session_memory.get("pending_request")
        if pending is None:
            return None

        # Check if expired
        created_at = datetime.fromisoformat(pending["created_at"])
        expires_at = datetime.fromisoformat(pending["expires_at"])
        if datetime.now() > expires_at:
            self.clear_pending()
            return None

        return pending

    def has_pending(self) -> bool:
        """Check if there's a pending clarification.

        Returns:
            True if pending exists and not expired
        """
        pending = self.get_pending()
        if pending is None:
            return False

        # Check expiration
        created_at = datetime.fromisoformat(pending["created_at"])
        expires_at = datetime.fromisoformat(pending["expires_at"])
        return datetime.now() <= expires_at

    def cleanup_expired(self) -> int:
        """Clean up expired pending requests.

        Returns:
            Number of expired requests cleaned up
        """
        expired_count = 0
        # In real implementation, would scan all sessions
        # For now, just check current session
        pending = self.session_memory.get("pending_request")
        if pending is not None:
            # Check if expired
            created_at = datetime.fromisoformat(pending["created_at"])
            expires_at = datetime.fromisoformat(pending["expires_at"])
            if datetime.now() > expires_at:
                self.clear_pending()
                expired_count = 1
        return expired_count


# Export for convenience
__all__ = ["ClarificationLoop"]
