"""Deterministic grounding for entities proposed by the semantic LLM.

The LLM may normalize language, but source identifiers are accepted only when
resolved against source-backed candidates. User wording is evidence of intent,
not proof that an identifier exists in AS21.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from po_agent.adapters.as21 import AS21Adapter

from .dialogue_runtime import ClarificationNeed, SemanticFrame
from .learned_semantics import LearnedSemanticsStore


@dataclass(frozen=True)
class TeamDirectoryEntry:
    login: str
    full_name: str
    products: tuple[str, ...] = ()


class TeamDirectory:
    def __init__(self, entries: tuple[TeamDirectoryEntry, ...] = ()) -> None:
        self.entries = entries

    @classmethod
    def from_yaml(cls, path: str | Path | None) -> "TeamDirectory":
        if path is None:
            return cls()
        file = Path(path)
        if not file.exists():
            return cls()
        data = yaml.safe_load(file.read_text(encoding="utf-8")) or {}
        entries = []
        for item in data.get("members", []):
            if not isinstance(item, dict) or not item.get("login"):
                continue
            entries.append(TeamDirectoryEntry(
                login=str(item["login"]),
                full_name=str(item.get("full_name") or "").strip(),
                products=tuple(str(x) for x in item.get("products", []) if x),
            ))
        return cls(tuple(entries))

    def public_context(self) -> list[dict[str, Any]]:
        return [{"login": x.login, "full_name": x.full_name, "products": list(x.products)} for x in self.entries]

    @staticmethod
    def _tokens(value: str) -> tuple[str, ...]:
        return tuple(x.casefold() for x in re.findall(r"[A-Za-zА-Яа-яЁё0-9]+", value) if len(x) > 1)

    def resolve_person(self, candidate: str) -> tuple[TeamDirectoryEntry, ...]:
        raw = candidate.strip().casefold()
        if not raw:
            return ()
        exact = tuple(x for x in self.entries if raw in {x.login.casefold(), x.full_name.casefold()})
        if exact:
            return exact
        wanted = self._tokens(candidate)
        if not wanted:
            return ()
        matches = []
        for entry in self.entries:
            hay = self._tokens(f"{entry.full_name} {entry.login}")
            if all(any(h == w or h.startswith(w) or w.startswith(h) for h in hay) for w in wanted):
                matches.append(entry)
        return tuple(matches)


class GroundedEntityResolver:
    """Resolve person/sprint/release/status semantics against real source facts."""

    _VIRTUAL_STATUS_FILTERS = {"all", "not_completed", "completed"}

    def __init__(
        self,
        adapter: AS21Adapter,
        *,
        team: TeamDirectory | None = None,
        semantics: LearnedSemanticsStore | None = None,
    ) -> None:
        self.adapter = adapter
        self.team = team or TeamDirectory()
        self.semantics = semantics

    async def semantic_context(self) -> dict[str, Any]:
        tasks = await self.adapter.search_tasks("")
        directory_logins = {x.login for x in self.team.entries}
        task_logins = {t.assignee for t in tasks if t.assignee}
        return {
            "team_members": self.team.public_context(),
            "known_assignees": sorted(directory_logins | task_logins),
            "known_sprints": sorted({t.sprint_id for t in tasks if t.sprint_id}),
            "known_releases": sorted({t.release_id for t in tasks if t.release_id}),
            "known_statuses": sorted({t.status.value for t in tasks if t.status}),
            "learned_semantics": self.semantics.context("global") if self.semantics else {},
        }

    @staticmethod
    def _match_shorthand(raw: str, candidates: list[str]) -> list[str]:
        parts = [x.casefold() for x in re.findall(r"[A-Za-zА-Яа-яЁё0-9]+", raw)]
        out = []
        for candidate in candidates:
            ctokens = [x.casefold() for x in re.findall(r"[A-Za-zА-Яа-яЁё0-9]+", candidate)]
            if all(any(p == c for c in ctokens) for p in parts):
                out.append(candidate)
        return out

    @staticmethod
    def _canonical_candidate(value: str, candidates: list[str]) -> str | None:
        wanted = value.strip().casefold()
        for candidate in candidates:
            if str(candidate).casefold() == wanted:
                return str(candidate)
        return None

    async def ground(self, frame: SemanticFrame, original_query: str) -> SemanticFrame:
        del original_query  # raw user text never bypasses source validation
        context = await self.semantic_context()
        needs = list(frame.clarifications)
        slots = dict(frame.slots)
        canonical = frame.canonical_query

        person_raw = slots.get("person_raw") or slots.get("member_name")
        member_login = slots.get("member_login")
        if member_login:
            grounded_login = self._canonical_candidate(member_login, context["known_assignees"])
            if grounded_login is None:
                slots.pop("member_login", None)
                needs.append(ClarificationNeed(
                    "member_login",
                    f"Не могу подтвердить исполнителя «{member_login}» по данным источника. Кого вы имеете в виду?",
                    tuple(context["known_assignees"]),
                ))
            else:
                slots["member_login"] = grounded_login
                canonical = canonical.replace("{member_login}", grounded_login)
        elif person_raw:
            people = self.team.resolve_person(person_raw)
            if len(people) == 1:
                slots["member_login"] = people[0].login
                canonical = canonical.replace("{member_login}", people[0].login)
            elif len(people) > 1:
                needs.append(ClarificationNeed("member_login", f"Нашёл несколько участников для «{person_raw}». Кого выбрать?", tuple(x.login for x in people)))
            else:
                assignee_matches = [x for x in context["known_assignees"] if person_raw.casefold() in str(x).casefold()]
                if len(assignee_matches) == 1:
                    slots["member_login"] = str(assignee_matches[0])
                    canonical = canonical.replace("{member_login}", str(assignee_matches[0]))
                else:
                    needs.append(ClarificationNeed(
                        "member_login",
                        f"Не нашёл однозначного участника «{person_raw}». Уточните ФИО или login.",
                        tuple(assignee_matches or context["known_assignees"]),
                    ))

        sprint_id = slots.get("sprint_id")
        sprint_raw = slots.get("sprint_raw")
        if sprint_id:
            grounded_sprint = self._canonical_candidate(sprint_id, context["known_sprints"])
            if grounded_sprint is None:
                slots.pop("sprint_id", None)
                needs.append(ClarificationNeed(
                    "sprint_id",
                    f"Не могу подтвердить спринт «{sprint_id}» по данным источника. Какой спринт выбрать?",
                    tuple(context["known_sprints"]),
                ))
            else:
                slots["sprint_id"] = grounded_sprint
                canonical = canonical.replace("{sprint_id}", grounded_sprint)
        elif sprint_raw and "{sprint_id}" in canonical:
            matches = self._match_shorthand(sprint_raw, context["known_sprints"])
            if len(matches) == 1:
                slots["sprint_id"] = matches[0]
                canonical = canonical.replace("{sprint_id}", matches[0])
            else:
                needs.append(ClarificationNeed("sprint_id", f"Какой именно спринт соответствует «{sprint_raw}»?", tuple(matches or context["known_sprints"])))

        release_id = slots.get("release_id")
        release_raw = slots.get("release_raw")
        if release_id:
            grounded_release = self._canonical_candidate(release_id, context["known_releases"])
            if grounded_release is None:
                slots.pop("release_id", None)
                needs.append(ClarificationNeed(
                    "release_id",
                    f"Не могу подтвердить релиз «{release_id}» по данным источника. Какой релиз выбрать?",
                    tuple(context["known_releases"]),
                ))
            else:
                slots["release_id"] = grounded_release
                canonical = canonical.replace("{release_id}", grounded_release)
        elif release_raw and "{release_id}" in canonical:
            matches = self._match_shorthand(release_raw, context["known_releases"])
            if len(matches) == 1:
                slots["release_id"] = matches[0]
                canonical = canonical.replace("{release_id}", matches[0])
            else:
                needs.append(ClarificationNeed("release_id", f"Какой именно релиз соответствует «{release_raw}»?", tuple(matches or context["known_releases"])))

        semantic_term = slots.get("status_semantic")
        if semantic_term and "{status}" in canonical:
            learned = context["learned_semantics"].get(semantic_term.casefold())
            if learned:
                slots["status"] = learned
                canonical = canonical.replace("{status}", learned)
            else:
                slots.pop("status", None)
                needs.append(ClarificationNeed("status", f"Что считать «{slots.get('status_raw', semantic_term)}»? Укажите статус или правило отбора.", tuple(context["known_statuses"])))
        elif slots.get("status"):
            status = str(slots["status"])
            grounded_status = self._canonical_candidate(status, context["known_statuses"])
            if grounded_status is not None:
                slots["status"] = grounded_status
                canonical = canonical.replace("{status}", grounded_status)
            elif status.casefold() not in self._VIRTUAL_STATUS_FILTERS:
                slots.pop("status", None)
                needs.append(ClarificationNeed(
                    "status",
                    f"Не могу подтвердить статус «{status}» по данным источника. Что именно использовать?",
                    tuple(context["known_statuses"]),
                ))

        return SemanticFrame(
            canonical_query=canonical,
            intent_hint=frame.intent_hint,
            slots=slots,
            clarifications=self._dedupe(needs),
            confidence=frame.confidence,
            llm_used=frame.llm_used,
        )

    @staticmethod
    def _dedupe(items: list[ClarificationNeed]) -> list[ClarificationNeed]:
        result = []
        seen = set()
        for item in items:
            if item.field in seen:
                continue
            seen.add(item.field)
            result.append(item)
        return result
