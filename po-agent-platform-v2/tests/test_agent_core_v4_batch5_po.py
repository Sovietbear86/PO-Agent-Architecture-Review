from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from po_agent.harness.agent_core_v4 import SkillCatalogV4, V4NeedsClarification
from po_agent.harness.v4_plugin_registry import discover_v4_plugins
from po_agent.harness.v4_plugins.wave_batch5_po import (
    build_po_attention_queue,
    build_po_daily_brief,
    build_po_local_task_draft,
    build_po_reminder_draft,
    build_po_status_report,
)


def _status(value: str):
    return SimpleNamespace(value=value)


def _category(value: str):
    return SimpleNamespace(value=value)


def _priority(value: str | None):
    return SimpleNamespace(value=value) if value else None


def _task(
    key: str,
    *,
    title: str | None = None,
    space: str | None = None,
    sprint_id: str | None = None,
    completed: bool = False,
    blocked: bool = False,
    assignee: str | None = "alice",
    priority: str | None = None,
    age_days: int = 1,
):
    return SimpleNamespace(
        key=key,
        title=title or key,
        project_space=space or key.split("-", 1)[0],
        sprint_id=sprint_id,
        release_id=None,
        is_completed=completed,
        is_blocked=blocked,
        assignee=assignee,
        assignee_login=assignee,
        assignee_id=assignee,
        priority=_priority(priority),
        age_days=age_days,
        status_raw="Closed" if completed else ("Blocked" if blocked else "In progress"),
        status=_status("Closed" if completed else ("Blocked" if blocked else "In progress")),
        status_category=_category("completed" if completed else "active_work"),
    )


class FakeAdapter:
    def __init__(self):
        self.current = {
            "DMS": "DMS-SPRNT-3",
            "OLP": "OLP-SPRNT-8",
            "WMB": None,
            "STS": None,
            "CRPV": None,
        }
        self.sprints = {
            "DMS-SPRNT-3": [
                _task("DMS-1", space="DMS", sprint_id="DMS-SPRNT-3", blocked=True, age_days=20),
                _task("DMS-2", space="DMS", sprint_id="DMS-SPRNT-3", completed=True),
                _task("DMS-3", space="DMS", sprint_id="DMS-SPRNT-3", assignee=None, priority="Critical"),
            ],
            "OLP-SPRNT-8": [
                _task("OLP-1", space="OLP", sprint_id="OLP-SPRNT-8", age_days=8),
            ],
        }
        self.by_key = {
            task.key: task
            for tasks in self.sprints.values()
            for task in tasks
        }
        self.source_calls = []

    async def get_current_sprint_id(self, space: str):
        self.source_calls.append(("current", space))
        return self.current.get(space)

    async def get_sprint_tasks(self, sprint_id: str, space: str | None = None):
        self.source_calls.append(("sprint", space, sprint_id))
        return list(self.sprints.get(sprint_id, []))

    async def get_task(self, key: str):
        self.source_calls.append(("task", key))
        return self.by_key.get(key)


def _runtime(adapter=None):
    adapter = adapter or FakeAdapter()
    registry = discover_v4_plugins()
    catalog = SkillCatalogV4(registry.skills(), registry.capability_specs())
    return SimpleNamespace(adapter=adapter, catalog=catalog, plugin_ids=registry.plugin_ids), adapter, registry


def test_batch5_po_plugin_is_registry_discovered():
    _runtime_obj, _adapter, registry = _runtime()
    assert "builtin.batch5.po_workflow" in registry.plugin_ids
    ids = {skill.id for skill in registry.skills()}
    assert {
        "po.attention_queue",
        "po.daily_brief",
        "po.status_report",
        "po.reminder_draft",
        "po.local_task_draft",
    } <= ids


