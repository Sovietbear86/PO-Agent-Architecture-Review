"""Explicit source contracts for the five remaining source-dependent Skills.

These contracts deliberately separate *availability of source facts* from Skill
implementation. A runtime may implement a Skill only when the corresponding
source can provide the required facts without inference from current state.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

import yaml


@dataclass(frozen=True)
class SprintScopeSnapshot:
    sprint_id: str
    captured_at: datetime
    task_keys: tuple[str, ...]
    kind: str = "commitment"


class SprintSnapshotSource(Protocol):
    async def get_commitment_snapshot(self, sprint_id: str) -> SprintScopeSnapshot | None: ...


@dataclass(frozen=True)
class TeamMemberProfile:
    login: str
    products: tuple[str, ...]
    professional_profile: str
    competencies: tuple[str, ...]
    grade: int | None = None


class TeamCompetencySource(Protocol):
    def list_profiles(self) -> tuple[TeamMemberProfile, ...]: ...


@dataclass(frozen=True)
class ReleaseTimelinePoint:
    release_id: str
    captured_at: datetime
    completed: int
    total: int


class ReleaseTimelineSource(Protocol):
    async def get_timeline(self, release_id: str) -> tuple[ReleaseTimelinePoint, ...]: ...


class YamlTeamCompetencySource:
    """Read declared team profiles from the project's canonical team config.

    `professional_profile` is treated as declared profile evidence, not as an
    LLM-generated competency. Empty `competencies` remain empty; no skills are
    invented from names, grades, or task assignment history.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    @staticmethod
    def _normalize_competencies(raw: object) -> tuple[str, ...]:
        if isinstance(raw, dict):
            return tuple(sorted(str(key) for key, value in raw.items() if value))
        if isinstance(raw, list):
            return tuple(str(item) for item in raw if str(item).strip())
        return ()

    def list_profiles(self) -> tuple[TeamMemberProfile, ...]:
        if not self.path.exists():
            return ()
        data = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        members = data.get("members", [])
        result: list[TeamMemberProfile] = []
        for member in members:
            if not isinstance(member, dict) or not member.get("login"):
                continue
            result.append(
                TeamMemberProfile(
                    login=str(member["login"]),
                    products=tuple(str(x) for x in member.get("products", []) if x),
                    professional_profile=str(member.get("professional_profile") or "").strip(),
                    competencies=self._normalize_competencies(member.get("competencies")),
                    grade=member.get("grade") if isinstance(member.get("grade"), int) else None,
                )
            )
        return tuple(result)

    def has_declared_profiles(self) -> bool:
        return any(profile.professional_profile or profile.competencies for profile in self.list_profiles())


@dataclass(frozen=True)
class SourceDependencyBundle:
    sprint_snapshots: SprintSnapshotSource | None = None
    team_competencies: TeamCompetencySource | None = None
    release_timeline: ReleaseTimelineSource | None = None

    @property
    def facts(self) -> frozenset[str]:
        result: set[str] = set()
        if self.sprint_snapshots is not None:
            result.add("sprint_snapshots")
        if self.team_competencies is not None:
            result.add("team_competencies")
        if self.release_timeline is not None:
            result.add("release_timeline")
        return frozenset(result)
