"""Executable recovery Harness Core.

Business behavior is expressed as versioned skills invoking allow-listed
capabilities. Deterministic logic is preferred; LLM use is added only where
interpretation is genuinely required.
"""
from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass
from typing import Awaitable, Callable

from po_agent.adapters.as21 import AS21Adapter
from po_agent.adapters.fake import FakeAS21Adapter
from po_agent.domain.models import AttachmentType, Task

from .contracts import CapabilityResult, Evidence, HarnessRequest, HarnessResponse, ResponseStatus

CapabilityHandler = Callable[[dict[str, str]], Awaitable[CapabilityResult]]


@dataclass(frozen=True)
class ExecutableSkill:
    id: str
    version: str
    intent: str
    capability_id: str
    description: str


class CapabilityRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, CapabilityHandler] = {}

    def register(self, capability_id: str, handler: CapabilityHandler) -> None:
        if capability_id in self._handlers:
            raise ValueError(f"Capability already registered: {capability_id}")
        self._handlers[capability_id] = handler

    async def execute(self, capability_id: str, arguments: dict[str, str]) -> CapabilityResult:
        if capability_id not in self._handlers:
            raise ValueError(f"Capability is not allow-listed: {capability_id}")
        return await self._handlers[capability_id](arguments)


class SkillRegistry:
    def __init__(self) -> None:
        self._by_intent: dict[str, ExecutableSkill] = {}

    def register(self, skill: ExecutableSkill) -> None:
        if skill.intent in self._by_intent:
            raise ValueError(f"Intent already has an active skill: {skill.intent}")
        self._by_intent[skill.intent] = skill

    def resolve(self, intent: str) -> ExecutableSkill:
        if intent not in self._by_intent:
            raise ValueError(f"No active skill for intent: {intent}")
        return self._by_intent[intent]

    def catalog(self) -> list[ExecutableSkill]:
        return list(self._by_intent.values())


