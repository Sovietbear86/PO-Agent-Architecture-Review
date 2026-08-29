"""Recovery for explicit task-search constraints omitted by the semantic LLM.

The semantic core stays LLM-first. Production experience showed that the configured
LLM can deterministically return a valid task_search intent while omitting every slot,
and can repeat the same failure in a dedicated recovery prompt. This module therefore
uses two bounded recovery sources:

1. a secondary LLM extraction pass;
2. a deterministic *surface* safety-net for constraints that are explicitly written in
   the user's request.

The deterministic pass does not resolve AS21 entities and never invents identifiers.
It only preserves literal user spans (person wording, product/space token, status text,
explicit task/sprint IDs) so a failed LLM parse cannot silently broaden a real query.
Source/entity grounding remains downstream.
"""
from __future__ import annotations

import re
from typing import Any

from po_agent.llm.client import LLMMessage

from .dialogue_runtime import SemanticFrame
from .semantic_core_v2 import _SPRINT_ID_FULL, _TASK_KEY_FULL, LLMFirstSemanticInterpreter


class RecoveringLLMFirstSemanticInterpreter(LLMFirstSemanticInterpreter):
    """LLM-first interpreter with bounded LLM + literal-surface recovery."""

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

    # These expressions recognize *request syntax*, not AS21 domain values. Values
    # captured by them are always literal spans from the query and are grounded later.
    _STATUS_SURFACE_RE = re.compile(
        r"(?:\bсо\s+статусом\b|\bстатус(?:ом|а)?\b|\bstatus\b)\s*[:=]?\s*[\"']?"
        r"(?P<value>[A-Za-zА-Яа-яЁё0-9_.-]+(?:\s+[A-Za-zА-Яа-яЁё0-9_.-]+){0,2})",
        re.I,
    )
    _PRODUCT_SURFACE_RE = re.compile(
        r"(?:\bв\b|\bпо\b|\bпространств(?:е|у|а)\b|\bпроект(?:е|у|а)\b|\bspace\b|\bproject\b)"
        r"\s+(?P<value>[A-ZА-Я][A-ZА-Я0-9_-]{1,24})\b"
    )
    _PERSON_AFTER_TASK_RE = re.compile(
        r"\b(?:задачи|задач|tasks)\s+"
        r"(?!в\b|по\b|со\b|с\b|на\b|из\b|для\b|со\s+статусом\b|status\b)"
        r"(?P<value>[А-ЯЁA-Z][А-Яа-яЁёA-Za-z'’-]{2,}"
        r"(?:\s+[А-ЯЁA-Z][А-Яа-яЁёA-Za-z'’-]{2,})?)",
        re.I,
    )
    _PERSON_MARKER_RE = re.compile(
        r"(?:\bдля\b|\bу\b|\bназначен(?:о|ы|ные)?\s+(?:на|для)?\s*)"
        r"(?P<value>[А-ЯЁA-Z][А-Яа-яЁёA-Za-z'’-]{2,}"
        r"(?:\s+[А-ЯЁA-Z][А-Яа-яЁёA-Za-z'’-]{2,})?)",
        re.I,
    )

    @staticmethod
    def _literal_surface_value(query: str, value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        compact = value.strip().strip("\"'")
        if not compact:
            return None
        return compact if compact.casefold() in query.casefold() else None

    @classmethod
    def _deterministic_surface_slots(cls, query: str) -> dict[str, str]:
        """Preserve explicit filter spans when semantic LLM passes drop them.

        This deliberately does not know team members, products, status semantics or
        AS21 IDs. It recognizes only stable request syntax and literal structural IDs.
        Any value still has to pass slot-contract checks and downstream grounding.
        """
        recovered: dict[str, str] = {}

        # Structural IDs use the canonical guards already owned by semantic_core_v2.
        structural = cls._structural_overlay(query, {})
        recovered.update(structural)

        status_match = cls._STATUS_SURFACE_RE.search(query)
        if status_match:
            value = cls._literal_surface_value(query, status_match.group("value"))
            if value:
                # Stop a status span before common following filter markers.
                value = re.split(r"\s+(?:в|по|на|для|из)\s+", value, maxsplit=1, flags=re.I)[0].strip()
                if value:
                    # Preserve the user's literal status only. Business semantics
                    # (for example whether Todo belongs to an open set) are grounded
                    # by the AS21/domain resolver, never hard-coded in this parser.
                    recovered["status_raw"] = value

        product_match = cls._PRODUCT_SURFACE_RE.search(query)
        if product_match:
            value = cls._literal_surface_value(query, product_match.group("value"))
            if value and not _SPRINT_ID_FULL.fullmatch(value) and not _TASK_KEY_FULL.fullmatch(value):
                recovered["product"] = value

        person_match = cls._PERSON_AFTER_TASK_RE.search(query) or cls._PERSON_MARKER_RE.search(query)
        if person_match:
            value = cls._literal_surface_value(query, person_match.group("value"))
            if value:
                # A product/status token immediately after "задачи" is not a person.
                folded = value.casefold()
                if folded not in {"todo", "open", "closed", "done", "blocked", "in progress"}:
                    recovered["person_raw"] = value

        return cls._drop_unsafe_slots(query, recovered)

    @staticmethod
    def _same_surface_value(left: Any, right: Any) -> bool:
        if not isinstance(left, str) or not isinstance(right, str):
            return left == right
        return " ".join(left.split()).casefold() == " ".join(right.split()).casefold()

    @classmethod
    def _needs_surface_recovery(cls, query: str, frame: SemanticFrame) -> tuple[bool, dict[str, str]]:
        """Recover only explicit constraints missing/stale in the current frame.

        A task/sprint-only lookup whose structural selector is already present must
        not trigger an unnecessary LLM recovery pass. Conversely, a structural ID
        must not suppress recovery of an explicit person/status/product filter.
        During a correction, an explicit *new* literal (e.g. status=in progress)
        overrides stale semantic state from the previous turn.
        """
        expected = cls._deterministic_surface_slots(query)
        if not expected:
            return False, expected
        for key, value in expected.items():
            if key not in frame.slots or not cls._same_surface_value(frame.slots.get(key), value):
                return True, expected
        return False, expected

    async def _recover_empty_task_slots(
        self,
        query: str,
        *,
        context: dict[str, Any] | None,
        frame: SemanticFrame,
    ) -> SemanticFrame:
        if frame.intent_hint != "task_search":
            return frame

        needs_recovery, deterministic = self._needs_surface_recovery(query, frame)
        if not needs_recovery:
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

        recovered: dict[str, str] = {}
        if isinstance(recovered_raw, dict):
            for key in self._RECOVERY_SURFACE_KEYS:
                value = self._literal_surface_value(query, recovered_raw.get(key))
                if value is not None:
                    recovered[key] = value

            phrase = recovered_raw.get("phrase")
            phrase_value = self._literal_surface_value(query, phrase)
            if phrase_value is not None:
                recovered["phrase"] = phrase_value

        # Start with the primary frame so valid grounded/structural constraints are
        # never discarded merely because one semantic field needs recovery.
        merged = dict(frame.slots)

        # A literal surface constraint in the *current* query is authoritative over
        # stale prior-turn semantic state, but it still remains raw/unresolved here.
        for key, value in deterministic.items():
            merged[key] = value

        # LLM recovery may fill additional safe fields only when not already fixed
        # by the current literal surface or primary frame.
        for key, value in recovered.items():
            merged.setdefault(key, value)

        merged = self._structural_overlay(query, merged)
        issues = self._slot_contract_issues(query, merged)
        if issues:
            # Fail closed on unsafe additions, while preserving the original frame
            # and deterministic literal constraints that independently pass checks.
            safe = self._drop_unsafe_slots(query, merged)
            if not safe:
                return frame
            merged = safe

        return SemanticFrame(
            canonical_query=frame.canonical_query,
            intent_hint=frame.intent_hint,
            slots=merged,
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
