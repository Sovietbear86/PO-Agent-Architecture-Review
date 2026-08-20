"""Production entity grounding v2.

Resolve semantic person references against both the configured team directory and
real AS21 task identity fields (display name, login, external id). This layer does
not parse natural-language grammar; it only resolves a person_raw candidate that
the semantic model already extracted.
"""
from __future__ import annotations

import re
from typing import Any

from .dialogue_runtime import SemanticFrame
from .live_entity_grounding import LiveGroundedEntityResolver


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(x.casefold() for x in re.findall(r"[A-Za-zА-Яа-яЁё0-9]+", value) if len(x) > 1)


def _token_match(wanted: tuple[str, ...], candidate: str) -> bool:
    hay = _tokens(candidate)
    return bool(wanted) and all(
        any(h == w or h.startswith(w) or w.startswith(h) for h in hay)
        for w in wanted
    )


class ProductionEntityResolverV2(LiveGroundedEntityResolver):
    async def semantic_context(self) -> dict[str, Any]:
        context = await super().semantic_context()
        tasks = await self.adapter.search_tasks("", max_results=getattr(self.adapter, "_scan_limit", 10000))
        identities: list[dict[str, str]] = []
        seen: set[tuple[str, str, str]] = set()
        known = {str(value) for value in context.get("known_assignees", []) if value}
        for task in tasks:
            display = str(task.assignee or "").strip()
            login = str(task.assignee_login or "").strip()
            external_id = str(task.assignee_id or "").strip()
            key = (display, login, external_id)
            if not any(key) or key in seen:
                continue
            seen.add(key)
            identities.append({"display_name": display, "login": login, "external_id": external_id})
            known.update(value for value in key if value)
        context["known_assignees"] = sorted(known)
        context["assignee_identities"] = identities
        return context

    async def ground(self, frame: SemanticFrame, original_query: str) -> SemanticFrame:
        slots = dict(frame.slots)
        person_raw = slots.get("person_raw") or slots.get("member_name")
        if person_raw and not slots.get("member_login"):
            # First preserve the configured team directory as the strongest
            # identity source. If it is not decisive, compare the semantic person
            # candidate against live AS21 identity fields.
            configured = self.team.resolve_person(person_raw)
            if len(configured) == 1:
                slots["member_login"] = configured[0].login
            elif not configured:
                context = await self.semantic_context()
                wanted = _tokens(person_raw)
                matches: list[dict[str, str]] = []
                for identity in context.get("assignee_identities", []):
                    hay = " ".join(
                        str(identity.get(key) or "")
                        for key in ("display_name", "login", "external_id")
                    )
                    if _token_match(wanted, hay):
                        matches.append(identity)
                # Unique identity record only. Never guess between multiple real
                # people; the base resolver will ask for clarification instead.
                unique = {
                    (m.get("display_name", ""), m.get("login", ""), m.get("external_id", ""))
                    for m in matches
                }
                if len(unique) == 1:
                    display, login, external_id = next(iter(unique))
                    slots["member_login"] = login or external_id or display

        enriched = SemanticFrame(
            canonical_query=frame.canonical_query,
            intent_hint=frame.intent_hint,
            slots=slots,
            clarifications=list(frame.clarifications),
            confidence=frame.confidence,
            llm_used=frame.llm_used,
        )
        return await super().ground(enriched, original_query)
