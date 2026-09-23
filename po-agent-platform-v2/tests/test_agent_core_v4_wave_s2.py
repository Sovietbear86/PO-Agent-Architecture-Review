from __future__ import annotations

import asyncio

import pytest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from po_agent.domain.models import StatusTransition, TaskStatus
from po_agent.harness.agent_core_v4 import AgentCoreV4Runtime
from po_agent.harness.agent_core_v4_completion import SkillCompletionContract, is_skill_satisfied
from po_agent.harness.v4_plugin_registry import discover_v4_plugins
from po_agent.harness.v4_plugins.wave_s2 import (
    build_sprint_carryover,
    build_sprint_cycle_time,
    build_sprint_lead_time,
    build_sprint_predictability,
    build_sprint_risk_queue,
)


BASE = datetime(2026, 9, 1, tzinfo=timezone.utc)


def _task(
    key: str,
    *,
    completed: bool,
    created_hours: int,
    blocked: bool = False,
    due_days_ago: int = 0,
    age_days: int = 5,
):
    return SimpleNamespace(
        key=key,
        title=key,
        is_completed=completed,
        is_open=not completed,
        is_blocked=blocked,
        created_at=BASE + timedelta(hours=created_hours),
        due_date=(datetime.now(timezone.utc) - timedelta(days=due_days_ago)) if due_days_ago else None,
        age_days=age_days,
        status_raw="Need info" if blocked else ("Closed" if completed else "In progress"),
        status=SimpleNamespace(value="Closed" if completed else "In progress"),
        assignee="User",
        source_data={
            "_canonical_created_at_from_source": True,
            "_canonical_updated_at_from_source": True,
            "_canonical_deadline_from_source": bool(due_days_ago),
        },
    )


class FakeAdapter:
    def __init__(self):
        self.current = [
            _task("DMS-1", completed=True, created_hours=0),
            _task("DMS-2", completed=True, created_hours=10),
            _task("DMS-3", completed=False, created_hours=20, blocked=True, age_days=20),
            _task("DMS-4", completed=False, created_hours=30, due_days_ago=3, age_days=10),
        ]
        self.previous = [
            _task("DMS-1", completed=False, created_hours=-100),
            _task("DMS-9", completed=True, created_hours=-120),
        ]
        self.histories = {
            "DMS-1": [
                StatusTransition(from_status=TaskStatus.OPEN, to_status=TaskStatus.IN_PROGRESS, timestamp=BASE + timedelta(hours=2), from_name="Open", to_name="In progress"),
                StatusTransition(from_status=TaskStatus.IN_PROGRESS, to_status=TaskStatus.CLOSED, timestamp=BASE + timedelta(hours=26), from_name="In progress", to_name="Closed"),
            ],
            "DMS-2": [
                StatusTransition(from_status=TaskStatus.OPEN, to_status=TaskStatus.IN_PROGRESS, timestamp=BASE + timedelta(hours=12), from_name="Open", to_name="In progress"),
                StatusTransition(from_status=TaskStatus.IN_PROGRESS, to_status=TaskStatus.CLOSED, timestamp=BASE + timedelta(hours=36), from_name="In progress", to_name="Closed"),
            ],
        }

    async def get_sprint_tasks(self, sprint_id: str, space=None):
        if sprint_id == "DMS-SPRNT-3":
            return list(self.current)
        if sprint_id == "DMS-SPRNT-2":
            return list(self.previous)
        return []

    async def get_task_history(self, task_key: str):
        return list(self.histories.get(task_key, []))

    async def list_sprints(self, space: str):
        return [
            {
                "code": "DMS-SPRNT-2",
                "space": "DMS",
                "start_at": "2026-08-30T00:00:00Z",
                "finish_at": "2026-09-12T23:59:59Z",
            },
            {
                "code": "DMS-SPRNT-3",
                "space": "DMS",
                "start_at": "2026-09-13T00:00:00Z",
                "finish_at": "2026-09-27T00:00:00Z",
                "committed_count": 5,
            },
        ]


def _runtime():
    return SimpleNamespace(adapter=FakeAdapter())


def test_wave_s2_plugin_is_auto_discovered_as_five_skill_batch():
    registry = discover_v4_plugins()
    assert "builtin.wave_s2.sprint_history_risk" in registry.plugin_ids
    ids = {skill.id for skill in registry.skills()}
    assert {
        "sprint.cycle_time",
        "sprint.lead_time",
        "sprint.carryover",
        "sprint.predictability",
        "sprint.risk_queue",
    } <= ids


