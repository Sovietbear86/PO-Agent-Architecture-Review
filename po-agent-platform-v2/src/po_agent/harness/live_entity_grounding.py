"""Live-source grounding extensions for production AS21 mode."""
from __future__ import annotations

from .dialogue_runtime import SemanticFrame
from .entity_grounding import GroundedEntityResolver


class LiveGroundedEntityResolver(GroundedEntityResolver):
    """Resolve explicit product aliases and 'current sprint' from real SWTR.

    The base grounder validates entities against canonical source-backed lists.
    This subclass only adds source-backed resolution for relative sprint wording;
    it does not invent sprint IDs or broaden user predicates.
    """

    _PRODUCT_ALIASES = {
        "olp": "OLP",
        "olap": "OLP",
        "olap analytics": "OLP",
        "dms": "DMS",
        "datamarts": "DMS",
        "data marts": "DMS",
    }
    _CURRENT_MARKERS = (
        "current",
        "active",
        "текущ",
        "актуальн",
        "активн",
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

        sprint_raw = slots.get("sprint_raw")
        if not slots.get("sprint_id") and product and self._asks_current_sprint(sprint_raw, original_query):
            resolver = getattr(self.adapter, "get_current_sprint_id", None)
            if callable(resolver):
                sprint_id = await resolver(product)
                if sprint_id:
                    slots["sprint_id"] = sprint_id
                    slots.pop("sprint_raw", None)
                    canonical = frame.canonical_query.replace("{sprint_id}", sprint_id)
                    frame = SemanticFrame(
                        canonical_query=canonical,
                        intent_hint=frame.intent_hint,
                        slots=slots,
                        clarifications=[item for item in frame.clarifications if item.field != "sprint_id"],
                        confidence=frame.confidence,
                        llm_used=frame.llm_used,
                    )
                else:
                    frame = SemanticFrame(
                        canonical_query=frame.canonical_query,
                        intent_hint=frame.intent_hint,
                        slots=slots,
                        clarifications=frame.clarifications,
                        confidence=frame.confidence,
                        llm_used=frame.llm_used,
                    )
            else:
                frame = SemanticFrame(
                    canonical_query=frame.canonical_query,
                    intent_hint=frame.intent_hint,
                    slots=slots,
                    clarifications=frame.clarifications,
                    confidence=frame.confidence,
                    llm_used=frame.llm_used,
                )
        elif slots != frame.slots:
            frame = SemanticFrame(
                canonical_query=frame.canonical_query,
                intent_hint=frame.intent_hint,
                slots=slots,
                clarifications=frame.clarifications,
                confidence=frame.confidence,
                llm_used=frame.llm_used,
            )

        return await super().ground(frame, original_query)
