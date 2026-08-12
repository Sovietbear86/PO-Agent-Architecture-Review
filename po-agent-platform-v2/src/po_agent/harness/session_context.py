"""Bounded short-lived session context for Harness follow-up requests.

This is intentionally not operational history and not curated memory. It stores
only explicit entity references needed to resolve local conversational follow-ups.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from .contracts import HarnessRequest, HarnessResponse, ResponseStatus


TASK_RE = re.compile(r"\b[A-ZА-Я][A-ZА-Я0-9_]{1,15}-\d+(?![-A-ZА-Я0-9_])\b", re.I)
SPRINT_RE = re.compile(r"\b[A-Z]+-SPRNT-\d+\b", re.I)
RELEASE_RE = re.compile(r"\b[A-Z]+-\d{4}-Q\d+\b", re.I)
PRODUCT_RE = re.compile(r"(?:продукт|продукте|пространств(?:о|е))\s+([A-Za-zА-Яа-я0-9_-]+)", re.I)
FOLLOW_UP_MARKERS = (
    "там", "ней", "нем", "нём", "этой", "этом", "этого", "его", "ее", "её",
    "а что", "а какие", "а как", "что с", "как там", "по нему", "по ней",
)
DOMAIN_FOLLOW_UP = (
    "риск", "блокер", "прогресс", "готовност", "состав", "задач", "статус",
    "velocity", "скорост", "wip", "cycle time", "lead time",
)


@dataclass
class SessionContext:
    current_task: str | None = None
    current_sprint: str | None = None
    current_release: str | None = None
    current_product: str | None = None
    clarification: dict[str, object] | None = None
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SessionContextStore:
    """In-memory TTL session state. Nothing is promoted permanently."""

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self.ttl = timedelta(seconds=ttl_seconds)
        self._items: dict[str, SessionContext] = {}

    def get(self, session_id: str) -> SessionContext:
        now = datetime.now(timezone.utc)
        item = self._items.get(session_id)
        if item is None or now - item.updated_at > self.ttl:
            item = SessionContext()
            self._items[session_id] = item
        return item

    def clear(self, session_id: str) -> None:
        self._items.pop(session_id, None)

    def snapshot(self, session_id: str) -> SessionContext:
        item = self.get(session_id)
        return SessionContext(
            current_task=item.current_task,
            current_sprint=item.current_sprint,
            current_release=item.current_release,
            current_product=item.current_product,
            clarification=dict(item.clarification) if item.clarification else None,
            updated_at=item.updated_at,
        )

    def resolve(self, request: HarnessRequest) -> HarnessRequest:
        """Resolve only clearly referential follow-ups; never inject history wholesale."""
        if not request.session_id:
            return request
        query = request.query.strip()
        if not query or TASK_RE.search(query) or SPRINT_RE.search(query) or RELEASE_RE.search(query) or PRODUCT_RE.search(query):
            return request
        low = query.casefold()
        if not any(marker in low for marker in FOLLOW_UP_MARKERS + DOMAIN_FOLLOW_UP):
            return request

        ctx = self.get(request.session_id)
        entity: str | None = None
        # Domain words disambiguate the preferred entity class.
        if any(token in low for token in ("релиз", "риск", "блокер", "прогресс", "готовност")) and ctx.current_release:
            entity = ctx.current_release
        elif any(token in low for token in ("спринт", "velocity", "скорост", "wip", "cycle time", "lead time")) and ctx.current_sprint:
            entity = ctx.current_sprint
        elif ctx.current_task:
            entity = ctx.current_task
        elif ctx.current_release:
            entity = ctx.current_release
        elif ctx.current_sprint:
            entity = ctx.current_sprint

        if not entity:
            return request
        return HarnessRequest(query=f"{query} {entity}", session_id=request.session_id)

    def observe(self, original: HarnessRequest, effective: HarnessRequest, response: HarnessResponse) -> None:
        if not original.session_id or response.status is ResponseStatus.FAILED:
            return
        ctx = self.get(original.session_id)
        text = effective.query
        task = TASK_RE.search(text)
        sprint = SPRINT_RE.search(text)
        release = RELEASE_RE.search(text)
        product = PRODUCT_RE.search(text)

        if task:
            ctx.current_task = task.group(0).upper()
        if sprint:
            ctx.current_sprint = sprint.group(0).upper()
        if release:
            ctx.current_release = release.group(0).upper()
        if product:
            ctx.current_product = product.group(1).upper()

        data = response.data if isinstance(response.data, dict) else {}
        if isinstance(data.get("task"), dict) and data["task"].get("key"):
            ctx.current_task = str(data["task"]["key"]).upper()
        if data.get("sprint_id"):
            ctx.current_sprint = str(data["sprint_id"]).upper()
        if data.get("release_id"):
            ctx.current_release = str(data["release_id"]).upper()
        filters = data.get("filters") if isinstance(data.get("filters"), dict) else {}
        if filters.get("product"):
            ctx.current_product = str(filters["product"]).upper()

        if response.status is ResponseStatus.NEEDS_CLARIFICATION:
            ctx.clarification = {
                "clarification_id": response.clarification_id,
                "question": response.question,
                "options": list(response.options),
            }
        elif response.status is ResponseStatus.COMPLETED:
            ctx.clarification = None
        ctx.updated_at = datetime.now(timezone.utc)
