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
from po_agent.models.resolved_context import ResolvedContext, ContextSource, ContextConflict


class ContextResolver:
    def __init__(self, session_memory: Optional[SessionMemory] = None, available_products: Optional[List[str]] = None, available_sprints: Optional[List[str]] = None):
        self.session_memory = session_memory or SessionMemory()
        self.available_products = available_products or []
        self.available_sprints = available_sprints or []

    async def resolve(self, query: str, entities: List[Dict[str, Any]], intents: List[str], session_id: Optional[str] = None) -> ResolvedContext:
        context = ResolvedContext(query=query, session_id=session_id)
        self._extract_from_query(context, query, entities)
        self._extract_from_session_memory(context)
        self._extract_from_deterministic_lookup(context)
        self._validate_context(context, intents)
        return context

    def _extract_from_query(self, context: ResolvedContext, query: str, entities: List[Dict[str, Any]]) -> None:
        query_lower = query.lower()
        for entity in entities:
            entity_type = entity.get("type", "")
            entity_value = entity.get("value", "")
            if entity_type == "product": context.set_value("product", entity_value, ContextSource.CURRENT_REQUEST)
            elif entity_type == "sprint": context.set_value("sprint_id", "current_sprint" if entity_value == "current_sprint" else entity_value, ContextSource.CURRENT_REQUEST)
            elif entity_type == "release": context.set_value("release_id", entity_value, ContextSource.CURRENT_REQUEST)
            elif entity_type == "task_key": context.set_value("task_id", entity_value, ContextSource.CURRENT_REQUEST)
            elif entity_type == "member":
                normalized = self._normalize_member(entity_value)
                if normalized: context.set_value("member_login", normalized, ContextSource.CURRENT_REQUEST)
            elif entity_type == "date" and entity_value.startswith("period:"):
                start, end = self._parse_date_period(entity_value.replace("period:", ""))
                context.set_value("date_range_start", start, ContextSource.CURRENT_REQUEST)
                context.set_value("date_range_end", end, ContextSource.CURRENT_REQUEST)
        attachment_type = self._extract_attachment_type(query_lower)
        if attachment_type: context.set_value("attachment_type", attachment_type, ContextSource.CURRENT_REQUEST)

    def _extract_from_session_memory(self, context: ResolvedContext) -> None:
        if context.product is None:
            product = self.session_memory.get("current_product")
            if product: context.set_value("product", product, ContextSource.SESSION_MEMORY)
        if context.sprint_id is None:
            sprint = self.session_memory.get("current_sprint")
            if sprint: context.set_value("sprint_id", sprint, ContextSource.SESSION_MEMORY)
        if context.sprint_id == "current_sprint" and self.available_sprints:
            context.set_value("sprint_id", self.available_sprints[0], ContextSource.DETERMINISTIC_LOOKUP)
        if context.member_login is None:
            member = self.session_memory.get("selected_member")
            if member: context.set_value("member_login", member, ContextSource.SESSION_MEMORY)
        if context.release_id is None:
            release = self.session_memory.get("current_release")
            if release: context.set_value("release_id", release, ContextSource.SESSION_MEMORY)

    def _extract_from_deterministic_lookup(self, context: ResolvedContext) -> None:
        if context.product is None and len(self.available_products) == 1:
            context.set_value("product", self.available_products[0], ContextSource.DETERMINISTIC_LOOKUP)
        if context.sprint_id is None and len(self.available_sprints) == 1:
            context.set_value("sprint_id", self.available_sprints[0], ContextSource.DETERMINISTIC_LOOKUP)

    def _validate_context(self, context: ResolvedContext, intents: List[str]) -> None:
        required_by_intent = {
            "task_search": ["sprint_id", "member_login"],
            "sprint_health": ["sprint_id"],
            "velocity": ["product", "member_login"],
            "team_workload": ["product", "member_login"],
            "release_health": ["release_id"],
            "task_summary": ["task_id"],
            "competency_match": ["task_id", "member_login"],
            "help": [],
        }
        required_fields: list[str] = []
        for intent in intents:
            required_fields.extend(required_by_intent.get(intent, []))
        for field in required_fields:
            value, _ = context.get_value(field)
            if value is None: context.mark_missing(field)
        if context.missing_fields:
            context.needs_clarification = True; context.confidence = 0.0
        elif context.ambiguous_fields:
            context.needs_clarification = True; context.confidence = 0.5
        else:
            context.confidence = 0.9

    def _normalize_member(self, value: str) -> Optional[str]:
        return value

    def _extract_attachment_type(self, query_lower: str) -> Optional[AttachmentType]:
        type_map = {"excel": AttachmentType.EXCEL,"spreadsheet": AttachmentType.EXCEL,"xls": AttachmentType.EXCEL,"word": AttachmentType.WORD,"doc": AttachmentType.WORD,"pdf": AttachmentType.PDF,"msg": AttachmentType.MSG,"email": AttachmentType.MSG,"image": AttachmentType.IMAGE,"photo": AttachmentType.IMAGE,"png": AttachmentType.IMAGE,"jpg": AttachmentType.IMAGE,"jpeg": AttachmentType.IMAGE}
        for keyword, att_type in type_map.items():
            if keyword in query_lower: return att_type
        return None

    def _parse_date_period(self, period: str) -> tuple[Optional[date], Optional[date]]:
        return None, None

__all__ = ["ContextResolver", "ContextSource"]
