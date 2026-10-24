"""Grounded team competency matching and assignee recommendation."""
from __future__ import annotations

import re
from collections import Counter

from po_agent.adapters.as21 import AS21Adapter
from po_agent.domain.models import Task

from .contracts import CapabilityResult, Evidence
from .source_contracts import TeamCompetencySource, TeamMemberProfile


_TOKEN = re.compile(r"[A-Za-zА-Яа-яЁё0-9+#.]{2,}")
_STOP = {
    "для", "или", "это", "как", "при", "над", "под", "без", "его", "ее", "её",
    "the", "and", "for", "with", "from", "task", "задача", "нужно", "требуется",
}


class TeamMatchingCapabilities:
    """Match only against declared profile evidence; never invent competencies."""

    def __init__(self, adapter: AS21Adapter, profiles: TeamCompetencySource) -> None:
        self.a = adapter
        self.profiles = profiles

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {x.casefold() for x in _TOKEN.findall(text or "") if x.casefold() not in _STOP}

    @classmethod
    def _profile_tokens(cls, profile: TeamMemberProfile) -> set[str]:
        declared = " ".join((profile.professional_profile, *profile.competencies, *profile.products))
        return cls._tokens(declared)

    @staticmethod
    def _profile_evidence(profile: TeamMemberProfile) -> Evidence:
        value = "; ".join(x for x in (profile.professional_profile, ", ".join(profile.competencies)) if x) or "declared profile"
        return Evidence(type="team_profile", source="team_config", entity_id=profile.login, label="declared_profile", value=value)

    async def _task(self, key: str) -> Task | None:
        return await self.a.get_task(key.upper())

    async def competency_match(self, args: dict[str, str]) -> CapabilityResult:
        key = args["task_key"].upper()
        task = await self._task(key)
        if task is None:
            return CapabilityResult(answer=f"Задача {key} не найдена.", data={"task_key": key, "found": False})
        task_tokens = self._tokens(f"{task.title} {task.description or ''}")
        rows = []
        evidence = [Evidence(type="task", source="as21", entity_id=task.key, label=task.title, value=task.status.value)]
        for profile in self.profiles.list_profiles():
            profile_tokens = self._profile_tokens(profile)
            matched = sorted(task_tokens & profile_tokens)
            if not matched:
                continue
            rows.append({
                "member": profile.login,
                "matched_terms": matched,
                "match_count": len(matched),
                "professional_profile": profile.professional_profile,
                "competencies": list(profile.competencies),
                "products": list(profile.products),
            })
            evidence.append(self._profile_evidence(profile))
        rows.sort(key=lambda x: (-int(x["match_count"]), str(x["member"])))
        warning = [] if rows else ["no_declared_competency_match"]
        answer = f"Для {key} найдено {len(rows)} совпадений с явно заявленными профилями команды."
        return CapabilityResult(answer=answer, data={"task_key": key, "matches": rows, "method": "declared_profile_token_overlap"}, evidence=evidence, warnings=warning)

    async def assignee_recommendation(self, args: dict[str, str]) -> CapabilityResult:
        key = args["task_key"].upper()
        task = await self._task(key)
        if task is None:
            return CapabilityResult(answer=f"Задача {key} не найдена.", data={"task_key": key, "found": False})
        task_tokens = self._tokens(f"{task.title} {task.description or ''}")
        active = [t for t in await self.a.search_tasks("") if not t.is_completed and t.assignee]
        load = Counter(t.assignee for t in active)
        rows = []
        evidence = [Evidence(type="task", source="as21", entity_id=task.key, label=task.title, value=task.status.value)]
        for profile in self.profiles.list_profiles():
            matched = sorted(task_tokens & self._profile_tokens(profile))
            if not matched:
                continue
            rows.append({
                "member": profile.login,
                "matched_terms": matched,
                "match_count": len(matched),
                "active_tasks": load.get(profile.login, 0),
                "professional_profile": profile.professional_profile,
                "competencies": list(profile.competencies),
            })
            evidence.append(self._profile_evidence(profile))
        rows.sort(key=lambda x: (-int(x["match_count"]), int(x["active_tasks"]), str(x["member"])))
        if not rows:
            return CapabilityResult(
                answer=f"Для {key} нельзя обоснованно рекомендовать исполнителя: нет совпадения с явно заявленными профилями.",
                data={"task_key": key, "recommendation": None, "candidates": [], "method": "declared_profile_then_active_task_load"},
                evidence=evidence,
                warnings=["insufficient_declared_competency_evidence"],
            )
        best = rows[0]
        answer = f"Для {key} наиболее обоснованный кандидат — {best['member']}: {best['match_count']} совпадений профиля, активных задач {best['active_tasks']}."
        return CapabilityResult(answer=answer, data={"task_key": key, "recommendation": best["member"], "candidates": rows, "method": "declared_profile_then_active_task_load"}, evidence=evidence)
