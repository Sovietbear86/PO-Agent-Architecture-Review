"""Core-8 production hardening hooks.

The original composite handler intersected Pydantic objects and compared only
`task.assignee`, while silently ignoring the product slot. That is unsafe for
real AS21 data where relation hydration may return copies and identities are
represented by login/externalId/display name. Install this handler on the
production runtime only.
"""
from __future__ import annotations

from .contracts import CapabilityResult, Evidence


def _same_identity(task, expected: str) -> bool:
    wanted = expected.casefold().strip()
    return any(
        isinstance(value, str) and value.casefold().strip() == wanted
        for value in (
            getattr(task, "assignee_id", None),
            getattr(task, "assignee_login", None),
            getattr(task, "assignee", None),
        )
    )


def _same_product(task, expected: str) -> bool:
    wanted = expected.casefold().strip()
    return any(
        isinstance(value, str) and value.casefold().strip() == wanted
        for value in (getattr(task, "project_space", None),)
    ) or task.key.casefold().startswith(f"{wanted}-")


def _task_dict(task):
    return {
        "key": task.key,
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
        "status_category": task.status_category.value,
        "assignee": task.assignee,
        "assignee_id": task.assignee_id,
        "assignee_login": task.assignee_login,
        "project_space": task.project_space,
        "sprint_id": task.sprint_id,
        "release_id": task.release_id,
        "source": task.source,
    }


async def _composite(adapter, args):
    sprint_id = (args.get("sprint_id") or "").strip().upper()
    release_id = (args.get("release_id") or "").strip().upper()
    product = (args.get("product") or "").strip().upper()
    assignee = (args.get("assignee") or "").strip()
    status = (args.get("status") or "").strip()
    phrase = (args.get("phrase") or "").strip().casefold()

    # Assignee is an authoritative source selector, not merely a local
    # post-filter. Preserve it in the adapter query so ProductionTaskApiAS21Adapter
    # can use the live `/swtr-read/assignee-tasks` facade. Previously a generic
    # assignee request fell through to search_tasks("") and therefore read the
    # empty legacy/local `/api/v1/tasks` facade before filtering to zero.
    if sprint_id:
        tasks = await adapter.get_sprint_tasks(sprint_id, space=product or None)
    elif assignee:
        selectors = [f"assignee = {assignee}"]
        if product:
            selectors.append(f"project = {product}")
        tasks = await adapter.search_tasks(" AND ".join(selectors), max_results=10000)
    elif product:
        tasks = await adapter.search_tasks(f"project = {product}", max_results=10000)
    else:
        tasks = await adapter.search_tasks("", max_results=10000)

    if release_id:
        release_tasks = await adapter.get_release_tasks(release_id, space=product or None)
        release_keys = {task.key.upper() for task in release_tasks}
        tasks = [task for task in tasks if task.key.upper() in release_keys]

    # Every source selector is re-applied locally after facade reads. This keeps
    # sprint/product/release membership source-backed even if an upstream facade
    # returns a broad candidate list or echoes an unproven selector. Assignee is
    # also rechecked defensively after the live source-side filter.
    if sprint_id:
        tasks = [task for task in tasks if (task.sprint_id or "").upper() == sprint_id]
    if release_id:
        tasks = [task for task in tasks if (task.release_id or "").upper() == release_id]
    if product:
        tasks = [task for task in tasks if _same_product(task, product)]
    if assignee:
        tasks = [task for task in tasks if _same_identity(task, assignee)]

    if status:
        normalized = status.casefold().replace("-", "_").strip()
        if normalized in {"not_completed", "open_tasks", "unresolved"}:
            tasks = [task for task in tasks if not task.is_completed]
        elif normalized in {"completed", "closed_tasks", "resolved_or_closed", "closed/resolved", "closed+resolved"}:
            tasks = [task for task in tasks if task.is_completed]
        else:
            tasks = [
                task for task in tasks
                if normalized == task.status.value.casefold().replace(" ", "_")
                or normalized == task.status_category.value.casefold()
                or normalized in task.status.value.casefold().replace(" ", "_")
            ]
    if phrase:
        tasks = [
            task for task in tasks
            if phrase in task.key.casefold()
            or phrase in task.title.casefold()
            or phrase in (task.description or "").casefold()
        ]

    filters = {key: value for key, value in args.items() if value not in (None, "")}
    return CapabilityResult(
        answer=f"Составной поиск: найдено задач: {len(tasks)}.",
        data={"count": len(tasks), "filters": filters, "tasks": [_task_dict(task) for task in tasks]},
        evidence=[
            Evidence(type="task", source="as21", entity_id=task.key, label=task.title, value=task.status.value)
            for task in tasks
        ],
    )


def enable_core8_hardened_composite(runtime) -> None:
    """Route production task searches through the source-backed filter boundary."""
    registry = getattr(runtime, "capabilities", None)
    adapter = getattr(runtime, "adapter", None)
    handlers = getattr(registry, "_handlers", None)
    if adapter is None or not isinstance(handlers, dict):
        raise RuntimeError("runtime does not expose the expected capability registry")

    async def handler(args):
        return await _composite(adapter, args)

    handlers["task.search.composite"] = handler
    for capability_id in (
        "task.search",
        "task.search_assignee",
        "task.search_status",
        "task.search_sprint",
        "task.search_release",
        "task.search_product",
    ):
        if capability_id in handlers:
            handlers[capability_id] = handler