def test_cycle_and_lead_time_use_authoritative_history():
    runtime = _runtime()

    cycle = asyncio.run(build_sprint_cycle_time(runtime)({"sprint_id": "DMS-SPRNT-3", "space": "DMS"}))
    assert cycle.data["completed_sample"] == 2
    assert cycle.data["cycle_time_hours"]["median"] == 24.0
    assert cycle.data["formula"].startswith("terminal workflow transition")

    lead = asyncio.run(build_sprint_lead_time(runtime)({"sprint_id": "DMS-SPRNT-3", "space": "DMS"}))
    assert lead.data["completed_sample"] == 2
    assert lead.data["lead_time_hours"]["median"] == 26.0
    assert "created_at" in lead.data["formula"]


def test_carryover_uses_previous_and_current_complete_membership_intersection():
    result = asyncio.run(build_sprint_carryover(_runtime())({"sprint_id": "DMS-SPRNT-3", "space": "DMS"}))
    assert result.data["previous_sprint_id"] == "DMS-SPRNT-2"
    assert result.data["carryover"] == 1
    assert result.data["task_keys"] == ["DMS-1"]


def test_predictability_requires_and_uses_authoritative_baseline():
    result = asyncio.run(build_sprint_predictability(_runtime())({"sprint_id": "DMS-SPRNT-3", "space": "DMS"}))
    assert result.data["baseline_committed"] == 5
    assert result.data["completed"] == 2
    assert result.data["predictability"] == 0.4


def test_risk_queue_ranks_tasks_not_people():
    result = asyncio.run(build_sprint_risk_queue(_runtime())({"sprint_id": "DMS-SPRNT-3", "space": "DMS"}))
    assert result.data["count"] == 2
    assert result.data["queue"][0]["task_key"] == "DMS-3"
    assert result.data["queue"][0]["blocked"] is True
    assert result.data["queue"][1]["task_key"] == "DMS-4"
    assert "blocked first" in result.data["formula"].lower()
    assert "overdue_days desc" in result.data["formula"].lower()
    assert "age_days desc" in result.data["formula"].lower()




def test_lead_time_normalizes_source_backed_naive_created_at():
    runtime = _runtime()
    runtime.adapter.current[0].created_at = runtime.adapter.current[0].created_at.replace(tzinfo=None)
    result = asyncio.run(
        build_sprint_lead_time(runtime)({"sprint_id": "DMS-SPRNT-3", "space": "DMS"})
    )
    assert result.data["completed_sample"] == 2
    assert result.data["lead_time_hours"]["median"] == 26.0


def test_cycle_time_fails_closed_without_source_created_at():
    runtime = _runtime()
    runtime.adapter.current[0].source_data["_canonical_created_at_from_source"] = False
    with pytest.raises(Exception, match="lack source created_at"):
        asyncio.run(build_sprint_cycle_time(runtime)({"sprint_id": "DMS-SPRNT-3", "space": "DMS"}))


def test_risk_queue_does_not_treat_fallback_created_at_as_aging_fact():
    runtime = _runtime()
    task = runtime.adapter.current[2]
    task.source_data["_canonical_created_at_from_source"] = False
    result = asyncio.run(build_sprint_risk_queue(runtime)({"sprint_id": "DMS-SPRNT-3", "space": "DMS"}))
    row = next(item for item in result.data["queue"] if item["task_key"] == "DMS-3")
    assert row["age_days"] == 0
    assert not any(reason.startswith("aging:") for reason in row["reasons"])
    assert "risk_queue_created_at_source_missing" in result.warnings

def test_carryover_completion_contract_survives_compaction():
    registry = discover_v4_plugins()
    skill = {item.id: item for item in registry.skills()}["sprint.carryover"]
    requirement = skill.completion[0]
    raw = {
        "sprint_id": "DMS-SPRNT-3",
        "previous_sprint_id": "DMS-SPRNT-2",
        "carryover": 2,
        "task_keys": ["DMS-1", "DMS-2"],
    }
    compacted = AgentCoreV4Runtime._compact_data("sprint.carryover", raw)
    assert compacted["task_key_count"] == 2
    obs = SimpleNamespace(capability_id="sprint.carryover", data=compacted, arguments={}, step=1)
    contract = SkillCompletionContract(skill_id="sprint.carryover", requirements=(requirement,))
    assert is_skill_satisfied(contract, [obs])