class PortfolioCapabilities:
    def __init__(self, adapter: AS21Adapter) -> None:
        self.a = adapter

    @staticmethod
    def task(t: Task) -> dict[str, object]:
        return {
            "key": t.key,
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "status": t.status.value,
            "status_category": t.status_category.value,
            "assignee": t.assignee,
            "priority": t.priority.value if t.priority else None,
            "source": t.source,
        }

    async def task_lookup(self, args: dict[str, str]) -> CapabilityResult:
        key = args["task_key"].upper()
        task = await self.a.get_task(key)
        if not task:
            return CapabilityResult(
                answer=f"Задача {key} не найдена.",
                data={"task_key": key, "found": False},
                evidence=[Evidence(type="task_lookup", source="as21", entity_id=key, label="lookup", value="not_found")],
            )
        return CapabilityResult(
            answer=f"{task.key} — {task.title}. Статус: {task.status.value}. Исполнитель: {task.assignee or 'не назначен'}.",
            data={"task": self.task(task)},
            evidence=[
                Evidence(type="task", source="as21", entity_id=task.key, label="title", value=task.title),
                Evidence(type="task", source="as21", entity_id=task.key, label="status", value=task.status.value),
            ],
        )

    async def task_search(self, args: dict[str, str]) -> CapabilityResult:
        phrase = args["phrase"].strip()
        needle = phrase.casefold()
        tasks = await self.a.search_tasks("")
        matches = [
            t for t in tasks
            if needle in t.key.casefold()
            or needle in t.title.casefold()
            or needle in (t.description or "").casefold()
        ]
        return CapabilityResult(
            answer=f"Найдено задач: {len(matches)}.",
            data={"query": phrase, "count": len(matches), "tasks": [self.task(t) for t in matches]},
            evidence=[Evidence(type="task", source="as21", entity_id=t.key, label=t.title, value=t.status.value) for t in matches],
        )

    async def task_search_attachments(self, args: dict[str, str]) -> CapabilityResult:
        requested_type = args.get("attachment_type")
        attachment_type = AttachmentType(requested_type) if requested_type else None
        tasks = await self.a.search_tasks("")
        matches: list[dict[str, object]] = []
        evidence: list[Evidence] = []
        for task in tasks:
            attachments = await self.a.get_attachment_metadata(task.key)
            if attachment_type:
                attachments = [item for item in attachments if item.type == attachment_type]
            if not attachments:
                continue
            matches.append({
                "task": self.task(task),
                "attachments": [
                    {"id": item.id, "name": item.name, "type": item.type.value, "size_bytes": item.size_bytes}
                    for item in attachments
                ],
            })
            for item in attachments:
                evidence.append(Evidence(type="attachment", source="as21", entity_id=task.key, label=item.name, value=item.type.value))
        type_label = attachment_type.value.upper() if attachment_type else "вложениями"
        return CapabilityResult(
            answer=f"Найдено задач с {type_label}: {len(matches)}.",
            data={"attachment_type": attachment_type.value if attachment_type else None, "count": len(matches), "results": matches},
            evidence=evidence,
        )

    async def sprint_health(self, args: dict[str, str]) -> CapabilityResult:
        sprint_id = args["sprint_id"].upper()
        tasks = await self.a.get_sprint_tasks(sprint_id)
        total = len(tasks)
        completed = sum(t.is_completed for t in tasks)
        blocked = sum(t.is_blocked for t in tasks)
        active = sum(t.status_category.value == "active_work" for t in tasks)
        completion_percent = round(completed / total * 100, 1) if total else 0.0
        return CapabilityResult(
            answer=f"{sprint_id}: выполнено {completed}/{total} ({completion_percent}%), заблокировано {blocked}.",
            data={"sprint_id": sprint_id, "total": total, "completed": completed, "active": active, "blocked": blocked, "completion_percent": completion_percent, "tasks": [self.task(t) for t in tasks]},
            evidence=[Evidence(type="sprint_task", source="as21", entity_id=t.key, label=t.title, value=t.status.value) for t in tasks],
        )

    async def release_health(self, args: dict[str, str]) -> CapabilityResult:
        release_id = args["release_id"].upper()
        tasks = await self.a.get_release_tasks(release_id)
        total = len(tasks)
        completed = sum(t.is_completed for t in tasks)
        blocked = sum(t.is_blocked for t in tasks)
        completion_percent = round(completed / total * 100, 1) if total else 0.0
        return CapabilityResult(
            answer=f"{release_id}: готовность {completion_percent}%, выполнено {completed}/{total}, заблокировано {blocked}.",
            data={"release_id": release_id, "total": total, "completed": completed, "blocked": blocked, "completion_percent": completion_percent, "tasks": [self.task(t) for t in tasks]},
            evidence=[Evidence(type="release_task", source="as21", entity_id=t.key, label=t.title, value=t.status.value) for t in tasks],
        )

    async def overview(self, args: dict[str, str]) -> CapabilityResult:
        tasks = await self.a.search_tasks("")
        total = len(tasks)
        completed = sum(t.is_completed for t in tasks)
        blocked = sum(t.is_blocked for t in tasks)
        active = sum(t.status_category.value == "active_work" for t in tasks)
        unassigned = sum(t.assignee is None for t in tasks)
        risks = [self.task(t) for t in tasks if t.is_blocked or (t.priority and t.priority.value in ("Critical", "Urgent") and not t.is_completed)]
        return CapabilityResult(
            answer=f"В контуре {total} задач: {active} в работе, {completed} завершено, {blocked} заблокировано.",
            data={"tasks_total": total, "active": active, "completed": completed, "blocked": blocked, "unassigned": unassigned, "risks": risks, "adapter": "fake-as21"},
            evidence=[Evidence(type="portfolio_task", source="as21", entity_id=t.key, label=t.title, value=t.status.value) for t in tasks],
        )


