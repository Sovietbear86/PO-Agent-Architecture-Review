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
    _PRODUCT_MARKERS = {
        "OLP": (r"\bolp\b", r"\bolap\b", r"\bolap analytics\b"),
        "DMS": (r"\bdms\b", r"\bdatamarts\b", r"\bdata marts\b"),
    }

    def __init__(self, delegate: SemanticInterpreter) -> None:
        self.delegate = delegate

    @staticmethod
    def _contains(text: str, markers: tuple[str, ...]) -> bool:
        return any(marker in text for marker in markers)

    @classmethod
    def _products(cls, query: str) -> tuple[str, ...]:
        low = query.casefold()
        found: list[str] = []
        for product, patterns in cls._PRODUCT_MARKERS.items():
            if any(re.search(pattern, low, re.I) for pattern in patterns):
                found.append(product)
        return tuple(found)

    @classmethod
    def _product(cls, query: str) -> str | None:
        products = cls._products(query)
        return products[0] if len(products) == 1 else None

    @classmethod
    def _contradictory_sprint_filters(cls, query: str) -> tuple[str, ...]:
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

        if mentions_sprint and self._contains(low, self._HEALTH):
            intent = "sprint_health"
        elif mentions_sprint and self._contains(low, self._VELOCITY):
            intent = "sprint_velocity"
        elif asks_current and self._contains(low, ("какой", "what")):
            intent = "sprint_current"

        products = self._products(query)
        product = products[0] if len(products) == 1 else None
        clarifications = list(frame.clarifications)

        # Multiple explicit product/space selectors are contradictory for the
        # current single-scope Core-8 task/sprint skills. Never silently keep the
        # first product chosen by the semantic model.
        if len(products) > 1 and (
            mentions_sprint or "задач" in low or "task" in low or "tasks" in low
        ):
            slots.pop("product", None)
            clarifications = [item for item in clarifications if item.field != "product"]
            clarifications.append(ClarificationNeed(
                "product",
                "В запросе указано несколько продуктов/пространств. Какой один использовать?",
                products,
            ))
        elif product:
            slots["product"] = product

        if asks_current:
            slots["sprint_raw"] = "current"

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
