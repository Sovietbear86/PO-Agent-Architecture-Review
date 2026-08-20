"""Live-source grounding extensions for production AS21 mode."""
from __future__ import annotations

import re
from typing import Any

from .dialogue_runtime import ClarificationNeed, SemanticFrame
from .entity_grounding import GroundedEntityResolver


class LiveGroundedEntityResolver(GroundedEntityResolver):
    """Resolve production entities from real Task API/SWTR source facts."""

    _PRODUCT_ALIASES = {
        "olp": "OLP",
        "olap": "OLP",
        "olap analytics": "OLP",
        "dms": "DMS",
        "datamarts": "DMS",
        "data marts": "DMS",
    }
    _CURRENT_MARKERS = ("current", "active", "текущ", "актуальн", "активн")
    _EXPLICIT_RELEASE_RE = re.compile(
        r"(?:релиз(?:а|е|у|ом)?|release)\s+([A-Za-z0-9][A-Za-z0-9_.-]{2,79})",
        re.I,
    )

    @classmethod
    def _normalize_product(cls, value: str | None) -> str | None:
        if not value:
            return None
        raw = value.strip()
        mapped = cls._PRODUCT_ALIASES.get(raw.casefold())
        return mapped or raw.upper()

    @classmethod
    def _explicit_product_from_query(cls, query: str) -> str | None:
        low = query.casefold()
        matches = {canonical for alias, canonical in cls._PRODUCT_ALIASES.items() if alias in low}
        return next(iter(matches)) if len(matches) == 1 else None

    @classmethod
    def _explicit_release_from_query(cls, query: str) -> str | None:
        match = cls._EXPLICIT_RELEASE_RE.search(query)
        return match.group(1).strip() if match else None

    @classmethod
    def _asks_current_sprint(cls, raw: str | None, query: str) -> bool:
        text = f"{raw or ''} {query}".casefold()
        mentions_sprint = "спринт" in text or "sprint" in text
        return mentions_sprint and any(marker in text for marker in cls._CURRENT_MARKERS)

    @staticmethod
    def _release_identifier(item: Any) -> str | None:
        if isinstance(item, str):
            value = item.strip()
            return value or None
        if isinstance(item, dict):
            for key in ("id", "code", "name", "value"):
                value = item.get(key)
                if isinstance(value, (str, int)) and str(value).strip():
                    return str(value).strip()
        return None

    async def semantic_context(self) -> dict[str, Any]:
        context = await super().semantic_context()
        search_versions = getattr(self.adapter, "search_versions", None)
        if callable(search_versions):
            versions = await search_versions()
            if isinstance(versions, dict):
                candidates = versions.get("content") or versions.get("items") or versions.get("versions") or []
            else:
                candidates = versions if isinstance(versions, list) else []
            merged = {str(value) for value in context.get("known_releases", []) if value}
            for item in candidates:
                release_id = self._release_identifier(item)
                if release_id:
                    merged.add(release_id)
            context["known_releases"] = sorted(merged)
        return context

    async def _ground_live_explicit_sprint(self, frame: SemanticFrame, original_query: str) -> SemanticFrame | None:
        """Validate and preserve a user-supplied full sprint ID using live SWTR.

        The cached task scan is not an authoritative sprint directory. If the
        precision layer extracted a full sprint ID, validate that exact ID via
        the live sprint endpoint. On success, ground all other entities normally
        while protecting the validated sprint selector from the base resolver's
        cached `known_sprints` set.
        """
        explicit = (frame.slots.get("sprint_id") or "").strip()
        if not explicit:
            return None
        validator = getattr(self.adapter, "sprint_exists", None)
        if not callable(validator):
            return None
        exists = await validator(explicit)
        if not exists:
            return SemanticFrame(
                canonical_query=frame.canonical_query,
                intent_hint=frame.intent_hint,
                slots={k: v for k, v in frame.slots.items() if k != "sprint_id"},
                clarifications=[
                    *[item for item in frame.clarifications if item.field != "sprint_id"],
                    ClarificationNeed("sprint_id", f"Не могу подтвердить спринт «{explicit}» по данным AS21. Какой спринт выбрать?"),
                ],
                confidence=frame.confidence,
                llm_used=frame.llm_used,
            )

        protected_slots = dict(frame.slots)
        protected_slots.pop("sprint_id", None)
        protected_frame = SemanticFrame(
            canonical_query=frame.canonical_query,
            intent_hint=frame.intent_hint,
            slots=protected_slots,
            clarifications=[item for item in frame.clarifications if item.field != "sprint_id"],
            confidence=frame.confidence,
            llm_used=frame.llm_used,
        )
        grounded = await super().ground(protected_frame, original_query)
        slots = dict(grounded.slots)
        slots["sprint_id"] = explicit
        slots.pop("sprint_raw", None)
        canonical = grounded.canonical_query.replace("{sprint_id}", explicit)
        return SemanticFrame(
            canonical_query=canonical,
            intent_hint=grounded.intent_hint,
            slots=slots,
            clarifications=[item for item in grounded.clarifications if item.field != "sprint_id"],
            confidence=grounded.confidence,
            llm_used=grounded.llm_used,
        )

    async def ground(self, frame: SemanticFrame, original_query: str) -> SemanticFrame:
        slots = dict(frame.slots)
        product = self._normalize_product(slots.get("product")) or self._explicit_product_from_query(original_query)
        if product:
            slots["product"] = product

        if not slots.get("release_id") and not slots.get("release_raw"):
            explicit_release = self._explicit_release_from_query(original_query)
            if explicit_release:
                slots["release_raw"] = explicit_release

        canonical_query = frame.canonical_query
        if slots.get("release_raw") and not slots.get("release_id") and "{release_id}" not in canonical_query:
            canonical_query = f"{canonical_query.rstrip()} {{release_id}}"

        frame = SemanticFrame(
            canonical_query=canonical_query,
            intent_hint=frame.intent_hint,
            slots=slots,
            clarifications=frame.clarifications,
            confidence=frame.confidence,
            llm_used=frame.llm_used,
        )

        live_explicit = await self._ground_live_explicit_sprint(frame, original_query)
        if live_explicit is not None:
            return live_explicit

        grounded = await super().ground(frame, original_query)

        current_raw = grounded.slots.get("sprint_raw") or frame.slots.get("sprint_raw")
        if not product or not self._asks_current_sprint(current_raw, original_query):
            return grounded

        resolver = getattr(self.adapter, "get_current_sprint_id", None)
        if not callable(resolver):
            return grounded

        sprint_id = await resolver(product)
        if not sprint_id:
            return grounded

        live_slots = dict(grounded.slots)
        live_slots["product"] = product
        live_slots["sprint_id"] = sprint_id
        live_slots.pop("sprint_raw", None)
        canonical = grounded.canonical_query.replace("{sprint_id}", sprint_id)
        clarifications = [item for item in grounded.clarifications if item.field != "sprint_id"]

        return SemanticFrame(
            canonical_query=canonical,
            intent_hint=grounded.intent_hint,
            slots=live_slots,
            clarifications=clarifications,
            confidence=grounded.confidence,
            llm_used=grounded.llm_used,
        )