class DeterministicRouter:
    TASK_KEY = re.compile(r"\b[A-ZА-Я][A-ZА-Я0-9_]{1,15}-\d+\b", re.I)
    SPRINT_KEY = re.compile(r"\b[A-Z]+-SPRNT-\d+\b", re.I)
    RELEASE_KEY = re.compile(r"\b[A-Z]+-\d{4}-Q\d+\b", re.I)

    def route(self, query: str) -> tuple[str, dict[str, str]]:
        if match := self.SPRINT_KEY.search(query):
            return "sprint_health", {"sprint_id": match.group(0)}
        if match := self.RELEASE_KEY.search(query):
            return "release_health", {"release_id": match.group(0)}
        if match := self.TASK_KEY.search(query):
            return "task_lookup", {"task_key": match.group(0)}

        lowered = query.casefold().strip()
        attachment_routes = (
            (("excel", "xlsx", "xls", "эксел"), "task_search_excel", AttachmentType.EXCEL),
            (("pdf", "пдф"), "task_search_pdf", AttachmentType.PDF),
            (("msg", "письм"), "task_search_msg", AttachmentType.MSG),
        )
        if any(token in lowered for token in ("вложен", "attachment", "файл")):
            for tokens, intent, kind in attachment_routes:
                if any(token in lowered for token in tokens):
                    return intent, {"attachment_type": kind.value}
            return "task_search_attachments", {}

        if any(token in lowered for token in ("обзор", "сводк", "что происходит", "риски")):
            return "portfolio_overview", {}
        for prefix in ("найди ", "поиск ", "search ", "найти "):
            if lowered.startswith(prefix):
                return "task_search", {"phrase": query[len(prefix):].strip().strip('"“”')}
        return "task_search", {"phrase": query.strip()}


class HarnessRuntime:
    def __init__(self, adapter: AS21Adapter) -> None:
        self.adapter = adapter
        self.router = DeterministicRouter()
        self.capabilities = CapabilityRegistry()
        self.skills = SkillRegistry()
        capabilities = PortfolioCapabilities(adapter)
        specs = [
            ("task-lookup", "task_lookup", "task.lookup", capabilities.task_lookup),
            ("task-search", "task_search", "task.search", capabilities.task_search),
            ("task-search-attachments", "task_search_attachments", "task.search_attachments", capabilities.task_search_attachments),
            ("task-search-excel", "task_search_excel", "task.search_attachment_excel", capabilities.task_search_attachments),
            ("task-search-pdf", "task_search_pdf", "task.search_attachment_pdf", capabilities.task_search_attachments),
            ("task-search-msg", "task_search_msg", "task.search_attachment_msg", capabilities.task_search_attachments),
            ("sprint-health", "sprint_health", "sprint.health", capabilities.sprint_health),
            ("release-health", "release_health", "release.health", capabilities.release_health),
            ("portfolio-overview", "portfolio_overview", "portfolio.overview", capabilities.overview),
        ]
        for skill_id, intent, capability_id, handler in specs:
            self.capabilities.register(capability_id, handler)
            self.skills.register(ExecutableSkill(skill_id, "1.0.0", intent, capability_id, f"Executable {intent} skill"))

    async def process(self, request: HarnessRequest) -> HarnessResponse:
        started = time.perf_counter()
        trace_id = str(uuid.uuid4())
        session_id = request.session_id or str(uuid.uuid4())
        query = request.query.strip()
        if not query:
            return HarnessResponse(status=ResponseStatus.FAILED, trace_id=trace_id, session_id=session_id, answer="Пустой запрос.", warnings=["query_empty"], latency_ms=(time.perf_counter() - started) * 1000)
        try:
            intent, arguments = self.router.route(query)
            skill = self.skills.resolve(intent)
            result = await self.capabilities.execute(skill.capability_id, arguments)
            return HarnessResponse(status=ResponseStatus.COMPLETED, trace_id=trace_id, session_id=session_id, answer=result.answer, intent=intent, skill_id=skill.id, skill_version=skill.version, data=result.data, evidence=result.evidence, warnings=result.warnings, latency_ms=(time.perf_counter() - started) * 1000)
        except Exception:
            return HarnessResponse(status=ResponseStatus.FAILED, trace_id=trace_id, session_id=session_id, answer="Не удалось выполнить запрос.", warnings=["runtime_failure"], latency_ms=(time.perf_counter() - started) * 1000)


def build_fake_runtime() -> HarnessRuntime:
    return HarnessRuntime(FakeAS21Adapter())
