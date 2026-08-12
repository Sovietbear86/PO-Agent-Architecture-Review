"""Task-intelligence capabilities for the executable Harness.

These handlers deliberately work without an LLM. Where the Master Spec allows
LLM interpretation, the deterministic fallback is still a complete typed result
and carries an explicit warning. Later LLM synthesis may enrich wording but may
not invent source facts or change deterministic quality/metric values.
"""
from __future__ import annotations

from datetime import datetime

from po_agent.adapters.as21 import AS21Adapter
from po_agent.analysis.task_quality import TaskQualityAnalysis
from po_agent.domain.models import Task, TaskStatus

from .contracts import CapabilityResult, Evidence


class TaskIntelligenceCapabilities:
    def __init__(self, adapter: AS21Adapter) -> None:
        self.adapter = adapter
        self.quality = TaskQualityAnalysis()

    async def summary(self, args: dict[str, str]) -> CapabilityResult:
        task = await self._require_task(args["task_key"])
        if task is None:
            return self._not_found(args["task_key"])

        description = (task.description or "").strip()
        dependencies = list(task.depends_on)
        open_questions: list[str] = []
        if not description:
            open_questions.append("Что конкретно требуется реализовать?")
        if not self._has_acceptance_expectations(description):
            open_questions.append("По каким критериям будет приниматься результат?")

        structured = {
            "task_key": task.key,
            "goal": description or task.title,
            "what_to_do": description or "В исходных данных нет описания; требуется уточнение постановки.",
            "acceptance_expectations": [],
            "dependencies": dependencies,
            "open_questions": open_questions,
            "source_title": task.title,
        }
        answer = (
            f"{task.key}: {task.title}. "
            f"По доступным данным требуется: {structured['what_to_do']}"
        )
        return CapabilityResult(
            answer=answer,
            data=structured,
            evidence=self._core_evidence(task),
            warnings=["llm_unavailable_deterministic_summary"],
        )

    async def quality_report(self, args: dict[str, str]) -> CapabilityResult:
        task = await self._require_task(args["task_key"])
        if task is None:
            return self._not_found(args["task_key"])
        report = self.quality.generate_quality_report(task)
        return CapabilityResult(
            answer=(
                f"Качество постановки {task.key}: {report['score']}/100 "
                f"({report['quality_level']}). Найдено замечаний: {len(report['issues'])}."
            ),
            data=report,
            evidence=self._core_evidence(task) + [
                Evidence(
                    type="quality_rule",
                    source="deterministic",
                    entity_id=task.key,
                    label=rule["id"],
                    value={"passed": rule["passed"], "penalty": rule["penalty"]},
                )
                for rule in report["rules"]
            ],
        )

    async def missing_requirements(self, args: dict[str, str]) -> CapabilityResult:
        task = await self._require_task(args["task_key"])
        if task is None:
            return self._not_found(args["task_key"])
        report = self.quality.generate_quality_report(task)
        return CapabilityResult(
            answer=(
                f"Для {task.key} отсутствуют/недостаточно определены элементы: "
                + (", ".join(report["missing_elements"]) if report["missing_elements"] else "нет критичных пробелов")
                + "."
            ),
            data={
                "task_key": task.key,
                "missing_elements": report["missing_elements"],
                "issues": report["issues"],
                "recommendations": report["recommendations"],
                "quality_score": report["score"],
            },
            evidence=self._core_evidence(task),
        )

    async def history(self, args: dict[str, str]) -> CapabilityResult:
        key = args["task_key"].upper()
        task = await self._require_task(key)
        if task is None:
            return self._not_found(key)
        transitions = await self.adapter.get_task_history(key)
        timeline = [
            {
                "from": transition.from_status.value,
                "to": transition.to_status.value,
                "timestamp": transition.timestamp.isoformat(),
                "author": transition.author,
            }
            for transition in transitions
        ]
        return CapabilityResult(
            answer=f"У {key} найдено переходов по статусам: {len(timeline)}.",
            data={"task_key": key, "current_status": task.status.value, "timeline": timeline},
            evidence=[
                Evidence(
                    type="status_transition",
                    source="as21",
                    entity_id=key,
                    label=f"{item['from']} → {item['to']}",
                    value=item["timestamp"],
                )
                for item in timeline
            ],
        )

    async def time_in_status(self, args: dict[str, str]) -> CapabilityResult:
        key = args["task_key"].upper()
        task = await self._require_task(key)
        if task is None:
            return self._not_found(key)
        transitions = await self.adapter.get_task_history(key)
        now = datetime.now()
        durations: list[dict[str, object]] = []
        if transitions:
            ordered = sorted(transitions, key=lambda item: item.timestamp)
            for index, transition in enumerate(ordered):
                end = ordered[index + 1].timestamp if index + 1 < len(ordered) else now
                durations.append(
                    {
                        "status": transition.to_status.value,
                        "hours": round(max(0.0, (end - transition.timestamp).total_seconds() / 3600), 2),
                        "from": transition.timestamp.isoformat(),
                        "to": end.isoformat(),
                    }
                )
        return CapabilityResult(
            answer=f"{key}: текущий статус {task.status.value}, рассчитано интервалов: {len(durations)}.",
            data={"task_key": key, "current_status": task.status.value, "durations": durations},
            evidence=[
                Evidence(
                    type="status_duration",
                    source="as21_history",
                    entity_id=key,
                    label=item["status"],
                    value=item["hours"],
                )
                for item in durations
            ],
        )

    async def aging(self, args: dict[str, str]) -> CapabilityResult:
        threshold_days = int(args.get("threshold_days", "7"))
        tasks = await self.adapter.search_tasks("")
        active = [
            task
            for task in tasks
            if not task.is_completed
            and task.status != TaskStatus.CANCELLED
            and task.age_days >= threshold_days
        ]
        active.sort(key=lambda task: task.age_days, reverse=True)
        data = [
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
            answer=f"Задач старше {threshold_days} дней: {len(data)}.",
            data={"threshold_days": threshold_days, "count": len(data), "tasks": data},
            evidence=[
                Evidence(
                    type="task_age",
                    source="as21",
                    entity_id=item["key"],
                    label=item["title"],
                    value=item["age_days"],
                )
                for item in data
            ],
        )

    async def _require_task(self, task_key: str) -> Task | None:
        return await self.adapter.get_task(task_key.upper())

    @staticmethod
    def _core_evidence(task: Task) -> list[Evidence]:
        return [
            Evidence(type="task", source="as21", entity_id=task.key, label="title", value=task.title),
            Evidence(type="task", source="as21", entity_id=task.key, label="description", value=task.description),
            Evidence(type="task", source="as21", entity_id=task.key, label="status", value=task.status.value),
        ]

    @staticmethod
    def _not_found(key: str) -> CapabilityResult:
        normalized = key.upper()
        return CapabilityResult(
            answer=f"Задача {normalized} не найдена.",
            data={"task_key": normalized, "found": False},
            evidence=[
                Evidence(
                    type="task_lookup",
                    source="as21",
                    entity_id=normalized,
                    label="lookup",
                    value="not_found",
                )
            ],
        )

    @staticmethod
    def _has_acceptance_expectations(description: str) -> bool:
        lowered = description.casefold()
        markers = (
            "критерии приемки",
            "критерии приёмки",
            "acceptance",
            "definition of done",
            "ожидаемый результат",
        )
        return any(marker in lowered for marker in markers)