def test_attention_queue_is_bounded_to_current_sprints_and_task_scored():
    runtime, adapter, _registry = _runtime()
    result = asyncio.run(build_po_attention_queue(runtime)({}))

    assert result.data["scope"] == "approved_product_spaces_current_sprints"
    assert result.data["count"] == 3
    assert [row["task"]["key"] for row in result.data["queue"]] == ["DMS-1", "DMS-3", "OLP-1"]
    assert result.data["queue"][0]["attention_score"] == 70
    assert result.data["queue"][1]["attention_score"] == 45

    assert all(call[0] in {"current", "sprint"} for call in adapter.source_calls)
    assert len([call for call in adapter.source_calls if call[0] == "current"]) == 5


def test_daily_brief_and_status_report_preserve_explicit_no_current_sprint_states():
    runtime, _adapter, _registry = _runtime()

    brief = asyncio.run(build_po_daily_brief(runtime)({}))
    assert brief.data["active"] == 3
    assert brief.data["blocked"] == 1
    assert brief.data["unassigned"] == 1
    assert brief.data["completed"] == 1
    assert brief.data["attention_count"] == 3

    report = asyncio.run(build_po_status_report(runtime)({}))
    assert report.data["total"] == 4
    assert report.data["completed"] == 1
    assert report.data["active"] == 3
    assert report.data["blocked"] == 1
    assert report.data["by_product"]["DMS"]["total"] == 3
    assert report.data["by_product"]["OLP"]["total"] == 1
    assert report.data["by_product"]["WMB"]["state"] == "NO_CURRENT_SPRINT"
    assert report.data["by_product"]["WMB"]["total"] is None


def test_reminder_draft_requires_explicit_task_and_never_writes():
    runtime, adapter, _registry = _runtime()

    with pytest.raises(V4NeedsClarification, match="Укажите задачу"):
        asyncio.run(build_po_reminder_draft(runtime)({}))

    result = asyncio.run(build_po_reminder_draft(runtime)({"task_key": "DMS-1"}))
    assert result.data["draft_created"] is True
    assert result.data["write_performed"] is False
    assert result.data["requires_approval_for_send"] is True
    assert result.data["task"]["key"] == "DMS-1"
    assert adapter.source_calls[-1] == ("task", "DMS-1")


def test_local_task_draft_supports_source_task_or_user_subject_without_write():
    runtime, adapter, _registry = _runtime()

    source = asyncio.run(build_po_local_task_draft(runtime)({"task_key": "DMS-2"}))
    assert source.data["draft_created"] is True
    assert source.data["write_performed"] is False
    assert source.data["draft"]["source_task_key"] == "DMS-2"
    assert source.data["source"] == "REAL_AS21"

    before = len(adapter.source_calls)
    user_only = asyncio.run(build_po_local_task_draft(runtime)({"subject": "Подготовить one-pager"}))
    assert user_only.data["draft_created"] is True
    assert user_only.data["write_performed"] is False
    assert user_only.data["source"] == "USER_INPUT_ONLY"
    assert len(adapter.source_calls) == before

    with pytest.raises(V4NeedsClarification, match="Укажите тему"):
        asyncio.run(build_po_local_task_draft(runtime)({}))


def test_batch5_completion_contracts_are_scalar_zero_safe():
    _runtime_obj, _adapter, registry = _runtime()
    skills = {skill.id: skill for skill in registry.skills()}

    assert skills["po.attention_queue"].completion[0].data_keys == ("count", "scoring_version")
    assert skills["po.daily_brief"].completion[0].data_keys == ("active", "blocked", "attention_count")
    assert skills["po.status_report"].completion[0].data_keys == ("total", "by_product")
    assert skills["po.reminder_draft"].completion[0].data_keys == ("draft_created", "write_performed")
    assert skills["po.local_task_draft"].completion[0].data_keys == ("draft_created", "write_performed")


def test_local_task_draft_contract_owns_source_validation():
    _runtime_obj, _adapter, registry = _runtime()
    skill = next(skill for skill in registry.skills() if skill.id == "po.local_task_draft")
    detail = "\n".join(skill.procedure)

    assert "po.local_task_draft" in detail
    assert "Do NOT load or call task.lookup" in detail
    assert skill.capabilities == ("po.local_task_draft",)
