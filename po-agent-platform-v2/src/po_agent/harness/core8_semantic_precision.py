"""Narrow deterministic normalization for high-precision Core-8 utterances.

This wrapper never invents source identifiers. It only corrects an already
supported semantic operation when the original wording explicitly names a
Core-8 operation and preserves raw/current source slots for normal grounding.
"""
from __future__ import annotations

import re
from typing import Any

from .dialogue_runtime import ClarificationNeed, SemanticFrame, SemanticInterpreter


class Core8SemanticPrecisionInterpreter:
    """Protect explicit Core-8 operation wording from provider misclassification."""

    _CURRENT = ("текущ", "актуальн", "current", "active")
    _SPRINT = ("спринт", "sprint")
    _HEALTH = ("здоров", "готовност", "health", "readiness")
    _VELOCITY = ("velocity", "велосит", "скорост", "производительност")
    _SPRINT_ID_RE = re.compile(r"\b[A-ZА-Я][A-ZА-Я0-9_]{1,15}-SPRNT-\d+\b", re.I)

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

    @classmethod
    def _contradictory_sprint_filters(cls, query: str) -> tuple[str, ...]:
        """Return explicit contradictory sprint selectors from one utterance.

        A relative current/active sprint plus a concrete sprint ID is
        contradictory unless the user explicitly resolves the relationship in a
        later turn. Two different explicit sprint IDs are contradictory as well.
        We fail closed before execution rather than silently choosing one filter.
        """
        explicit = tuple(dict.fromkeys(match.group(0).upper() for match in cls._SPRINT_ID_RE.finditer(query)))
        low = query.casefold()
        relative_current = cls._contains(low, cls._SPRINT) and cls._contains(low, cls._CURRENT)
        if len(explicit) > 1:
            return explicit
        if explicit and relative_current:
            return ("current", *explicit)
        return ()

    async def interpret(self, query: str, *, context: dict[str, Any] | None = None) -> SemanticFrame:
        frame = await self.delegate.interpret(query, context=context)
        low = query.casefold()
        mentions_sprint = self._contains(low, self._SPRINT)
        asks_current = mentions_sprint and self._contains(low, self._CURRENT)
        slots = dict(frame.slots)
        intent = frame.intent_hint

        contradictions = self._contradictory_sprint_filters(query)
        if contradictions:
            # Preserve the selected operation but make execution impossible until
            # the user chooses one source selector. Do not allow the LLM or the
            # live current-sprint resolver to silently discard either constraint.
            slots.pop("sprint_id", None)
            slots.pop("sprint_raw", None)
            other = [item for item in frame.clarifications if item.field != "sprint_id"]
            other.append(ClarificationNeed(
                "sprint_id",
                "В запросе указаны несовместимые фильтры спринта. Какой один спринт использовать?",
                contradictions,
            ))
            return SemanticFrame(
                canonical_query=frame.canonical_query,
                intent_hint=intent,
                slots=slots,
                clarifications=other,
                confidence=frame.confidence,
                llm_used=frame.llm_used,
            )

        # Operation words are more specific than generic "show current sprint".
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
