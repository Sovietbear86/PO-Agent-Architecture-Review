"""Live-only V4 task capability handlers.

These builders are trusted plugin artifacts, not Agent Core code. They keep the
Hermes/V4 invariant intact: source-specific task behavior is attached through the
plugin registry and can evolve without editing planner/runtime orchestration.
"""
from __future__ import annotations

from typing import Any

from po_agent.domain.models import AttachmentType

from ..contracts import CapabilityResult, Evidence


def _task_dict(task: Any) -> dict[str, Any]:
    attachments = []
    for item in getattr(task, "attachments", None) or []:
        attachments.append({"id": item.id, "name": item.name, "type": item.type.value, "size_bytes": item.size_bytes})
    return {
        "key": task.key, "id": task.id, "title": task.title, "description": task.description,
        "status": task.status.value, "status_category": task.status_category.value,
        "assignee": task.assignee, "priority": task.priority.value if task.priority else None,
        "sprint_id": task.sprint_id, "release_id": task.release_id, "source": task.source,
        "source_data": task.source_data, "attachments": attachments,
    }


async def _live_rows(runtime: Any, *, phrase: str | None = None, space: str | None = None, assignee: str | None = None) -> list[Any]:
    adapter = runtime.adapter
    params: dict[str, Any] = {"limit": 100, "max_pages": 100}
    if phrase:
        params["phrase"] = phrase
    if space:
        params["space"] = space.upper().strip()
    if assignee:
        params["assignee"] = assignee.strip()
    response = await adapter._get_resilient("/api/v1/swtr-read/task-query", params=params)
    payload = response.json()
    rows = payload.get("tasks") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise RuntimeError("live task-query returned malformed payload")
    tasks = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        mapped = adapter._map(row)
        if mapped is not None:
            tasks.append(mapped)
    return tasks


def build_task_search_text(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        phrase = str(args.get("phrase") or "").strip()
        if not phrase:
            raise ValueError("phrase is required")
        space = str(args.get("space") or "").strip() or None
        assignee = str(args.get("assignee") or args.get("reference") or "").strip() or None
        tasks = await _live_rows(runtime, phrase=phrase, space=space, assignee=assignee)
        rows = [_task_dict(task) for task in tasks]
        return CapabilityResult(answer=f"Найдено задач по фразе «{phrase}»: {len(rows)}.", data={"count": len(rows), "tasks": rows, "task_keys": [row["key"] for row in rows], "phrase": phrase, "source": "REAL_AS21"}, evidence=[Evidence(type="task", source="as21", entity_id=row["key"], label=row["title"], value=row["status"]) for row in rows])
    return execute


def build_task_search_assignee(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        reference = str(args.get("reference") or args.get("assignee") or "").strip()
        if not reference:
            raise ValueError("reference is required")
        space = str(args.get("space") or "").strip() or None
        tasks = await _live_rows(runtime, space=space, assignee=reference)
        rows = [_task_dict(task) for task in tasks]
        return CapabilityResult(answer=f"Для «{reference}» найдено задач: {len(rows)}.", data={"count": len(rows), "tasks": rows, "task_keys": [row["key"] for row in rows], "reference": reference, "space": space, "source": "REAL_AS21"}, evidence=[Evidence(type="task", source="as21", entity_id=row["key"], label=row["title"], value=row["status"]) for row in rows])
    return execute


def build_task_search_status(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        status = str(args.get("status") or "").strip().casefold()
        if not status:
            raise ValueError("status is required")
        space = str(args.get("space") or "").strip() or None
        assignee = str(args.get("assignee") or args.get("reference") or "").strip() or None
        tasks = await _live_rows(runtime, space=space, assignee=assignee)
        if status in {"not_completed", "open", "active", "открытые", "незавершенные", "незавершённые"}:
            tasks = [task for task in tasks if task.is_open]
            normalized = "not_completed"
        elif status in {"completed", "done", "closed", "закрытые", "завершенные", "завершённые"}:
            tasks = [task for task in tasks if task.is_completed]
            normalized = "completed"
        else:
            tasks = [task for task in tasks if status in task.status.value.casefold() or status in task.status_category.value.casefold()]
            normalized = status
        rows = [_task_dict(task) for task in tasks]
        return CapabilityResult(answer=f"Найдено задач по состоянию «{normalized}»: {len(rows)}.", data={"count": len(rows), "tasks": rows, "task_keys": [row["key"] for row in rows], "status": normalized, "space": space, "source": "REAL_AS21"}, evidence=[Evidence(type="task", source="as21", entity_id=row["key"], label=row["title"], value=row["status"]) for row in rows])
    return execute


def build_task_search_attachments(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        requested = str(args.get("attachment_type") or "").strip().casefold() or None
        kind = AttachmentType(requested) if requested else None
        task_key = str(args.get("task_key") or "").strip().upper() or None
        space = str(args.get("space") or "").strip() or None
        assignee = str(args.get("assignee") or args.get("reference") or "").strip() or None
        if task_key:
            task = await runtime.adapter.get_task(task_key)
            candidates = [task] if task is not None else []
        else:
            candidates = await _live_rows(runtime, space=space, assignee=assignee)
        matches: list[dict[str, Any]] = []
        evidence: list[Evidence] = []
        for task in candidates:
            items = list(getattr(task, "attachments", None) or [])
            if not items:
                items = list(await runtime.adapter.get_attachment_metadata(task.key))
            if kind is not None:
                items = [item for item in items if item.type == kind]
            if not items:
                continue
            attachments = [{"id": item.id, "name": item.name, "type": item.type.value, "size_bytes": item.size_bytes} for item in items]
            task_payload = _task_dict(task)
            task_payload["attachments"] = attachments
            matches.append({"task": task_payload, "attachments": attachments})
            evidence.extend(Evidence(type="attachment", source="as21", entity_id=task.key, label=item.name, value=item.type.value) for item in items)
        label = kind.value.upper() if kind else "вложениями"
        return CapabilityResult(answer=f"Найдено задач с {label}: {len(matches)}.", data={"attachment_type": kind.value if kind else None, "count": len(matches), "results": matches, "task_key": task_key, "space": space, "assignee": assignee, "source": "REAL_AS21"}, evidence=evidence)
    return execute
