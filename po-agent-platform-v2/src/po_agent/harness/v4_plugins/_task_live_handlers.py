"""Live-only V4 task capability handlers.

These builders are trusted plugin artifacts, not Agent Core code. They keep the
Hermes/V4 invariant intact: source-specific task behavior is attached through the
plugin registry and can evolve without editing planner/runtime orchestration.
"""
from __future__ import annotations

import asyncio
import re
from datetime import datetime, time as dt_time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from po_agent.adapters.task_api import AS21SourceUnavailable
from po_agent.config.real_team import get_all_member_logins
from po_agent.domain.models import AttachmentType, TaskStatus, normalize_task_status

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
        "status_raw": getattr(task, "status_raw", None),
        "status_type": getattr(task, "status_type", None),
        "assignee": task.assignee,
        "assignee_id": getattr(task, "assignee_id", None),
        "assignee_login": getattr(task, "assignee_login", None),
        "priority": task.priority.value if task.priority else None,
        "project_space": getattr(task, "project_space", None),
        "sprint_id": task.sprint_id,
        "release_id": task.release_id,
        "task_type_code": getattr(task, "task_type_code", None),
        "task_type_name": getattr(task, "task_type_name", None),
        "parent_key": getattr(task, "parent_key", None),
        "epic_key": getattr(task, "epic_key", None),
        "related_keys": list(getattr(task, "related_keys", None) or []),
        "source": task.source,
        "created_at": task.created_at.isoformat() if getattr(task, "created_at", None) else None,
        "source_data": task.source_data,
        "attachments": attachments,
    }


async def _live_query(runtime: Any, *, phrase: str | None = None, space: str | None = None, assignee: str | None = None) -> tuple[list[Any], dict[str, Any]]:
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
    metadata = {
        "completed_spaces": payload.get("completed_spaces") if isinstance(payload, dict) else None,
        "incomplete_spaces": payload.get("incomplete_spaces") if isinstance(payload, dict) else None,
        "source_complete": payload.get("source_complete", True) if isinstance(payload, dict) else True,
    }
    return tasks, metadata


async def _live_rows(runtime: Any, *, phrase: str | None = None, space: str | None = None, assignee: str | None = None) -> list[Any]:
    tasks, _ = await _live_query(runtime, phrase=phrase, space=space, assignee=assignee)
    return tasks


async def _live_assignee_rows(runtime: Any, *, assignee: str, space: str | None = None) -> list[Any]:
    adapter = runtime.adapter
    params: dict[str, Any] = {"assignee": assignee, "limit": 100, "max_pages": 100}
    if space:
        params["space"] = space.upper().strip()
    response = await adapter._get_resilient("/api/v1/swtr-read/assignee-tasks", params=params)
    payload = response.json()
    rows = payload.get("tasks") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise RuntimeError("live assignee-tasks returned malformed payload")
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


def _matches_requested_status(runtime: Any, task: Any, raw_status: str) -> bool:
    """Apply the same typed status semantics used by generic task.search.

    This keeps specialized collection capabilities composable: adding an
    attachment/file constraint must not force the planner to drop an already
    requested status constraint.
    """
    raw = str(raw_status or "").strip()
    if not raw:
        return True
    normalize = getattr(runtime, "_safe_status", None)
    normalized = str(normalize(raw) if callable(normalize) else raw).strip().casefold()
    if normalized == "not_completed":
        return bool(getattr(task, "is_open", False))
    if normalized == "completed":
        return bool(getattr(task, "is_completed", False))
    if normalized == "blocked":
        return bool(getattr(task, "is_blocked", False))

    requested_domain_status = normalize_task_status(raw)
    if requested_domain_status == TaskStatus.IN_PROGRESS:
        return getattr(task, "status", None) == TaskStatus.IN_PROGRESS
    if normalized == "progress":
        return str(getattr(task, "status_type", "") or "").strip().casefold() == "progress"

    requested = raw.casefold()
    return any(
        requested in str(value or "").casefold()
        for value in (
            getattr(task, "status_raw", None),
            getattr(task, "status_type", None),
            getattr(getattr(task, "status", None), "value", None),
            getattr(getattr(task, "status_category", None), "value", None),
        )
    )


