"""Narrow deterministic normalization for high-precision Core-8 utterances.

This wrapper never invents source identifiers. It only corrects an already
supported semantic operation when the original wording explicitly names a
Core-8 operation and preserves raw/current source slots for normal grounding.
"""
from __future__ import annotations

from typing import Any

from .dialogue_runtime import SemanticFrame, SemanticInterpreter


class Core8SemanticPrecisionInterpreter:
    """Protect explicit Core-8 operation wording from provider misclassification."""

    _CURRENT = ("текущ", "актуальн", "current", "active")
    _SPRINT = ("спринт", "sprint")
    _HEALTH = ("здоров", "готовност", "health", "readiness")
    _VELOCITY = ("velocity", "велосит", "скорост", "производительност")

    def __init__(self, delegate: SemanticInterpreter) -> None:
        self.delegate = delegate

    @staticmethod
    def _contains(text: str, markers: tuple[str, ...]) -> bool:
        return any(marker in text for marker in markers)

    @staticmethod
    def _product(query: str) -> str | None:
        low = query.casefold()
        if "olap" in low or " olp" in f" {low}":
            return "OLP"
        if "datamarts" in low or "data marts" in low or " dms" in f" {low}":
            return "DMS"
        return None

    async def interpret(self, query: str, *, context: dict[str, Any] | None = None) -> SemanticFrame:
        frame = await self.delegate.interpret(query, context=context)
        low = query.casefold()
        mentions_sprint = self._contains(low, self._SPRINT)
        asks_current = mentions_sprint and self._contains(low, self._CURRENT)
        slots = dict(frame.slots)
        intent = frame.intent_hint

        # Operation words are more specific than generic "show current sprint".
        # This fixes provider outputs such as sprint_current for explicit health
        # or velocity requests without bypassing catalog/source validation.
        if mentions_sprint and self._contains(low, self._HEALTH):
            intent = "sprint_health"
        elif mentions_sprint and self._contains(low, self._VELOCITY):
            intent = "sprint_velocity"
        elif asks_current and self._contains(low, ("какой", "what")):
            intent = "sprint_current"

        product = self._product(query)
        if product:
            slots["product"] = product
        if asks_current:
            slots["sprint_raw"] = "current"

        # A live current-sprint resolver owns this slot. Remove only a premature
        # sprint_id clarification; all other ambiguity remains fail-closed.
        clarifications = list(frame.clarifications)
        if asks_current and product:
            clarifications = [item for item in clarifications if item.field != "sprint_id"]

        return SemanticFrame(
            canonical_query=frame.canonical_query,
            intent_hint=intent,
            slots=slots,
            clarifications=clarifications,
            confidence=frame.confidence,
            llm_used=frame.llm_used,
        )
