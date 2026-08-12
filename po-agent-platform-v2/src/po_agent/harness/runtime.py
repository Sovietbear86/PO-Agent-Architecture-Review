"""Executable recovery Harness Core.

Business behavior is expressed as versioned Skills invoking allow-listed
capabilities. `PO_AGENT_PLATFORM_V2_GIGACODE_MASTER_SPEC_V2_1.md` is the product
acceptance baseline. Every implemented user-facing Skill must execute through
this chain and return source-grounded evidence.
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
from .task_advanced import AdvancedTaskCapabilities
from .task_intelligence import TaskIntelligenceCapabilities

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
    """Source-grounded discovery and basic portfolio capabilities."""

    def __init__(self, adapter: AS21Adapter) -> None:
        self.a = adapter

    @staticmethod
    def task(task: Task) -> dict[str, object]:
        return {
            "key": task.key,
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "status_category": task.status_category.value,
            "assignee": task.assignee,
            "priority": task.priority.value if task.priority else None,
            "sprint_id": task.sprint_id,
            "release_id": task.release_id,
            "source": task.source,
        }

    @classmethod
    def task_list_result(cls, *, answer: str, tasks: list[Task], filters: dict[str, object], evidence_type: str = "task") -> CapabilityResult:
        return CapabilityResult(
            answer=answer,
            data={"count": len(tasks), "filters": filters, "tasks": [cls.task(task) for task in tasks]},
            evidence=[Evidence(type=evidence_type, source="as21", entity_id=task.key, label=task.title, value=task.status.value) for task in tasks],
        )

    async def task_lookup(self, args: dict[str, str]) -> CapabilityResult:
        key = args["task_key"].upper()
        task = await self.a.get_task(key)
        if not task:
            return CapabilityResult(answer=f"Задача {key} не найдена.", data={"task_key": key, "found": False}, evidence=[Evidence(type="task_lookup", source="as21", entity_id=key, label="lookup", value="not_found")])
        return CapabilityResult(
            answer=f"{task.key} — {task.title}. Статус: {task.status.value}. Исполнитель: {task.assignee or 'не назначен'}.",
            data={"task": self.task(task)},
            evidence=[
                Evidence(type="task", source="as21", entity_id=task.key, label="title", value=task.title),
                Evidence(type="task", source="as21", entity_id=task.key, label="status", value=task.status.value),
                Evidence(type="task", source="as21", entity_id=task.key, label="assignee", value=task.assignee),
            ],
        )

    async def task_search(self, args: dict[str, str]) -> CapabilityResult:
        phrase = args["phrase"].strip()
        needle = phrase.casefold()
        tasks = await self.a.search_tasks("")
        matches = [task for task in tasks if needle in task.key.casefold() or needle in task.title.casefold() or needle in (task.description or "").casefold()]
        return self.task_list_result(answer=f"Найдено задач: {len(matches)}.", tasks=matches, filters={"phrase": phrase})

    async def task_search_assignee(self, args: dict[str, str]) -> CapabilityResult:
        assignee = args["assignee"].strip()
        tasks = await self.a.search_tasks(f"assignee = {assignee}")
        return self.task_list_result(answer=f"У исполнителя {assignee} найдено задач: {len(tasks)}.", tasks=tasks, filters={"assignee": assignee})

    async def task_search_status(self, args: dict[str, str]) -> CapabilityResult:
        requested = args["status"].strip().casefold()
        tasks = await self.a.search_tasks("")
        matches = [task for task in tasks if requested == task.status.value.casefold() or requested == task.status_category.value.casefold() or requested in task.status.value.casefold()]
        return self.task_list_result(answer=f"В статусе «{args['status']}» найдено задач: {len(matches)}.", tasks=matches, filters={"status": args["status"]})

    async def task_search_sprint(self, args: dict[str, str]) -> CapabilityResult:
        sprint_id = args["sprint_id"].upper()
        tasks = await self.a.get_sprint_tasks(sprint_id)
        return self.task_list_result(answer=f"В спринте {sprint_id} найдено задач: {len(tasks)}.", tasks=tasks, filters={"sprint_id": sprint_id}, evidence_type="sprint_task")

    async def task_search_release(self, args: dict[str, str]) -> CapabilityResult:
        release_id = args["release_id"].upper()
        tasks = await self.a.get_release_tasks(release_id)
        return self.task_list_result(answer=f"В релизе {release_id} найдено задач: {len(tasks)}.", tasks=tasks, filters={"release_id": release_id}, evidence_type="release_task")

    async def task_search_product(self, args: dict[str, str]) -> CapabilityResult:
        product = args["product"].upper()
        tasks = await self.a.search_tasks(f"project = {product}")
        return self.task_list_result(answer=f"В продукте {product} найдено задач: {len(tasks)}.", tasks=tasks, filters={"product": product})

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
            matches.append({"task": self.task(task), "attachments": [{"id": item.id, "name": item.name, "type": item.type.value, "size_bytes": item.size_bytes} for item in attachments]})
            evidence.extend(Evidence(type="attachment", source="as21", entity_id=task.key, label=item.name, value=item.type.value) for item in attachments)
        type_label = attachment_type.value.upper() if attachment_type else "вложениями"
        return CapabilityResult(answer=f"Найдено задач с {type_label}: {len(matches)}.", data={"attachment_type": attachment_type.value if attachment_type else None, "count": len(matches), "results": matches}, evidence=evidence)

    async def sprint_health(self, args: dict[str, str]) -> CapabilityResult:
        sprint_id = args["sprint_id"].upper()
        tasks = await self.a.get_sprint_tasks(sprint_id)
        total = len(tasks)
        completed = sum(task.is_completed for task in tasks)
        blocked = sum(task.is_blocked for task in tasks)
        active = sum(task.status_category.value == "active_work" for task in tasks)
        completion_percent = round(completed / total * 100, 1) if total else 0.0
        return CapabilityResult(answer=f"{sprint_id}: выполнено {completed}/{total} ({completion_percent}%), заблокировано {blocked}.", data={"sprint_id": sprint_id, "total": total, "completed": completed, "active": active, "blocked": blocked, "completion_percent": completion_percent, "tasks": [self.task(task) for task in tasks]}, evidence=[Evidence(type="sprint_task", source="as21", entity_id=task.key, label=task.title, value=task.status.value) for task in tasks])

    async def release_health(self, args: dict[str, str]) -> CapabilityResult:
        release_id = args["release_id"].upper()
        tasks = await self.a.get_release_tasks(release_id)
        total = len(tasks)
        completed = sum(task.is_completed for task in tasks)
        blocked = sum(task.is_blocked for task in tasks)
        completion_percent = round(completed / total * 100, 1) if total else 0.0
        return CapabilityResult(answer=f"{release_id}: готовность {completion_percent}%, выполнено {completed}/{total}, заблокировано {blocked}.", data={"release_id": release_id, "total": total, "completed": completed, "blocked": blocked, "completion_percent": completion_percent, "tasks": [self.task(task) for task in tasks]}, evidence=[Evidence(type="release_task", source="as21", entity_id=task.key, label=task.title, value=task.status.value) for task in tasks])

    async def overview(self, args: dict[str, str]) -> CapabilityResult:
        tasks = await self.a.search_tasks("")
        total = len(tasks)
        completed = sum(task.is_completed for task in tasks)
        blocked = sum(task.is_blocked for task in tasks)
        active = sum(task.status_category.value == "active_work" for task in tasks)
        unassigned = sum(task.assignee is None for task in tasks)
        risks = [self.task(task) for task in tasks if task.is_blocked or (task.priority and task.priority.value in ("Critical", "Urgent") and not task.is_completed)]
        return CapabilityResult(answer=f"В контуре {total} задач: {active} в работе, {completed} завершено, {blocked} заблокировано.", data={"tasks_total": total, "active": active, "completed": completed, "blocked": blocked, "unassigned": unassigned, "risks": risks, "adapter": "fake-as21"}, evidence=[Evidence(type="portfolio_task", source="as21", entity_id=task.key, label=task.title, value=task.status.value) for task in tasks])


class DeterministicRouter:
    TASK_KEY = re.compile(r"\b[A-ZА-Я][A-ZА-Я0-9_]{1,15}-\d+\b", re.I)
    SPRINT_KEY = re.compile(r"\b[A-Z]+-SPRNT-\d+\b", re.I)
    RELEASE_KEY = re.compile(r"\b[A-Z]+-\d{4}-Q\d+\b", re.I)
    ASSIGNEE = re.compile(r"(?:исполнитель|исполнителя|на исполнителе)\s+([A-Za-zА-Яа-я0-9._-]+)", re.I)
    STATUS = re.compile(r"(?:статус|статусе)\s+[«\"]?([^»\"]+?)[»\"]?(?:$|\s+в\s|\s+для\s)", re.I)
    PRODUCT = re.compile(r"(?:продукт|продукте|пространств(?:о|е))\s+([A-Za-zА-Яа-я0-9_-]+)", re.I)

    def route(self, query: str) -> tuple[str, dict[str, str]]:
        lowered = query.casefold().strip()
        task_match = self.TASK_KEY.search(query)
        if task_match:
            task_key = task_match.group(0)
            routes = (
                (("суммар", "кратко", "что нужно сделать", "объясни задачу", "описание задачи"), "task_summary"),
                (("качество постанов", "оцени постанов", "насколько хорошо постав", "quality"), "task_quality"),
                (("чего не хватает", "что отсутствует", "missing requirements", "не хватает в задач"), "task_missing_requirements"),
                (("критерии прием", "критерии приём", "acceptance", "тестируем", "проверяем"), "task_acceptance_analysis"),
                (("зависимост", "depends", "dependency"), "task_dependency_analysis"),
                (("блокер", "блокиров", "что мешает", "blocked"), "task_blocker_analysis"),
                (("похож", "дубликат", "similar", "duplicate"), "task_similar"),
                (("история", "переход", "lifecycle"), "task_history"),
                (("сколько в статус", "времени в статус", "time in status"), "task_time_in_status"),
            )
            for tokens, intent in routes:
                if any(token in lowered for token in tokens):
                    return intent, {"task_key": task_key}

        if any(token in lowered for token in ("старые задачи", "залежал", "aging", "давно не закры")):
            days = re.search(r"(\d+)\s*(?:дн|дней|дня)", lowered)
            return "task_aging", {"threshold_days": days.group(1) if days else "7"}

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
        if match := self.ASSIGNEE.search(query):
            return "task_search_assignee", {"assignee": match.group(1)}
        if match := self.STATUS.search(query):
            return "task_search_status", {"status": match.group(1).strip()}
        if match := self.SPRINT_KEY.search(query):
            sprint_id = match.group(0)
            if any(token in lowered for token in ("задач", "scope", "состав")):
                return "task_search_sprint", {"sprint_id": sprint_id}
            return "sprint_health", {"sprint_id": sprint_id}
        if match := self.RELEASE_KEY.search(query):
            release_id = match.group(0)
            if any(token in lowered for token in ("задач", "scope", "состав")):
                return "task_search_release", {"release_id": release_id}
            return "release_health", {"release_id": release_id}
        if match := self.PRODUCT.search(query):
            return "task_search_product", {"product": match.group(1)}
        if task_match:
            return "task_lookup", {"task_key": task_match.group(0)}
        if any(token in lowered for token in ("обзор", "сводк", "что происходит", "риски")):
            return "portfolio_overview", {}
        for prefix in ("найди ", "поиск ", "search ", "найти "):
            if lowered.startswith(prefix):
                return "task_search", {"phrase": query[len(prefix):].strip().strip('"“”')}
        return "task_search", {"phrase": query.strip()}


class HarnessRuntime:
    """Thin coordinator: route -> versioned Skill -> allow-listed capability."""

    def __init__(self, adapter: AS21Adapter) -> None:
        self.adapter = adapter
        self.router = DeterministicRouter()
        self.capabilities = CapabilityRegistry()
        self.skills = SkillRegistry()
        discovery = PortfolioCapabilities(adapter)
        intelligence = TaskIntelligenceCapabilities(adapter)
        advanced = AdvancedTaskCapabilities(adapter)
        specs = [
            ("task-lookup", "task_lookup", "task.lookup", discovery.task_lookup),
            ("task-search", "task_search", "task.search", discovery.task_search),
            ("task-search-attachments", "task_search_attachments", "task.search_attachments", discovery.task_search_attachments),
            ("task-search-excel", "task_search_excel", "task.search_attachment_excel", discovery.task_search_attachments),
            ("task-search-pdf", "task_search_pdf", "task.search_attachment_pdf", discovery.task_search_attachments),
            ("task-search-msg", "task_search_msg", "task.search_attachment_msg", discovery.task_search_attachments),
            ("task-search-assignee", "task_search_assignee", "task.search_assignee", discovery.task_search_assignee),
            ("task-search-status", "task_search_status", "task.search_status", discovery.task_search_status),
            ("task-search-sprint", "task_search_sprint", "task.search_sprint", discovery.task_search_sprint),
            ("task-search-release", "task_search_release", "task.search_release", discovery.task_search_release),
            ("task-search-product", "task_search_product", "task.search_product", discovery.task_search_product),
            ("task-summary", "task_summary", "task.summary", intelligence.summary),
            ("task-quality", "task_quality", "task.quality", intelligence.quality_report),
            ("task-missing-requirements", "task_missing_requirements", "task.missing_requirements", intelligence.missing_requirements),
            ("task-acceptance-analysis", "task_acceptance_analysis", "task.acceptance_analysis", advanced.acceptance_analysis),
            ("task-dependency-analysis", "task_dependency_analysis", "task.dependencies", advanced.dependencies),
            ("task-blocker-analysis", "task_blocker_analysis", "task.blockers", advanced.blockers),
            ("task-similar", "task_similar", "task.similar", advanced.similar),
            ("task-history", "task_history", "task.history", intelligence.history),
            ("task-time-in-status", "task_time_in_status", "task.time_in_status", intelligence.time_in_status),
            ("task-aging", "task_aging", "task.aging", intelligence.aging),
            ("sprint-health", "sprint_health", "sprint.health", discovery.sprint_health),
            ("release-health", "release_health", "release.health", discovery.release_health),
            ("portfolio-overview", "portfolio_overview", "portfolio.overview", discovery.overview),
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