async def _source_assignee_from_args(
    runtime: Any,
    args: dict[str, str],
    *,
    space: str | None = None,
) -> tuple[str | None, str | None]:
    """Return (user_reference, canonical_source_identity) for any person scope.

    All plugin-owned person-scoped task capabilities share this seam. A natural
    name, inflected form or even a planner-provided assignee token is confirmed
    through the generic governed member resolver before it reaches a source
    route that expects a canonical identity. Team membership is never a
    population boundary.
    """
    reference = str(args.get("reference") or args.get("assignee") or "").strip() or None
    if not reference:
        return None, None
    return reference, await _resolve_assignee_identity(runtime, reference, space=space)


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
        assignee, source_assignee = await _source_assignee_from_args(runtime, args, space=space)
        tasks, source_meta = await _live_query(runtime, phrase=phrase, space=space, assignee=source_assignee)
        rows = [_task_dict(task) for task in tasks]
        incomplete_spaces = list(source_meta.get("incomplete_spaces") or [])
        source_complete = bool(source_meta.get("source_complete", not incomplete_spaces))
        answer = f"Найдено задач по фразе «{phrase}»: {len(rows)}."
        if incomplete_spaces:
            answer += " Результат частичный: часть пространств недоступна из-за ограничения источника."
        return CapabilityResult(
            answer=answer,
            data={
                "count": len(rows),
                "tasks": rows,
                "task_keys": [row["key"] for row in rows],
                "phrase": phrase,
                "assignee": assignee,
                "source_assignee": source_assignee,
                "source": "REAL_AS21",
                "source_complete": source_complete,
                "completed_spaces": source_meta.get("completed_spaces") or [],
                "incomplete_spaces": incomplete_spaces,
            },
            evidence=[Evidence(type="task", source="as21", entity_id=row["key"], label=row["title"], value=row["status"]) for row in rows],
            warnings=["partial_source_spaces"] if incomplete_spaces else [],
        )
    return execute


_MOSCOW_TZ = ZoneInfo("Europe/Moscow")


def _parse_human_created_period(raw: str, *, now: datetime | None = None) -> tuple[datetime, datetime, str]:
    """Parse a bounded human creation period without turning text into source truth.

    Supported forms are generic calendar expressions, not task/entity phrases:
    - "последние N дней" / "last N days";
    - explicit inclusive ranges containing two DD.MM.YYYY or YYYY-MM-DD dates.
    """
    text = str(raw or "").strip()
    if not text:
        raise ValueError("created_period is required")

    current = now.astimezone(_MOSCOW_TZ) if now is not None else datetime.now(_MOSCOW_TZ)
    relative = re.search(r"(?:последн(?:ие|их)\s+|last\s+)(\d{1,3})\s*(?:дн(?:я|ей)?|days?)", text, flags=re.I)
    if relative:
        days = int(relative.group(1))
        if days < 1 or days > 366:
            raise ValueError("created_period days must be between 1 and 366")
        start_date = current.date() - timedelta(days=days - 1)
        start = datetime.combine(start_date, dt_time.min, tzinfo=_MOSCOW_TZ)
        return start, current, f"last_{days}_calendar_days"

    date_tokens = re.findall(r"\b(?:\d{2}\.\d{2}\.\d{4}|\d{4}-\d{2}-\d{2})\b", text)
    if len(date_tokens) == 2:
        def parse_one(value: str):
            fmt = "%d.%m.%Y" if "." in value else "%Y-%m-%d"
            return datetime.strptime(value, fmt).date()

        start_date = parse_one(date_tokens[0])
        end_date = parse_one(date_tokens[1])
        if end_date < start_date:
            raise ValueError("created_period end precedes start")
        if (end_date - start_date).days > 366:
            raise ValueError("created_period exceeds 366 days")
        start = datetime.combine(start_date, dt_time.min, tzinfo=_MOSCOW_TZ)
        end = datetime.combine(end_date, dt_time.max, tzinfo=_MOSCOW_TZ)
        return start, end, "explicit_inclusive_dates"

    raise ValueError(
        "created_period must contain 'последние N дней'/'last N days' "
        "or two explicit dates (DD.MM.YYYY or YYYY-MM-DD)"
    )


