"""Live-source grounding extensions for production AS21 mode."""
from __future__ import annotations

from .dialogue_runtime import SemanticFrame
from .entity_grounding import GroundedEntityResolver


class LiveGroundedEntityResolver(GroundedEntityResolver):
    """Resolve explicit product aliases and relative current sprint from real SWTR.

    Generic entities are validated by the base grounder first. A relative
    "current sprint" is then resolved by the dedicated live source endpoint and
    is therefore not revalidated against the task-derived known_sprints list,
    which may be incomplete or lag the live sprint endpoint.
    """

    _PRODUCT_ALIASES = {
        "olp": "OLP",
        "olap": "OLP",
        "olap analytics": "OLP",
        "dms": "DMS",
        "datamarts": "DMS",
        "data marts": "DMS",
    }
    _CURRENT_MARKERS = ("current", "active", "текущ", "актуальн", "активн")

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
        for alias, canonical in sorted(cls._PRODUCT_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
            if alias in low:
                return canonical
        return None

    @classmethod
    def _asks_current_sprint(cls, raw: str | None, query: str) -> bool:
        text = f"{raw or ''} {query}".casefold()
        mentions_sprint = "спринт" in text or "sprint" in text
        return mentions_sprint and any(marker in text for marker in cls._CURRENT_MARKERS)

    async def ground(self, frame: SemanticFrame, original_query: str) -> SemanticFrame:
        slots = dict(frame.slots)
        product = self._normalize_product(slots.get("product")) or self._explicit_product_from_query(original_query)
        if product:
            slots["product"] = product
        frame = SemanticFrame(
            canonical_query=frame.canonical_query,
            intent_hint=frame.intent_hint,
            slots=slots,
            clarifications=frame.clarifications,
            confidence=frame.confidence,
            llm_used=frame.llm_used,
        )

        # First validate people/status/explicit sprint/release identifiers using
        # the ordinary canonical contract.
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
