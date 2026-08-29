"""Recovery pass for production semantic slots when the primary LLM frame is empty.

The production semantic core remains LLM-first. This module adds a narrowly scoped
second-pass extractor with a flat JSON contract because some Qwen/Coder responses
reliably return a valid intent but an empty nested ``slots`` object. Recovered raw
values must be literal spans of the user's query; no AS21 identifiers are guessed.
"""
from __future__ import annotations

from typing import Any

from po_agent.llm.client import LLMMessage

from .dialogue_runtime import SemanticFrame
from .semantic_core_v2 import LLMFirstSemanticInterpreter


class RecoveringLLMFirstSemanticInterpreter(LLMFirstSemanticInterpreter):
    """LLM-first interpreter with a bounded flat-slot recovery pass."""

    SLOT_RECOVERY_SYSTEM = """You recover explicit task-search constraints that were omitted from a semantic frame.
Return ONE flat JSON object only. Do not nest values under a `slots` key.
Allowed keys are exactly:
person_raw, product, status_raw, sprint_raw, release_raw, member_login, task_key, phrase.

Rules:
- Copy only constraints explicitly present in the ORIGINAL user query.
- person_raw/product/status_raw/sprint_raw/release_raw/member_login/task_key must be exact literal substrings from the query.
- Never invent or resolve AS21 IDs, logins, people, products, statuses, sprints or releases.
- Use null for every absent key.
- Do not return explanations, prose, arrays, markdown or additional keys.
- `phrase` may be a compact literal search phrase only when the user explicitly asks for text/content matching.
- Prefer raw surface wording exactly as typed by the user.
"""

    _RECOVERY_SURFACE_KEYS = (
        "person_raw",
        "product",
        "status_raw",
        "sprint_raw",
        "release_raw",
        "member_login",
        "task_key",
    )

    @staticmethod
    def _literal_surface_value(query: str, value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        compact = value.strip()
        if not compact:
            return None
        return compact if compact.casefold() in query.casefold() else None

    async def _recover_empty_task_slots(
        self,
        query: str,
        *,
        context: dict[str, Any] | None,
        frame: SemanticFrame,
    ) -> SemanticFrame:
        if frame.intent_hint != "task_search" or frame.slots:
            return frame

        payload = {
            "original_query": query,
            "intent_hint": frame.intent_hint,
            "canonical_query": frame.canonical_query,
            "context": context or {},
        }
        recovered_raw = await self._complete_json(
            [
                LLMMessage(role="system", content=self.SLOT_RECOVERY_SYSTEM),
                LLMMessage(role="user", content=self._json(payload)),
            ]
        )
        if not isinstance(recovered_raw, dict):
            return frame

        recovered: dict[str, str] = {}
        for key in self._RECOVERY_SURFACE_KEYS:
            value = self._literal_surface_value(query, recovered_raw.get(key))
            if value is not None:
                recovered[key] = value

        phrase = recovered_raw.get("phrase")
        phrase_value = self._literal_surface_value(query, phrase)
        if phrase_value is not None:
            recovered["phrase"] = phrase_value

        if not recovered:
            return frame

        # Reuse the existing structural guardrails. This removes ambiguous task
        # keys and promotes literal sprint/task IDs without introducing language
        # heuristics or source guesses.
        recovered = self._structural_overlay(query, recovered)
        issues = self._slot_contract_issues(query, recovered)
        if issues:
            recovered = self._drop_unsafe_slots(query, recovered)
            if not recovered:
                return frame

        return SemanticFrame(
            canonical_query=frame.canonical_query,
            intent_hint=frame.intent_hint,
            slots=recovered,
            clarifications=list(frame.clarifications),
            confidence=frame.confidence,
            llm_used=True,
        )

    @staticmethod
    def _json(value: dict[str, Any]) -> str:
        import json

        return json.dumps(value, ensure_ascii=False, sort_keys=True)

    async def interpret(self, query: str, *, context: dict[str, Any] | None = None) -> SemanticFrame:
        frame = await super().interpret(query, context=context)
        return await self._recover_empty_task_slots(query, context=context, frame=frame)
