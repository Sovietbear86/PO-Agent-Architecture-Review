"""Minimal executable vertical slice for the recovered harness architecture.

The purpose of this module is deliberately narrow: prove that a user request is
routed to a versioned skill, the skill invokes only an allow-listed capability,
and that capability reads through AS21Adapter and returns source evidence.
"""

from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass
from typing import Awaitable, Callable

from po_agent.adapters.as21 import AS21Adapter
from po_agent.adapters.fake import FakeAS21Adapter
from po_agent.domain.models import Task

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
    """Allow-listed runtime capability registry."""

    def __init__(self) -> None:
        self._handlers: dict[str, CapabilityHandler] = {}

    def register(self, capability_id: str, handler: CapabilityHandler) -> None:
        if capability_id in self._handlers:
            raise ValueError(f"Capability already registered: {capability_id}")
        self._handlers[capability_id] = handler

    async def execute(self, capability_id: str, arguments: dict[str, str]) -> CapabilityResult:
        try:
            handler = self._handlers[capability_id]
        except KeyError as exc:
            raise ValueError(f"Capability is not allow-listed: {capability_id}") from exc
        return await handler(arguments)


class SkillRegistry:
    """Small executable registry used by the recovery vertical slice."""

    def __init__(self) -> None:
        self._by_intent: dict[str, ExecutableSkill] = {}

    def register(self, skill: ExecutableSkill) -> None:
        if skill.intent in self._by_intent:
            raise ValueError(f"Intent already has an active skill: {skill.intent}")
        self._by_intent[skill.intent] = skill

    def resolve(self, intent: str) -> ExecutableSkill:
        try:
            return self._by_intent[intent]
        except KeyError as exc:
            raise ValueError(f"No active skill for intent: {intent}") from exc


class TaskCapabilities:
    """Source-grounded task capabilities. No LLM is required."""

    def __init__(self, adapter: AS21Adapter) -> None:
        self._adapter = adapter

    async def lookup(self, arguments: dict[str, str]) -> CapabilityResult:
        task_key = arguments["task_key"].upper()
        task = await self._adapter.get_task(task_key)
        if task is None:
            return CapabilityResult(
                answer=f"Задача {task_key} не найдена.",
                data={"task_key": task_key, "found": False},
                evidence=[Evidence(type="task_lookup", source="as21", entity_id=task_key, label="lookup", value="not_found")],
            )
        return self._task_result(task)

    async def search(self, arguments: dict[str, str]) -> CapabilityResult:
        phrase = arguments["phrase"].strip()
        # The real adapter may translate this search contract to SWTR/JQL. The
        # fake adapter returns a deterministic corpus which we filter here so
        # tests exercise the same capability behavior without SWTR.
        tasks = await self._adapter.search_tasks("")
        needle = phrase.casefold()
        matches = [
            task for task in tasks
            if needle in task.key.casefold()
            or needle in task.title.casefold()
            or needle in (task.description or "").casefold()
        ]
        data = {"query": phrase, "count": len(matches), "tasks": [self._serialize_task(t) for t in matches]}
        evidence = [
            Evidence(type="task", source="as21", entity_id=t.key, label=t.title, value=t.status.value)
            for t in matches
        ]
        return CapabilityResult(
            answer=f"Найдено задач: {len(matches)}.",
            data=data,
            evidence=evidence,
        )

    def _task_result(self, task: Task) -> CapabilityResult:
        assignee = task.assignee or "не назначен"
        answer = f"{task.key} — {task.title}. Статус: {task.status.value}. Исполнитель: {assignee}."
        evidence = [
            Evidence(type="task", source="as21", entity_id=task.key, label="title", value=task.title),
            Evidence(type="task", source="as21", entity_id=task.key, label="status", value=task.status.value),
            Evidence(type="task", source="as21", entity_id=task.key, label="assignee", value=task.assignee),
        ]
        return CapabilityResult(answer=answer, data={"task": self._serialize_task(task)}, evidence=evidence)

    @staticmethod
    def _serialize_task(task: Task) -> dict[str, object]:
        return {
            "key": task.key,
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "status_category": task.status_category.value,
            "assignee": task.assignee,
            "priority": task.priority.value if task.priority else None,
            "source": task.source,
        }


