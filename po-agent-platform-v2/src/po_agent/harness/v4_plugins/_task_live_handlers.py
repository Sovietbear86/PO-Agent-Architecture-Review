"""Live-only V4 task capability handlers.

These builders are trusted plugin artifacts, not Agent Core code. They keep the
Hermes/V4 invariant intact: source-specific task behavior is attached through the
plugin registry and can evolve without editing planner/runtime orchestration.
"""
from __future__ import annotations

import asyncio
from typing import Any

from po_agent.adapters.task_api import AS21SourceUnavailable
from po_agent.domain.models import AttachmentType

from ..contracts import CapabilityResult, Evidence


def _attachment_dict(item: Any) -> dict[str, Any]:
    return {"id": item.id, "name": item.name, "type": item.type.value, "size_bytes": item.size_bytes}


def _task_dict(task: Any) -> dict[str, Any]:
    attachments = [_attachment_dict(item) for item in (getattr(task, "attachments", None) or [])]
    return {
        "key": task.key,
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
        "status_category": task.status_category.value,
        "assignee": task.assignee,
        "assignee_id": getattr(task, "assignee_id", None),
        "assignee_login": getattr(task, "assignee_login", None),
        "priority": task.priority.value if task.priority else None,
        "project_space": getattr(task, "project_space", None),
        "sprint_id": task.sprint_id,
        "release_id": task.release_id,
        "source": task.source,
        "source_data": task.source_data,
        "attachments": attachments,
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


async def _resolve_assignee_identity(runtime: Any, reference: str, *, space: str | None = None) -> str:
    """Resolve any natural person reference through the generic governed resolver.

    The configured team directory is only an optional fast disambiguation hint
    inside ``member.resolve``. It MUST NOT define the searchable population. A
    person outside the configured team is resolved against REAL AS21 in exactly
    the same contract. Ambiguous identities propagate typed clarification instead
    of being collapsed into a generic source error.
    """
    resolver = getattr(runtime, "_member_resolve", None)
    if resolver is None:
        raise RuntimeError("runtime does not expose governed member resolver")
    args = {"reference": reference}
    if space:
        args["space"] = space
    result = await resolver(args)
    data = getattr(result, "data", {}) or {}
    external_id = str(data.get("external_id") or data.get("member_login") or "").strip()
    if not external_id:
        raise RuntimeError("member resolver returned no canonical identity")
    return external_id


def build_task_lookup(runtime: Any):
    """Exact live lookup with canonical identity + attachments in the observation."""
    async def execute(args: dict[str, str]) -> CapabilityResult:
        task_key = str(args.get("task_key") or "").strip().upper()
        if not task_key:
            raise ValueError("task_key is required")
        task = await runtime.adapter.get_task(task_key)
        if task is None:
            return CapabilityResult(
                answer=f"Задача {task_key} не найдена в REAL AS21.",
                data={"task_key": task_key, "task": None, "source": "REAL_AS21"},
                evidence=[],
                warnings=["task_not_found"],
            )
        row = _task_dict(task)
        attachment_count = len(row["attachments"])
        attachment_suffix = f" Вложений: {attachment_count}." if attachment_count else " Вложений: 0."
        return CapabilityResult(
            answer=(
                f"{task.key} — {task.title}. Статус: {task.status.value}."
                + (f" Исполнитель: {task.assignee}." if task.assignee else "")
                + attachment_suffix
            ),
            data={
                "task_key": task.key,
                "task": row,
                "assignee_login": getattr(task, "assignee_login", None),
                "assignee_id": getattr(task, "assignee_id", None),
                "attachment_count": attachment_count,
                "attachments": row["attachments"],
                "source": "REAL_AS21",
            },
            evidence=[
                Evidence(type="task", source="as21", entity_id=task.key, label=task.title, value=task.status.value),
                *[
                    Evidence(type="attachment", source="as21", entity_id=task.key, label=item["name"], value=item["type"])
                    for item in row["attachments"]
                ],
            ],
        )
    return execute


def build_task_search_text(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        phrase = str(args.get("phrase") or "").strip()
        if not phrase:
            raise ValueError("phrase is required")
        space = str(args.get("space") or "").strip() or None
        assignee = str(args.get("assignee") or args.get("reference") or "").strip() or None
        tasks = await _live_rows(runtime, phrase=phrase, space=space, assignee=assignee)
        rows = [_task_dict(task) for task in tasks]
        return CapabilityResult(
            answer=f"Найдено задач по фразе «{phrase}»: {len(rows)}.",
            data={"count": len(rows), "tasks": rows, "task_keys": [row["key"] for row in rows], "phrase": phrase, "source": "REAL_AS21"},
            evidence=[Evidence(type="task", source="as21", entity_id=row["key"], label=row["title"], value=row["status"]) for row in rows],
        )
    return execute


def build_task_search_assignee(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        reference = str(args.get("reference") or args.get("assignee") or "").strip()
        if not reference:
            raise ValueError("reference is required")
        space = str(args.get("space") or "").strip().upper() or None

        # Restore the generic identity contract that existed before the A194 fast
        # path optimization: resolve any human reference first, then search only by
        # the source-confirmed canonical identity. Team membership is never a
        # population filter and ambiguity remains a clarification, not source error.
        canonical_identity = await _resolve_assignee_identity(runtime, reference, space=space)
        query = f'assignee = "{canonical_identity}"'
        if space:
            query += f' AND project = "{space}"'
        tasks = list(await runtime.adapter.search_tasks(query, max_results=10000))
        rows = [_task_dict(task) for task in tasks]
        return CapabilityResult(
            answer=f"Для «{reference}» найдено задач: {len(rows)}.",
            data={
                "count": len(rows),
                "tasks": rows,
                "task_keys": [row["key"] for row in rows],
                "reference": reference,
                "source_reference": canonical_identity,
                "member_login": canonical_identity,
                "space": space,
                "source": "REAL_AS21",
            },
            evidence=[Evidence(type="task", source="as21", entity_id=row["key"], label=row["title"], value=row["status"]) for row in rows],
        )
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
        return CapabilityResult(
            answer=f"Найдено задач по состоянию «{normalized}»: {len(rows)}.",
            data={"count": len(rows), "tasks": rows, "task_keys": [row["key"] for row in rows], "status": normalized, "space": space, "source": "REAL_AS21"},
            evidence=[Evidence(type="task", source="as21", entity_id=row["key"], label=row["title"], value=row["status"]) for row in rows],
        )
    return execute


def build_task_search_attachments(runtime: Any):
    """Search attachments without an unbounded N+1 fan-out.

    Exact-task and bounded person-scoped requests remain fully supported. A very
    broad space-only scan is explicitly SOURCE_UNAVAILABLE until AS21 exposes a
    batch/file-search contract; it must not launch thousands of per-task calls.
    """
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

        # A196 D2: 2k+ WMB tasks caused a 300s N+1 timeout. Until the source
        # offers a batch attachment search, fail closed before fan-out instead of
        # pretending a partial scan is complete.
        max_fanout = 250
        if len(candidates) > max_fanout and not task_key:
            raise AS21SourceUnavailable(
                f"REAL AS21 has no certified batch attachment-search surface for {len(candidates)} candidate tasks; "
                f"bounded limit is {max_fanout}"
            )

        semaphore = asyncio.Semaphore(12)

        async def files_for(task: Any):
            items = list(getattr(task, "attachments", None) or [])
            if items:
                return task, items
            async with semaphore:
                return task, list(await runtime.adapter.get_attachment_metadata(task.key))

        resolved = await asyncio.gather(*(files_for(task) for task in candidates))
        matches: list[dict[str, Any]] = []
        evidence: list[Evidence] = []
        for task, items in resolved:
            if kind is not None:
                items = [item for item in items if item.type == kind]
            if not items:
                continue
            attachments = [_attachment_dict(item) for item in items]
            task_payload = _task_dict(task)
            task_payload["attachments"] = attachments
            matches.append({"task": task_payload, "attachments": attachments})
            evidence.extend(
                Evidence(type="attachment", source="as21", entity_id=task.key, label=item.name, value=item.type.value)
                for item in items
            )
        label = kind.value.upper() if kind else "вложениями"
        return CapabilityResult(
            answer=f"Найдено задач с {label}: {len(matches)}.",
            data={"attachment_type": kind.value if kind else None, "count": len(matches), "results": matches, "task_key": task_key, "space": space, "assignee": assignee, "source": "REAL_AS21"},
            evidence=evidence,
        )
    return execute


def build_task_aging(runtime: Any):
    """Calculate aging only over an explicitly bounded live task collection."""
    async def execute(args: dict[str, str]) -> CapabilityResult:
        threshold_days = int(args.get("threshold_days") or "7")
        if threshold_days < 0:
            raise ValueError("threshold_days must be >= 0")
        space = str(args.get("space") or "").strip().upper() or None
        assignee = str(args.get("assignee") or args.get("reference") or "").strip() or None
        if not space and not assignee:
            raise AS21SourceUnavailable("task.aging requires a bounded space or assignee on the live source path")
        tasks = await _live_rows(runtime, space=space, assignee=assignee)
        with_source_age = [
            task for task in tasks
            if bool((getattr(task, "source_data", None) or {}).get("_canonical_created_at_from_source"))
        ]
        if tasks and not with_source_age:
            raise AS21SourceUnavailable("REAL AS21 task rows do not expose source creation timestamps required for task.aging")
        active = [task for task in with_source_age if task.is_open and task.age_days >= threshold_days]
        active.sort(key=lambda task: task.age_days, reverse=True)
        rows = [
            {
                "key": task.key,
                "title": task.title,
                "status": task.status.value,
                "assignee": task.assignee,
                "age_days": task.age_days,
            }
            for task in active
        ]
        return CapabilityResult(
            answer=f"Задач старше {threshold_days} дней: {len(rows)}.",
            data={
                "threshold_days": threshold_days,
                "count": len(rows),
                "tasks": rows,
                "space": space,
                "assignee": assignee,
                "source": "REAL_AS21",
            },
            evidence=[
                Evidence(type="task_age", source="as21", entity_id=row["key"], label=row["title"], value=row["age_days"])
                for row in rows
            ],
        )
    return execute


def build_task_similar(runtime: Any):
    """Compare one task only with the bounded live corpus of its own space."""
    async def execute(args: dict[str, str]) -> CapabilityResult:
        import re

        task_key = str(args.get("task_key") or "").strip().upper()
        if not task_key:
            raise ValueError("task_key is required")
        space = task_key.split("-", 1)[0] if "-" in task_key else ""
        if not space:
            raise ValueError("task_key must contain a product-space prefix")

        # Resolve the source task through the live bounded task-query path rather
        # than tenant-wide adapter.search_tasks("").
        exact = await _live_rows(runtime, phrase=task_key, space=space)
        source_task = next((task for task in exact if task.key.upper() == task_key), None)
        if source_task is None:
            return CapabilityResult(
                answer=f"Задача {task_key} не найдена в REAL AS21.",
                data={"task_key": task_key, "found": False, "matches": [], "method": "token_jaccard_v1", "source": "REAL_AS21"},
                evidence=[],
            )

        candidates = await _live_rows(runtime, space=space)
        stop = {"для", "the", "and", "или", "это", "with", "from", "create", "add", "user", "task"}

        def tokens(text: str) -> set[str]:
            return {token for token in re.findall(r"[A-Za-zА-Яа-я0-9]{3,}", text.casefold()) if token not in stop}

        source_tokens = tokens(f"{source_task.title} {source_task.description or ''}")
        rows: list[dict[str, Any]] = []
        for other in candidates:
            if other.key.upper() == task_key:
                continue
            other_tokens = tokens(f"{other.title} {other.description or ''}")
            union = source_tokens | other_tokens
            similarity = round(len(source_tokens & other_tokens) / len(union), 3) if union else 0.0
            if similarity <= 0:
                continue
            rows.append({"key": other.key, "title": other.title, "similarity": similarity, "status": other.status.value})
        rows.sort(key=lambda item: item["similarity"], reverse=True)
        rows = rows[:5]
        return CapabilityResult(
            answer=f"Для {task_key} найдено похожих задач: {len(rows)}.",
            data={"task_key": task_key, "matches": rows, "method": "token_jaccard_v1", "space": space, "source": "REAL_AS21"},
            evidence=[
                Evidence(type="task", source="as21", entity_id=source_task.key, label=source_task.title, value=source_task.status.value),
                *[
                    Evidence(type="similar_task", source="as21+deterministic", entity_id=item["key"], label=item["title"], value=item["similarity"])
                    for item in rows
                ],
            ],
        )
    return execute
