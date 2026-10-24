"""Deterministic capabilities invoked from grounded semantic frames."""
from __future__ import annotations

from po_agent.adapters.as21 import AS21Adapter

from .contracts import CapabilityResult, Evidence


class StructuredTaskSearchCapability:
    """Apply multiple grounded filters in one deterministic task search.

    This is the execution target for semantic queries such as
    'open tasks of member X in sprint Y'. Natural-language interpretation does
    not happen here; all values must already be grounded or clarified.
    """

    def __init__(self, adapter: AS21Adapter) -> None:
        self.adapter = adapter

    async def execute(self, args: dict[str, str]) -> CapabilityResult:
        tasks = await self.adapter.search_tasks("")
        assignee = (args.get("assignee") or "").strip()
        sprint_id = (args.get("sprint_id") or "").strip().upper()
        release_id = (args.get("release_id") or "").strip().upper()
        product = (args.get("product") or "").strip().upper()
        status = (args.get("status") or "").strip()
        phrase = (args.get("phrase") or "").strip().casefold()

        if assignee:
            tasks = [t for t in tasks if t.assignee and t.assignee.casefold() == assignee.casefold()]
        if sprint_id:
            tasks = [t for t in tasks if (t.sprint_id or "").upper() == sprint_id]
        if release_id:
            tasks = [t for t in tasks if (t.release_id or "").upper() == release_id]
        if product:
            tasks = [t for t in tasks if t.key.upper().startswith(product + "-")]
        if status:
            normalized = status.casefold().replace("_", " ").strip()
            if normalized in {"not completed", "not_completed", "all unresolved tasks", "все незавершенные", "все незавершённые"}:
                tasks = [t for t in tasks if not t.is_completed]
            else:
                accepted = {x.strip().casefold() for x in status.replace(";", ",").split(",") if x.strip()}
                tasks = [t for t in tasks if t.status.value.casefold() in accepted or t.status_category.value.casefold() in accepted]
        if phrase:
            tasks = [t for t in tasks if phrase in t.key.casefold() or phrase in t.title.casefold() or phrase in (t.description or "").casefold()]

        data = {
            "count": len(tasks),
            "filters": {k: v for k, v in {
                "assignee": assignee or None,
                "sprint_id": sprint_id or None,
                "release_id": release_id or None,
                "product": product or None,
                "status": status or None,
                "phrase": args.get("phrase") or None,
            }.items() if v is not None},
            "tasks": [
                {
                    "key": t.key,
                    "title": t.title,
                    "status": t.status.value,
                    "status_category": t.status_category.value,
                    "assignee": t.assignee,
                    "sprint_id": t.sprint_id,
                    "release_id": t.release_id,
                    "priority": t.priority.value if t.priority else None,
                }
                for t in tasks
            ],
        }
        evidence = [Evidence(type="task", source="as21", entity_id=t.key, label=t.title, value=t.status.value) for t in tasks]
        return CapabilityResult(answer=f"Найдено задач: {len(tasks)}.", data=data, evidence=evidence)