class DeterministicRouter:
    """Recovery router for the first two task skills.

    Complex semantic routing will be layered later. Exact identifiers remain
    deterministic even after LLM routing is introduced.
    """

    TASK_KEY = re.compile(r"\b[A-ZА-Я][A-ZА-Я0-9_]{1,15}-\d+\b", re.IGNORECASE)

    def route(self, query: str) -> tuple[str, dict[str, str]]:
        match = self.TASK_KEY.search(query)
        if match:
            return "task_lookup", {"task_key": match.group(0).upper()}

        lowered = query.casefold().strip()
        search_prefixes = ("найди ", "поиск ", "search ", "найти ")
        for prefix in search_prefixes:
            if lowered.startswith(prefix):
                phrase = query[len(prefix):].strip().strip('"“”')
                if phrase:
                    return "task_search", {"phrase": phrase}

        # Free text is a search during the narrow recovery slice. This keeps the
        # behavior useful while unsupported intents are added skill-by-skill.
        return "task_search", {"phrase": query.strip()}


class HarnessRuntime:
    """Thin coordination runtime: route -> skill -> capability -> response."""

    def __init__(self, adapter: AS21Adapter) -> None:
        self.adapter = adapter
        self.router = DeterministicRouter()
        self.capabilities = CapabilityRegistry()
        self.skills = SkillRegistry()

        task_capabilities = TaskCapabilities(adapter)
        self.capabilities.register("task.lookup", task_capabilities.lookup)
        self.capabilities.register("task.search", task_capabilities.search)

        self.skills.register(ExecutableSkill(
            id="task-lookup",
            version="1.0.0",
            intent="task_lookup",
            capability_id="task.lookup",
            description="Find an exact task by key and return grounded facts.",
        ))
        self.skills.register(ExecutableSkill(
            id="task-search",
            version="1.0.0",
            intent="task_search",
            capability_id="task.search",
            description="Search task title/description/key and return grounded matches.",
        ))

    async def process(self, request: HarnessRequest) -> HarnessResponse:
        started = time.perf_counter()
        trace_id = str(uuid.uuid4())
        session_id = request.session_id or str(uuid.uuid4())
        query = request.query.strip()
        if not query:
            return HarnessResponse(
                status=ResponseStatus.FAILED,
                trace_id=trace_id,
                session_id=session_id,
                answer="Пустой запрос.",
                warnings=["query_empty"],
                latency_ms=(time.perf_counter() - started) * 1000,
            )

        try:
            intent, arguments = self.router.route(query)
            skill = self.skills.resolve(intent)
            result = await self.capabilities.execute(skill.capability_id, arguments)
            return HarnessResponse(
                status=ResponseStatus.COMPLETED,
                trace_id=trace_id,
                session_id=session_id,
                answer=result.answer,
                intent=intent,
                skill_id=skill.id,
                skill_version=skill.version,
                data=result.data,
                evidence=result.evidence,
                warnings=result.warnings,
                latency_ms=(time.perf_counter() - started) * 1000,
            )
        except Exception:
            # The public contract is deliberately safe. Detailed exceptions will
            # be recorded by the persistent trace layer in the next recovery step.
            return HarnessResponse(
                status=ResponseStatus.FAILED,
                trace_id=trace_id,
                session_id=session_id,
                answer="Не удалось выполнить запрос.",
                warnings=["runtime_failure"],
                latency_ms=(time.perf_counter() - started) * 1000,
            )



def build_fake_runtime() -> HarnessRuntime:
    """Build a deterministic local runtime that requires neither SWTR nor LLM."""
    return HarnessRuntime(FakeAS21Adapter())
