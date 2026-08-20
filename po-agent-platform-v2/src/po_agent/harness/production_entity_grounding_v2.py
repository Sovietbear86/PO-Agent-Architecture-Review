"""Production entity grounding v2.

The semantic model proposes human-level constraints; this layer turns them into
source-backed canonical values. A requested constraint is never silently removed:
if grounding cannot prove it, execution must stop for clarification.
"""
from __future__ import annotations

import re
from typing import Any

from .dialogue_runtime import ClarificationNeed, SemanticFrame
from .live_entity_grounding import LiveGroundedEntityResolver


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(x.casefold() for x in re.findall(r"[A-Za-zА-Яа-яЁё0-9]+", value) if len(x) > 1)


def _token_match(wanted: tuple[str, ...], candidate: str) -> bool:
    hay = _tokens(candidate)
    return bool(wanted) and all(any(h == w or h.startswith(w) or w.startswith(h) for h in hay) for w in wanted)


class ProductionEntityResolverV2(LiveGroundedEntityResolver):
    async def semantic_context(self) -> dict[str, Any]:
        context = await super().semantic_context()
        tasks = await self.adapter.search_tasks("", max_results=getattr(self.adapter, "_scan_limit", 10000))
        identities: list[dict[str, str]] = []
        seen: set[tuple[str, str, str]] = set()
        known_assignees = {str(value) for value in context.get("known_assignees", []) if value}
        known_products = {str(task.project_space).upper() for task in tasks if task.project_space}
        for task in tasks:
            display = str(task.assignee or "").strip()
            login = str(task.assignee_login or "").strip()
            external_id = str(task.assignee_id or "").strip()
            key = (display, login, external_id)
            if not any(key) or key in seen:
                continue
            seen.add(key)
            identities.append({"display_name": display, "login": login, "external_id": external_id})
            known_assignees.update(value for value in key if value)
        context["known_assignees"] = sorted(known_assignees)
        context["assignee_identities"] = identities
        context["known_products"] = sorted(known_products)
        return context

    @staticmethod
    def _dedupe_needs(items: list[ClarificationNeed]) -> list[ClarificationNeed]:
        out: list[ClarificationNeed] = []
        seen: set[str] = set()
        for item in items:
            if item.field in seen:
                continue
            seen.add(item.field)
            out.append(item)
        return out

    async def ground(self, frame: SemanticFrame, original_query: str) -> SemanticFrame:
        requested_slots = dict(frame.slots)
        slots = dict(frame.slots)

        # Normalize semantic aliases into the canonical slots consumed downstream.
        if slots.get("status_raw") and not slots.get("status") and not slots.get("status_semantic"):
            slots["status"] = slots["status_raw"]
        if slots.get("member_name") and not slots.get("person_raw"):
            slots["person_raw"] = slots["member_name"]

        person_raw = slots.get("person_raw")
        if person_raw and not slots.get("member_login"):
            configured = self.team.resolve_person(person_raw)
            if len(configured) == 1:
                slots["member_login"] = configured[0].login
            elif not configured:
                context = await self.semantic_context()
                wanted = _tokens(person_raw)
                matches: list[dict[str, str]] = []
                for identity in context.get("assignee_identities", []):
                    hay = " ".join(str(identity.get(k) or "") for k in ("display_name", "login", "external_id"))
                    if _token_match(wanted, hay):
                        matches.append(identity)
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
        grounded = await super().ground(enriched, original_query)
        final_slots = dict(grounded.slots)
        needs = list(grounded.clarifications)
        context = await self.semantic_context()

        # Product/space is a real source constraint too. Never accept arbitrary
        # uppercase text as a product and never drop a requested scope silently.
        requested_product = requested_slots.get("product")
        if requested_product:
            wanted = requested_product.strip().upper()
            products = [str(x).upper() for x in context.get("known_products", [])]
            canonical_product = next((x for x in products if x.casefold() == wanted.casefold()), None)
            if canonical_product:
                final_slots["product"] = canonical_product
            else:
                final_slots.pop("product", None)
                needs.append(ClarificationNeed(
                    "product",
                    f"Не могу подтвердить пространство/продукт «{requested_product}» по данным AS21. Что выбрать?",
                    tuple(products),
                ))

        # Invariant: an explicitly requested semantic constraint either survives in
        # canonical grounded form or produces clarification. It may never disappear
        # and broaden the query to all tasks.
        if (requested_slots.get("person_raw") or requested_slots.get("member_name")) and not final_slots.get("member_login"):
            needs.append(ClarificationNeed(
                "member_login",
                f"Не удалось однозначно подтвердить исполнителя «{requested_slots.get('person_raw') or requested_slots.get('member_name')}».",
                tuple(str(x) for x in context.get("known_assignees", [])),
            ))
        if requested_slots.get("sprint_id") and not final_slots.get("sprint_id"):
            needs.append(ClarificationNeed(
                "sprint_id",
                f"Не удалось подтвердить спринт «{requested_slots['sprint_id']}».",
                tuple(str(x) for x in context.get("known_sprints", [])),
            ))
        if (requested_slots.get("status") or requested_slots.get("status_raw") or requested_slots.get("status_semantic")) and not (
            final_slots.get("status") or any(n.field == "status" for n in needs)
        ):
            needs.append(ClarificationNeed(
                "status",
                f"Не удалось однозначно подтвердить условие статуса «{requested_slots.get('status') or requested_slots.get('status_raw') or requested_slots.get('status_semantic')}».",
                tuple(str(x) for x in context.get("known_statuses", [])),
            ))

        return SemanticFrame(
            canonical_query=grounded.canonical_query,
            intent_hint=grounded.intent_hint,
            slots=final_slots,
            clarifications=self._dedupe_needs(needs),
            confidence=grounded.confidence,
            llm_used=grounded.llm_used,
        )
