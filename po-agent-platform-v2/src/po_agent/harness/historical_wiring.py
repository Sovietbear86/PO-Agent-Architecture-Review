"""Runtime wiring for snapshot- and timeline-dependent Skills."""
from __future__ import annotations

import re
from typing import Protocol

from .historical_intelligence import ReleaseForecastCapabilities, SprintHistoricalCapabilities
from .runtime import ExecutableSkill, HarnessRuntime
from .source_contracts import ReleaseTimelineSource, SprintSnapshotSource


_SPRINT_KEY = re.compile(r"\b[A-Z]+-SPRNT-\d+\b", re.I)
_RELEASE_KEY = re.compile(r"\b[A-Z]+-\d{4}-Q\d+\b", re.I)


class _Router(Protocol):
    def route(self, query: str) -> tuple[str, dict[str, str]]: ...


class HistoricalRouter:
    def __init__(self, base: _Router, *, sprint_enabled: bool, release_enabled: bool) -> None:
        self.base = base
        self.sprint_enabled = sprint_enabled
        self.release_enabled = release_enabled

    def route(self, query: str) -> tuple[str, dict[str, str]]:
        lowered = query.casefold()
        if self.sprint_enabled and (match := _SPRINT_KEY.search(query)):
            sprint_id = match.group(0)
            if any(token in lowered for token in ("carryover", "перенос", "перенесено", "незавершенный commitment", "незавершённый commitment")):
                return "sprint_carryover", {"sprint_id": sprint_id}
            if any(token in lowered for token in ("scope change", "изменение scope", "изменение состава", "что добавили", "что убрали")):
                return "sprint_scope_change", {"sprint_id": sprint_id}
        if self.release_enabled and (match := _RELEASE_KEY.search(query)):
            release_id = match.group(0)
            if any(token in lowered for token in ("forecast", "прогноз", "когда закончим", "когда будет готов")):
                return "release_forecast", {"release_id": release_id}
        return self.base.route(query)


def enable_historical_skills(
    runtime: HarnessRuntime,
    *,
    sprint_snapshots: SprintSnapshotSource | None = None,
    release_timeline: ReleaseTimelineSource | None = None,
) -> HarnessRuntime:
    if sprint_snapshots is not None:
        sprint = SprintHistoricalCapabilities(runtime.adapter, sprint_snapshots)
        for skill_id, intent, capability_id, handler in (
            ("sprint-carryover", "sprint_carryover", "sprint.carryover", sprint.carryover),
            ("sprint-scope-change", "sprint_scope_change", "sprint.scope_change", sprint.scope_change),
        ):
            runtime.capabilities.register(capability_id, handler)
            runtime.skills.register(ExecutableSkill(skill_id, "1.0.0", intent, capability_id, f"Executable {intent} skill"))
    if release_timeline is not None:
        release = ReleaseForecastCapabilities(runtime.adapter, release_timeline)
        runtime.capabilities.register("release.forecast", release.forecast)
        runtime.skills.register(ExecutableSkill("release-forecast", "1.0.0", "release_forecast", "release.forecast", "Executable release_forecast skill"))
    runtime.router = HistoricalRouter(runtime.router, sprint_enabled=sprint_snapshots is not None, release_enabled=release_timeline is not None)
    return runtime