def _source_created_at(task: Any) -> datetime | None:
    source_data = getattr(task, "source_data", None)
    if not isinstance(source_data, dict) or source_data.get("_canonical_created_at_from_source") is not True:
        return None
    value = getattr(task, "created_at", None)
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=_MOSCOW_TZ)
    return value.astimezone(_MOSCOW_TZ)


def build_task_search_created(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        reference = str(args.get("reference") or args.get("assignee") or "").strip() or None
        space = str(args.get("space") or "").strip().upper() or None
        raw_period = str(args.get("created_period") or "").strip()
        start, end, period_kind = _parse_human_created_period(raw_period)

        source_assignee = None
        if reference:
            source_assignee = await _resolve_assignee_identity(runtime, reference, space=space)

        if not space and not source_assignee:
            raise AS21SourceUnavailable(
                "task.search_created requires a bounded person or product space"
            )

        tasks = await _live_rows(runtime, space=space, assignee=source_assignee)
        missing_created = [task.key for task in tasks if _source_created_at(task) is None]
        if missing_created:
            raise AS21SourceUnavailable(
                "REAL AS21 task creation timestamps are incomplete for the bounded corpus; "
                f"cannot prove an exact created-period result ({len(missing_created)} rows missing created_at)"
            )

        matches = [
            task for task in tasks
            if start <= _source_created_at(task) <= end
        ]

        raw_status = str(args.get("status") or "").strip()
        if raw_status:
            matches = [
                task for task in matches
                if _matches_requested_status(runtime, task, raw_status)
            ]

        rows = [_task_dict(task) for task in matches]
        status_suffix = f" со статусом «{raw_status}»" if raw_status else ""
        return CapabilityResult(
            answer=(
                f"Найдено задач, созданных за период «{raw_period}»{status_suffix}: {len(rows)}."
            ),
            data={
                "count": len(rows),
                "tasks": rows,
                "task_keys": [row["key"] for row in rows],
                "reference": reference,
                "source_assignee": source_assignee,
                "space": space,
                "status": raw_status or None,
                "created_period": raw_period,
                "created_from": start.isoformat(),
                "created_to": end.isoformat(),
                "period_kind": period_kind,
                "source": "REAL_AS21",
            },
            evidence=[
                Evidence(
                    type="task",
                    source="as21",
                    entity_id=row["key"],
                    label=row["title"],
                    value=row["created_at"],
                )
                for row in rows
            ],
        )

    return execute



def _task_type_pair(task: Any) -> tuple[str | None, str | None]:
    code = getattr(task, "task_type_code", None)
    name = getattr(task, "task_type_name", None)
    source_data = getattr(task, "source_data", None)
    if (not code and not name) and isinstance(source_data, dict):
        suit = source_data.get("swtr_suit")
        if isinstance(suit, dict):
            code = suit.get("code") or suit.get("id")
            name = suit.get("name") or suit.get("title")
        elif isinstance(suit, str):
            code = suit
            name = suit
    code_text = str(code).strip() if code not in (None, "") else None
    name_text = str(name).strip() if name not in (None, "") else None
    return code_text, name_text


_TYPE_ALIASES = {
    "bug": {"bug", "bugs", "баг", "баги"},
    "defect": {"defect", "defects", "дефект", "дефекты"},
    "story": {"story", "stories", "user story", "история", "истории"},
    "epic": {"epic", "epics", "эпик", "эпики"},
    "task": {"task", "tasks", "задача", "задачи"},
}


def _normalized_type_tokens(value: str) -> set[str]:
    raw = re.sub(r"[_\-]+", " ", str(value or "").casefold()).strip()
    tokens = {raw} if raw else set()
    for canonical, aliases in _TYPE_ALIASES.items():
        if raw == canonical or raw in aliases:
            tokens.add(canonical)
            tokens.update(aliases)
    return tokens


def _task_type_matches(task: Any, requested: str) -> bool:
    wanted = _normalized_type_tokens(requested)
    if not wanted:
        return True
    code, name = _task_type_pair(task)
    source_values = {
        re.sub(r"[_\-]+", " ", str(value).casefold()).strip()
        for value in (code, name)
        if value
    }
    expanded: set[str] = set(source_values)
    for source_value in list(source_values):
        for canonical, aliases in _TYPE_ALIASES.items():
            if source_value == canonical or source_value in aliases:
                expanded.add(canonical)
                expanded.update(aliases)
    return bool(wanted & expanded)


def _task_matches_identity(task: Any, canonical_identity: str) -> bool:
    wanted = canonical_identity.casefold().strip()
    values = {
        str(value).casefold().strip()
        for value in (
            getattr(task, "assignee", None),
            getattr(task, "assignee_login", None),
            getattr(task, "assignee_id", None),
        )
        if value and str(value).strip()
    }
    return wanted in values


async def _bounded_composable_tasks(
    runtime: Any,
    args: dict[str, str],
) -> tuple[list[Any], dict[str, Any]]:
    """Build one source-bounded collection for composable plugin skills."""
    space = str(args.get("space") or "").strip().upper() or None
    reference = str(args.get("reference") or args.get("assignee") or "").strip() or None
    sprint_id = str(args.get("sprint_id") or "").strip().upper() or None
    phrase = str(args.get("phrase") or "").strip() or None

    source_assignee = None
    if reference:
        source_assignee = await _resolve_assignee_identity(runtime, reference, space=space)

    source_complete = True
    if sprint_id:
        tasks = list(await runtime.adapter.get_sprint_tasks(sprint_id, space))
        if source_assignee:
            tasks = [task for task in tasks if _task_matches_identity(task, source_assignee)]
        if phrase:
            needle = phrase.casefold()
            tasks = [
                task for task in tasks
                if needle in task.key.casefold()
                or needle in str(task.title or "").casefold()
                or needle in str(task.description or "").casefold()
            ]
    else:
        if not space and not source_assignee:
            raise AS21SourceUnavailable(
                "composable task analysis requires a bounded space, person or sprint"
            )
        if source_assignee:
            tasks = await _live_assignee_rows(
                runtime,
                assignee=source_assignee,
                space=space,
            )
            if phrase:
                needle = phrase.casefold()
                tasks = [
                    task for task in tasks
                    if needle in task.key.casefold()
                    or needle in str(task.title or "").casefold()
                    or needle in str(task.description or "").casefold()
                ]
        else:
            tasks, meta = await _live_query(
                runtime,
                phrase=phrase,
                space=space,
                assignee=None,
            )
            source_complete = bool(meta.get("source_complete", True))
            if not source_complete:
                raise AS21SourceUnavailable(
                    "REAL AS21 returned an incomplete bounded task corpus; exact analysis is unproven"
                )

    raw_status = str(args.get("status") or "").strip()
    if raw_status:
        tasks = [task for task in tasks if _matches_requested_status(runtime, task, raw_status)]

    raw_period = str(args.get("created_period") or "").strip()
    period_meta: dict[str, Any] = {}
    if raw_period:
        start, end, kind = _parse_human_created_period(raw_period)
        missing = [task.key for task in tasks if _source_created_at(task) is None]
        if missing:
            raise AS21SourceUnavailable(
                "REAL AS21 creation timestamps are incomplete for the bounded corpus; "
                f"cannot compose an exact period constraint ({len(missing)} rows missing created_at)"
            )
        tasks = [task for task in tasks if start <= _source_created_at(task) <= end]
        period_meta = {
            "created_period": raw_period,
            "created_from": start.isoformat(),
            "created_to": end.isoformat(),
            "period_kind": kind,
        }

    return tasks, {
        "space": space,
        "reference": reference,
        "source_assignee": source_assignee,
        "sprint_id": sprint_id,
        "status": raw_status or None,
        "phrase": phrase,
        "source_complete": source_complete,
        **period_meta,
    }


def build_task_type_analysis(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        requested_type = str(args.get("task_type") or "").strip() or None
        tasks, scope = await _bounded_composable_tasks(runtime, args)

        breakdown: dict[tuple[str | None, str | None], int] = {}
        unknown_type_keys: list[str] = []
        for task in tasks:
            code, name = _task_type_pair(task)
            if not code and not name:
                unknown_type_keys.append(task.key)
            breakdown[(code, name)] = breakdown.get((code, name), 0) + 1

        if requested_type and unknown_type_keys:
            raise AS21SourceUnavailable(
                "REAL AS21 task type is missing for part of the bounded corpus; "
                f"cannot prove an exact type filter ({len(unknown_type_keys)} rows missing suit/type)"
            )

        matches = [
            task for task in tasks
            if not requested_type or _task_type_matches(task, requested_type)
        ]
        rows = [_task_dict(task) for task in matches]
        type_rows = [
            {"code": code, "name": name, "count": count}
            for (code, name), count in sorted(
                breakdown.items(),
                key=lambda item: (-item[1], str(item[0][1] or item[0][0] or "")),
            )
        ]

        if requested_type:
            answer = f"Найдено задач типа «{requested_type}»: {len(rows)}."
        else:
            readable = ", ".join(
                f"{item['name'] or item['code'] or 'UNKNOWN'} — {item['count']}"
                for item in type_rows[:8]
            )
            answer = f"Распределение типов задач: {readable or 'данные о типах отсутствуют'}."

        warnings = []
        if unknown_type_keys:
            warnings.append(f"task_type_missing_for_{len(unknown_type_keys)}_tasks")

        return CapabilityResult(
            answer=answer,
            data={
                "count": len(rows),
                "scope_count": len(tasks),
                "tasks": rows,
                "task_keys": [row["key"] for row in rows],
                "task_type": requested_type,
                "type_breakdown": type_rows,
                "unknown_type_count": len(unknown_type_keys),
                "unknown_type_keys": unknown_type_keys[:50],
                **scope,
                "source": "REAL_AS21",
                "type_source": "unit.suit",
            },
            evidence=[
                Evidence(
                    type="task_type",
                    source="as21",
                    entity_id=task.key,
                    label=task.title,
                    value=(_task_type_pair(task)[1] or _task_type_pair(task)[0] or "UNKNOWN"),
                )
                for task in matches
            ],
            warnings=warnings,
        )

    return execute


def _is_epic_type(code: str | None, name: str | None) -> bool:
    values = [
        re.sub(r"[_\-]+", " ", str(value).casefold()).strip()
        for value in (code, name)
        if value
    ]
    epic_aliases = _TYPE_ALIASES["epic"]
    return any(value == "epic" or value in epic_aliases for value in values)


async def _hierarchy_for_task(
    runtime: Any,
    task_key: str,
    relation_cache: dict[str, dict[str, Any]],
    *,
    max_depth: int = 20,
) -> dict[str, Any]:
    async def relation(key: str) -> dict[str, Any]:
        normalized = key.upper().strip()
        if normalized not in relation_cache:
            relation_cache[normalized] = await runtime.adapter.get_task_relations(normalized)
        return relation_cache[normalized]

    start = task_key.upper().strip()
    current = start
    visited = {start}
    parent_chain: list[dict[str, Any]] = []
    explicit_epic: str | None = None
    source_fields: list[str] = []
    related_keys: list[str] = []
    start_schema_proven = False

    for depth in range(max_depth + 1):
        facts = await relation(current)
        if depth == 0:
            start_schema_proven = bool(facts.get("schema_proven"))
            related_keys = list(facts.get("related_keys") or [])
        source_fields.extend(str(item) for item in facts.get("source_fields_seen", []) if item)
        if facts.get("parent_ambiguous") or facts.get("epic_ambiguous"):
            raise AS21SourceUnavailable(
                f"REAL AS21 exposes ambiguous hierarchy relation for {current}"
            )

        epic = facts.get("epic_key")
        if isinstance(epic, str) and epic.strip() and explicit_epic is None:
            explicit_epic = epic.upper().strip()

        code = facts.get("task_type_code")
        name = facts.get("task_type_name")
        if current != start and explicit_epic is None and _is_epic_type(
            str(code) if code else None,
            str(name) if name else None,
        ):
            explicit_epic = current

        parent = facts.get("parent_key")
        if not isinstance(parent, str) or not parent.strip():
            return {
                "task_key": start,
                "parent_chain": parent_chain,
                "depth": len(parent_chain),
                "root_key": current,
                "epic_key": explicit_epic,
                "related_keys": related_keys,
                "schema_proven": start_schema_proven or bool(source_fields),
                "source_fields_seen": list(dict.fromkeys(source_fields)),
                "truncated": False,
            }

        parent = parent.upper().strip()
        if parent in visited:
            raise AS21SourceUnavailable(
                f"REAL AS21 hierarchy cycle detected while traversing {start}: {parent}"
            )
        if depth >= max_depth:
            raise AS21SourceUnavailable(
                f"Task hierarchy for {start} exceeds the safety traversal cap {max_depth}; "
                "source maximum depth is not assumed"
            )

        visited.add(parent)
        parent_chain.append({
            "key": parent,
            "relation": "parent",
        })
        current = parent

    raise AS21SourceUnavailable(f"Task hierarchy traversal did not terminate for {start}")


def build_task_hierarchy(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        mode = str(args.get("mode") or "").strip().casefold() or "inspect"
        task_key = str(args.get("task_key") or "").strip().upper() or None
        relation_cache: dict[str, dict[str, Any]] = {}

        if task_key and mode not in {"group", "group_by_epic", "epic_group"}:
            hierarchy = await _hierarchy_for_task(runtime, task_key, relation_cache)
            if not hierarchy["schema_proven"]:
                raise AS21SourceUnavailable(
                    "REAL AS21 relation schema is not observable for this task; "
                    "cannot certify an empty parent/linked-task result"
                )
            chain = hierarchy["parent_chain"]
            answer = (
                f"Для {task_key}: уровней родителей — {len(chain)}, "
                f"связанных задач — {len(hierarchy['related_keys'])}."
            )
            if hierarchy.get("epic_key"):
                answer += f" Эпик: {hierarchy['epic_key']}."
            return CapabilityResult(
                answer=answer,
                data={
                    **hierarchy,
                    "mode": "inspect",
                    "source": "REAL_AS21",
                    "max_depth_assumption": None,
                    "safety_traversal_cap": 20,
                },
                evidence=[
                    Evidence(
                        type="task_relation",
                        source="as21",
                        entity_id=task_key,
                        label="parent_chain",
                        value=" -> ".join(item["key"] for item in chain) or "ROOT",
                    )
                ],
            )

        tasks, scope = await _bounded_composable_tasks(runtime, args)
        requested_type = str(args.get("task_type") or "").strip() or None
        if requested_type:
            missing_type = [task.key for task in tasks if not any(_task_type_pair(task))]
            if missing_type:
                raise AS21SourceUnavailable(
                    "REAL AS21 task type is missing for part of the hierarchy scope; "
                    f"cannot compose an exact type constraint ({len(missing_type)} rows missing suit/type)"
                )
            tasks = [task for task in tasks if _task_type_matches(task, requested_type)]
            scope["task_type"] = requested_type
        if not tasks:
            return CapabilityResult(
                answer="В выбранном source-backed scope задач нет.",
                data={
                    "mode": "group_by_epic",
                    "count": 0,
                    "groups": [],
                    "tasks": [],
                    **scope,
                    "source": "REAL_AS21",
                },
                evidence=[],
            )

        max_fanout = 200
        if len(tasks) > max_fanout:
            raise AS21SourceUnavailable(
                f"Epic grouping requires relation point-reads for {len(tasks)} tasks; "
                f"bounded safety limit is {max_fanout}. Narrow by person/sprint/status/type."
            )

        semaphore = asyncio.Semaphore(8)

        async def resolve_one(task: Any) -> tuple[Any, dict[str, Any]]:
            async with semaphore:
                return task, await _hierarchy_for_task(runtime, task.key, relation_cache)

        resolved = await asyncio.gather(*(resolve_one(task) for task in tasks))
        groups: dict[str, list[Any]] = {}
        unproven: list[str] = []
        hierarchy_rows: list[dict[str, Any]] = []
        for task, hierarchy in resolved:
            if not hierarchy.get("schema_proven"):
                unproven.append(task.key)
            epic_key = hierarchy.get("epic_key")
            group_key = str(epic_key or "NO_EPIC")
            groups.setdefault(group_key, []).append(task)
            hierarchy_rows.append({
                "task_key": task.key,
                "epic_key": epic_key,
                "root_key": hierarchy.get("root_key"),
                "depth": hierarchy.get("depth"),
                "parent_chain": hierarchy.get("parent_chain"),
                "related_keys": hierarchy.get("related_keys"),
                "schema_proven": hierarchy.get("schema_proven"),
            })

        if len(unproven) == len(tasks):
            raise AS21SourceUnavailable(
                "REAL AS21 relation field contract is not observable for the bounded corpus; "
                "epic grouping would be an invented empty hierarchy"
            )

        group_rows = [
            {
                "epic_key": None if key == "NO_EPIC" else key,
                "label": "Без подтверждённого эпика" if key == "NO_EPIC" else key,
                "count": len(items),
                "task_keys": [task.key for task in items],
                "tasks": [_task_dict(task) for task in items],
            }
            for key, items in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0]))
        ]

        warnings = []
        if unproven:
            warnings.append(
                f"hierarchy_schema_unproven_for_{len(unproven)}_tasks"
            )

        return CapabilityResult(
            answer=(
                f"Сгруппировано задач по эпикам/иерархии: {len(tasks)}; "
                f"групп: {len(group_rows)}."
            ),
            data={
                "mode": "group_by_epic",
                "count": len(tasks),
                "groups": group_rows,
                "hierarchy": hierarchy_rows,
                "unproven_count": len(unproven),
                "unproven_task_keys": unproven[:50],
                "max_depth_assumption": None,
                "safety_traversal_cap": 20,
                **scope,
                "source": "REAL_AS21",
            },
            evidence=[
                Evidence(
                    type="task_hierarchy",
                    source="as21",
                    entity_id=task.key,
                    label=task.title,
                    value=str(hierarchy.get("epic_key") or hierarchy.get("root_key") or "NO_EPIC"),
                )
                for task, hierarchy in resolved
            ],
            warnings=warnings,
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

        requested_status = str(args.get("status") or "").strip().casefold()
        normalized_status = None
        if requested_status:
            if requested_status in {"not_completed", "open", "active", "открытые", "незавершенные", "незавершённые"}:
                tasks = [task for task in tasks if task.is_open]
                normalized_status = "not_completed"
            elif requested_status in {"completed", "done", "closed", "закрытые", "завершенные", "завершённые"}:
                tasks = [task for task in tasks if task.is_completed]
                normalized_status = "completed"
            else:
                tasks = [
                    task for task in tasks
                    if requested_status in task.status.value.casefold()
                    or requested_status in task.status_category.value.casefold()
                ]
                normalized_status = requested_status

        rows = [_task_dict(task) for task in tasks]
        label = f" по состоянию «{normalized_status}»" if normalized_status else ""
        return CapabilityResult(
            answer=f"Для «{reference}» найдено задач{label}: {len(rows)}.",
            data={
                "count": len(rows),
                "tasks": rows,
                "task_keys": [row["key"] for row in rows],
                "reference": reference,
                "source_reference": canonical_identity,
                "member_login": canonical_identity,
                "space": space,
                "status": normalized_status,
                "source": "REAL_AS21",
            },
            evidence=[Evidence(type="task", source="as21", entity_id=row["key"], label=row["title"], value=row["status"]) for row in rows],
        )
    return execute


def build_task_search_status(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        raw_status = str(args.get("status") or "").strip()
        status = raw_status.casefold()
        if not status:
            raise ValueError("status is required")
        space = str(args.get("space") or "").strip() or None
        assignee, source_assignee = await _source_assignee_from_args(runtime, args, space=space)
        tasks = await _live_rows(runtime, space=space, assignee=source_assignee)
        if status in {"not_completed", "open", "active", "открытые", "незавершенные", "незавершённые"}:
            tasks = [task for task in tasks if task.is_open]
            normalized = "not_completed"
        elif status in {"completed", "done", "closed", "закрытые", "завершенные", "завершённые"}:
            tasks = [task for task in tasks if task.is_completed]
            normalized = "completed"
        elif normalize_task_status(raw_status) == TaskStatus.IN_PROGRESS:
            tasks = [task for task in tasks if task.status == TaskStatus.IN_PROGRESS]
            normalized = TaskStatus.IN_PROGRESS.value
        else:
            tasks = [task for task in tasks if status in task.status.value.casefold() or status in task.status_category.value.casefold()]
            normalized = status
        rows = [_task_dict(task) for task in tasks]
        return CapabilityResult(
            answer=f"Найдено задач по состоянию «{normalized}»: {len(rows)}.",
            data={"count": len(rows), "tasks": rows, "task_keys": [row["key"] for row in rows], "status": normalized, "space": space, "assignee": assignee, "source_assignee": source_assignee, "source": "REAL_AS21"},
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
        space = str(args.get("space") or "").strip().upper() or None
        sprint_id = str(args.get("sprint_id") or "").strip().upper() or None
        assignee = str(args.get("assignee") or args.get("reference") or "").strip() or None
        source_assignee = None

        if assignee:
            assignee, source_assignee = await _source_assignee_from_args(runtime, args, space=space)

        if task_key:
            task = await runtime.adapter.get_task(task_key)
            candidates = [task] if task is not None else []
        elif sprint_id:
            candidates = list(await runtime.adapter.get_sprint_tasks(sprint_id, space))
            if source_assignee:
                wanted = source_assignee.casefold()
                candidates = [
                    task for task in candidates
                    if wanted in {
                        str(value).strip().casefold()
                        for value in (
                            getattr(task, "assignee", None),
                            getattr(task, "assignee_login", None),
                            getattr(task, "assignee_id", None),
                        )
                        if value and str(value).strip()
                    }
                ]
        else:
            if not assignee:
                assignee, source_assignee = await _source_assignee_from_args(runtime, args, space=space)
            candidates = await _live_rows(runtime, space=space, assignee=source_assignee)

        raw_status = str(args.get("status") or "").strip()
        if raw_status:
            candidates = [
                task for task in candidates
                if _matches_requested_status(runtime, task, raw_status)
            ]

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
            data={"attachment_type": kind.value if kind else None, "count": len(matches), "results": matches, "task_key": task_key, "space": space, "sprint_id": sprint_id, "assignee": assignee, "source_assignee": source_assignee, "status": raw_status or None, "source": "REAL_AS21"},
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
        team_scope = str(args.get("team_scope") or args.get("scope") or "").strip().casefold() in {
            "1", "true", "yes", "team", "команда", "команды",
        }
        assignee, source_assignee = await _source_assignee_from_args(runtime, args, space=space)
        if not space and not assignee:
            raise AS21SourceUnavailable("task.aging requires a bounded space or assignee on the live source path")

        if team_scope and space and not assignee:
            logins = [login for login in get_all_member_logins() if login]
            if not logins:
                raise AS21SourceUnavailable("configured team directory is unavailable for team-scoped aging")
            tasks_by_key: dict[str, Any] = {}
            failed: list[str] = []
            for login in logins:
                try:
                    member_tasks = await _live_rows(runtime, space=space, assignee=login)
                except AS21SourceUnavailable:
                    failed.append(login)
                    continue
                for task in member_tasks:
                    tasks_by_key[task.key] = task
            if failed:
                raise AS21SourceUnavailable(
                    "team-scoped aging requires complete assignee reads; unavailable members: "
                    + ", ".join(failed)
                )
            tasks = list(tasks_by_key.values())
        else:
            tasks = await _live_rows(runtime, space=space, assignee=source_assignee)

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
                "source_assignee": source_assignee,
                "team_scope": team_scope,
                "team_member_count": len(get_all_member_logins()) if team_scope else None,
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
