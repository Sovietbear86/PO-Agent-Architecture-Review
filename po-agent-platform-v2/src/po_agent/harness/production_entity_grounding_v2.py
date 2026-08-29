"""Production entity grounding v2.

The semantic model proposes human-level constraints; this layer turns them into
source-backed canonical values. A requested constraint is never silently removed:
if grounding cannot prove it, execution must stop for clarification.
"""
from __future__ import annotations

import re
from typing import Any

from po_agent.domain.models import TaskStatus

from .dialogue_runtime import ClarificationNeed, SemanticFrame
from .live_entity_grounding import LiveGroundedEntityResolver


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(x.casefold() for x in re.findall(r"[A-Za-zА-Яа-яЁё0-9]+", value) if len(x) > 1)


def _token_match(wanted: tuple[str, ...], candidate: str) -> bool:
    hay = _tokens(candidate)
    return bool(wanted) and all(any(h == w or h.startswith(w) or w.startswith(h) for h in hay) for w in wanted)


class ProductionEntityResolverV2(LiveGroundedEntityResolver):
    _OPEN_STATUS_TERMS = {
        "open",
        "opened",
        "открыт",
        "открыта",
    }
    _NOT_COMPLETED_TERMS = {
        "open_tasks",
        "not_completed",
        "unresolved",
        "active",
        "открытые",
        "незакрытые",
        "незавершенные",
        "незавершённые",
    }
    _COMPLETED_TERMS = {
        "completed",
        "closed_tasks",
        "resolved_or_closed",
        "done",
        "закрытые",
        "завершенные",
        "завершённые",
        "closed/resolved",
        "closed+resolved",
    }
    _PERSON_RAW_ALIASES = (
        "person",
        "person_name",
        "member",
        "member_name",
        "assignee_raw",
        "assignee_name",
        "employee",
        "user",
    )

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
        context["known_statuses"] = sorted({
            *[str(value) for value in context.get("known_statuses", []) if value],
            *[status.value for status in TaskStatus],
        })
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

    @staticmethod
    def _query_requests_open_task_set(query: str) -> bool:
        text = query.casefold()
        return any(
            marker in text
            for marker in (
                "открытые",
                "открытых",
                "незакрытые",
                "незаверш",
                "open tasks",
                "unresolved tasks",
                "not completed",
            )
        )

    @classmethod
    def _normalize_status_constraint(cls, slots: dict[str, str], original_query: str) -> None:
        raw = str(slots.get("status_raw") or "").strip()
        status = str(slots.get("status") or "").strip()
        semantic = str(slots.get("status_semantic") or "").strip()
        values = {value.casefold() for value in (raw, status, semantic) if value}

        if any(value in cls._COMPLETED_TERMS or "/" in value and {"closed", "resolved"} <= set(re.split(r"[/+\s]+", value)) for value in values):
            slots["status"] = "completed"
            slots.pop("status_semantic", None)
            return
        if any(value in cls._NOT_COMPLETED_TERMS for value in values):
            slots["status"] = "not_completed"
            slots.pop("status_semantic", None)
            return
        if not status and any(value in cls._OPEN_STATUS_TERMS for value in values):
            slots["status"] = "not_completed" if cls._query_requests_open_task_set(original_query) else "Open"
            slots.pop("status_semantic", None)

    @classmethod
    def _normalize_person_slots(cls, slots: dict[str, str]) -> None:
        if not slots.get("person_raw"):
            for alias in cls._PERSON_RAW_ALIASES:
                value = slots.get(alias)
                if value:
                    slots["person_raw"] = value
                    break
        assignee = slots.get("assignee")
        if assignee and not slots.get("member_login") and not slots.get("person_raw"):
            slots["person_raw"] = assignee

    async def _ground_person_login(self, slots: dict[str, str]) -> None:
        """Canonicalize a model-proposed login from the user's person literal.

        `member_login` is a source identifier, not a semantic free-text field. If a
        correction/follow-up LLM leaks the full query (or any other prose) into that
        slot, never trust it merely because it is non-empty. Whenever `person_raw`
        exists, resolve the login again from configured/live AS21 identities and
        replace the proposal only with authoritative evidence.
        """
        person_raw = str(slots.get("person_raw") or "").strip()
        if not person_raw:
            return

        configured = self.team.resolve_person(person_raw)
        if len(configured) == 1:
            slots["member_login"] = configured[0].login
            return
        if configured:
            # Ambiguous configured identity: remove an unproven LLM proposal so the
            # invariant below produces clarification rather than a wrong assignee.
            slots.pop("member_login", None)
            return

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
        else:
            slots.pop("member_login", None)

    async def ground(self, frame: SemanticFrame, original_query: str) -> SemanticFrame:
        requested_slots = dict(frame.slots)
        slots = dict(frame.slots)

        # Normalize semantic aliases into the canonical slots consumed downstream.
        if slots.get("status_raw") and not slots.get("status") and not slots.get("status_semantic"):
            slots["status"] = slots["status_raw"]
        self._normalize_person_slots(slots)
        self._normalize_status_constraint(slots, original_query)

        # Always re-ground a source identifier when a user-visible person literal is
        # available. This prevents stale/corrupted member_login values from a prior
        # correction turn from surviving into execution.
        await self._ground_person_login(slots)

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

        if final_slots.get("member_login"):
            final_slots["assignee"] = final_slots["member_login"]

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
        requested_person = next(
            (
                requested_slots.get(key)
                for key in ("person_raw", *self._PERSON_RAW_ALIASES, "assignee")
                if requested_slots.get(key)
            ),
            None,
        )
        if requested_person and not final_slots.get("member_login"):
            needs.append(ClarificationNeed(
                "member_login",
                f"Не удалось однозначно подтвердить исполнителя «{requested_person}».",
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
