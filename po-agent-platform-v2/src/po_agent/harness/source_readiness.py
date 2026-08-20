"""Source-readiness model for Harness skills.

A Skill can be implemented in code while unavailable for a particular runtime
source. Readiness is therefore derived from explicit source facts, never from
empty result sets or optimistic assumptions.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Literal

from po_agent.adapters.as21 import AS21Adapter

from .skill_catalog import SKILL_CATALOG, SkillCatalogEntry


class SourceFact(str, Enum):
    TASKS = "tasks"
    SPRINTS = "sprints"
    RELEASES = "releases"
    SPACES = "spaces"
    HISTORY = "history"
    ATTACHMENTS = "attachments"
    SPRINT_SNAPSHOTS = "sprint_snapshots"
    TEAM_COMPETENCIES = "team_competencies"
    RELEASE_TIMELINE = "release_timeline"


ReadinessStatus = Literal["ready", "degraded", "unavailable", "planned"]


@dataclass(frozen=True)
class SkillReadiness:
    skill_id: str
    status: ReadinessStatus
    required_facts: tuple[str, ...]
    missing_facts: tuple[str, ...]
    reason: str | None = None


@dataclass(frozen=True)
class SourceReadinessReport:
    source: str
    available_facts: tuple[str, ...]
    skills: tuple[SkillReadiness, ...]

    def by_skill(self) -> dict[str, SkillReadiness]:
        return {item.skill_id: item for item in self.skills}

    def summary(self) -> dict[str, int]:
        result = {"ready": 0, "degraded": 0, "unavailable": 0, "planned": 0}
        for item in self.skills:
            result[item.status] += 1
        return result


_ATTACHMENT_SKILLS = {
    "task-search-attachments",
    "task-search-excel",
    "task-search-pdf",
    "task-search-msg",
}

_SKILL_FACT_OVERRIDES: dict[str, tuple[SourceFact, ...]] = {
    # Product/space filtering is not equivalent to generic task availability.
    # It is ready only when the source explicitly exposes AS21 space facts.
    "task-search-product": (SourceFact.TASKS, SourceFact.SPACES),
    "sprint-current": (SourceFact.TASKS, SourceFact.SPRINTS),
    "sprint-health": (SourceFact.SPRINTS,),
    "sprint-scope": (SourceFact.SPRINTS,),
    "sprint-velocity": (SourceFact.SPRINTS,),
    "sprint-throughput": (SourceFact.SPRINTS,),
    "sprint-wip": (SourceFact.SPRINTS,),
    "sprint-predictability": (SourceFact.SPRINTS,),
    "sprint-risk-queue": (SourceFact.SPRINTS,),
    "sprint-carryover": (SourceFact.SPRINTS, SourceFact.SPRINT_SNAPSHOTS),
    "sprint-scope-change": (SourceFact.SPRINTS, SourceFact.SPRINT_SNAPSHOTS),
    "release-health": (SourceFact.RELEASES,),
    "release-scope": (SourceFact.RELEASES,),
    "release-progress": (SourceFact.RELEASES,),
    "release-blockers": (SourceFact.RELEASES,),
    "release-dependencies": (SourceFact.RELEASES,),
    "release-risk-queue": (SourceFact.RELEASES,),
    "release-forecast": (SourceFact.RELEASES, SourceFact.RELEASE_TIMELINE),
    "team-competency-match": (SourceFact.TASKS, SourceFact.TEAM_COMPETENCIES),
    "team-assignee-recommendation": (SourceFact.TASKS, SourceFact.TEAM_COMPETENCIES),
}


def required_facts(entry: SkillCatalogEntry) -> tuple[SourceFact, ...]:
    if entry.id in _ATTACHMENT_SKILLS:
        return (SourceFact.TASKS, SourceFact.ATTACHMENTS)
    if entry.id in _SKILL_FACT_OVERRIDES:
        facts = list(_SKILL_FACT_OVERRIDES[entry.id])
    elif entry.domain in {"tasks", "team", "portfolio", "po"}:
        facts = [SourceFact.TASKS]
    elif entry.domain == "sprints":
        facts = [SourceFact.SPRINTS]
    elif entry.domain == "releases":
        facts = [SourceFact.RELEASES]
    else:
        facts = []
    if entry.requires_history and SourceFact.HISTORY not in facts:
        facts.append(SourceFact.HISTORY)
    return tuple(facts)


def source_facts(adapter: AS21Adapter) -> frozenset[SourceFact]:
    raw = getattr(adapter, "source_facts", None)
    if raw is not None:
        return frozenset(SourceFact(item) for item in raw)

    name = adapter.__class__.__name__
    if name == "FakeAS21Adapter":
        return frozenset({SourceFact.TASKS, SourceFact.SPRINTS, SourceFact.RELEASES, SourceFact.HISTORY, SourceFact.ATTACHMENTS})
    if name in {"TaskApiAS21Adapter", "LegacyAS21Bridge"}:
        return frozenset({SourceFact.TASKS, SourceFact.SPRINTS, SourceFact.RELEASES})
    return frozenset({SourceFact.TASKS})


def build_source_readiness(
    adapter: AS21Adapter,
    *,
    extra_facts: Iterable[str] = (),
) -> SourceReadinessReport:
    available = set(source_facts(adapter))
    available.update(SourceFact(item) for item in extra_facts)
    available_set = frozenset(available)
    items: list[SkillReadiness] = []
    for entry in SKILL_CATALOG:
        required = required_facts(entry)
        missing = tuple(f.value for f in required if f not in available_set)
        required_names = tuple(f.value for f in required)
        if entry.status == "planned":
            status: ReadinessStatus = "planned"
            reason = "skill_not_implemented"
        elif missing:
            status = "unavailable"
            reason = "missing_source_facts"
        else:
            status = "ready"
            reason = None
        items.append(SkillReadiness(skill_id=entry.id, status=status, required_facts=required_names, missing_facts=missing, reason=reason))
    source_name = getattr(adapter, "source_name", adapter.__class__.__name__)
    return SourceReadinessReport(
        source=str(source_name),
        available_facts=tuple(sorted(f.value for f in available_set)),
        skills=tuple(items),
    )


def unavailable_implemented_skills(report: SourceReadinessReport) -> tuple[SkillReadiness, ...]:
    return tuple(item for item in report.skills if item.status == "unavailable")
