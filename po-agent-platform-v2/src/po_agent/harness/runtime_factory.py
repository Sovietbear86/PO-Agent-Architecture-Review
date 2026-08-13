"""Runtime construction for fake and production AS21 sources."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from po_agent.adapters import FakeAS21Adapter, TaskApiAS21Adapter
from po_agent.adapters.as21 import AS21Adapter

from .historical_wiring import enable_historical_skills
from .observed_runtime import ObservedHarnessRuntime
from .source_aware_runtime import SourceAwareHarnessRuntime
from .source_contracts import (
    ReleaseTimelineSource,
    SourceDependencyBundle,
    SprintSnapshotSource,
    YamlTeamCompetencySource,
)
from .source_readiness import SourceReadinessReport, build_source_readiness
from .team_matching_wiring import enable_team_matching

RuntimeMode = Literal["fake", "task-api"]


@dataclass(frozen=True)
class RuntimeBundle:
    mode: RuntimeMode
    runtime: ObservedHarnessRuntime
    adapter: AS21Adapter
    readiness: SourceReadinessReport
    dependencies: SourceDependencyBundle


def _resolve_team_config(explicit: str | None, mode: RuntimeMode) -> Path | None:
    if explicit:
        path = Path(explicit)
        return path if path.exists() else None
    if mode != "task-api":
        return None
    candidates = (Path("../task-api/config/team_members.yaml"), Path("task-api/config/team_members.yaml"))
    return next((path for path in candidates if path.exists()), None)


def build_runtime_bundle(
    mode: str = "fake",
    *,
    task_api_base_url: str = "http://localhost:8003",
    task_api_timeout_seconds: float = 30.0,
    team_config_path: str | None = None,
    sprint_snapshots: SprintSnapshotSource | None = None,
    release_timeline: ReleaseTimelineSource | None = None,
) -> RuntimeBundle:
    normalized = mode.strip().lower()
    if normalized == "fake":
        adapter: AS21Adapter = FakeAS21Adapter()
        selected: RuntimeMode = "fake"
    elif normalized in {"task-api", "task_api", "real"}:
        adapter = TaskApiAS21Adapter(base_url=task_api_base_url, timeout_seconds=task_api_timeout_seconds)
        selected = "task-api"
    else:
        raise ValueError(f"Unsupported PO_AGENT_AS21_MODE: {mode}")

    team_path = _resolve_team_config(team_config_path, selected)
    team_source = YamlTeamCompetencySource(team_path) if team_path is not None else None
    dependencies = SourceDependencyBundle(
        sprint_snapshots=sprint_snapshots,
        team_competencies=team_source,
        release_timeline=release_timeline,
    )
    readiness = build_source_readiness(adapter, extra_facts=dependencies.facts)

    inner = SourceAwareHarnessRuntime(adapter, source_facts=readiness.available_facts)
    if team_source is not None and team_source.has_declared_profiles():
        enable_team_matching(inner, team_source)
    if sprint_snapshots is not None or release_timeline is not None:
        enable_historical_skills(inner, sprint_snapshots=sprint_snapshots, release_timeline=release_timeline)
    runtime = ObservedHarnessRuntime(inner)

    return RuntimeBundle(
        mode=selected,
        runtime=runtime,
        adapter=adapter,
        readiness=readiness,
        dependencies=dependencies,
    )
