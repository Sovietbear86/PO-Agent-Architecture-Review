"""Runtime wiring for source-dependent team matching Skills."""
from __future__ import annotations

import re
from typing import Protocol

from .runtime import ExecutableSkill, HarnessRuntime
from .source_contracts import TeamCompetencySource
from .team_matching import TeamMatchingCapabilities


_TASK_KEY = re.compile(r"\b[A-ZА-Я][A-ZА-Я0-9_]{1,15}-\d+(?![-A-ZА-Я0-9_])\b", re.I)


class _Router(Protocol):
    def route(self, query: str) -> tuple[str, dict[str, str]]: ...


class TeamMatchingRouter:
    """Intercept only the two team matching intents, delegate everything else."""

    def __init__(self, base: _Router) -> None:
        self.base = base

    def route(self, query: str) -> tuple[str, dict[str, str]]:
        lowered = query.casefold()
        match = _TASK_KEY.search(query)
        if match:
            task_key = match.group(0)
            if any(token in lowered for token in (
                "подходит по компетенц", "соответствие компетенц", "competency match",
                "кто подходит", "профиль команды для",
            )):
                return "team_competency_match", {"task_key": task_key}
            if any(token in lowered for token in (
                "кому назначить", "рекомендуй исполнителя", "рекомендация исполнителя",
                "assignee recommendation", "кого назначить",
            )):
                return "team_assignee_recommendation", {"task_key": task_key}
        return self.base.route(query)


def enable_team_matching(runtime: HarnessRuntime, source: TeamCompetencySource) -> HarnessRuntime:
    """Register the two source-dependent Skills on an existing HarnessRuntime."""
    capabilities = TeamMatchingCapabilities(runtime.adapter, source)
    specs = (
        ("team-competency-match", "team_competency_match", "team.competency_match", capabilities.competency_match),
        ("team-assignee-recommendation", "team_assignee_recommendation", "team.assignee_recommendation", capabilities.assignee_recommendation),
    )
    for skill_id, intent, capability_id, handler in specs:
        runtime.capabilities.register(capability_id, handler)
        runtime.skills.register(
            ExecutableSkill(
                id=skill_id,
                version="1.0.0",
                intent=intent,
                capability_id=capability_id,
                description=f"Executable {intent} skill",
            )
        )
    runtime.router = TeamMatchingRouter(runtime.router)
    return runtime
