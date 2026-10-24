"""Advanced deterministic task intelligence for Harness recovery.

These capabilities keep factual extraction in code. LLM enrichment can be added
later for wording/ranking, but source facts and scores remain deterministic.
"""
from __future__ import annotations

import re
from collections import Counter

from po_agent.adapters.as21 import AS21Adapter
from po_agent.domain.models import Task

from .contracts import CapabilityResult, Evidence


class AdvancedTaskCapabilities:
    def __init__(self, adapter: AS21Adapter) -> None:
        self.adapter = adapter

    async def acceptance_analysis(self, args: dict[str, str]) -> CapabilityResult:
        task = await self._task(args["task_key"])
        if task is None:
            return self._not_found(args["task_key"])
        description = (task.description or "").strip()
        criteria = self._extract_criteria(description)
        has_explicit_section = any(marker in description.casefold() for marker in (
            "критерии приемки", "критерии приёмки", "acceptance", "definition of done", "ожидаемый результат"
        ))
        testable = [item for item in criteria if self._looks_testable(item)]
        score = 0
        if has_explicit_section:
            score += 40
        if criteria:
            score += 30
        if criteria and len(testable) == len(criteria):
            score += 30
        elif testable:
            score += 15
        gaps = []
        if not has_explicit_section:
            gaps.append("Нет явно выделенных критериев приемки")
        if not criteria:
            gaps.append("Нет отдельных проверяемых условий")
        elif len(testable) < len(criteria):
            gaps.append("Часть условий сформулирована непроверяемо")
        return CapabilityResult(
            answer=f"{task.key}: качество критериев приемки {score}/100, найдено условий: {len(criteria)}.",
            data={
                "task_key": task.key,
                "score": score,
                "has_explicit_section": has_explicit_section,
                "criteria": criteria,
                "testable_criteria": testable,
                "gaps": gaps,
            },
            evidence=self._evidence(task) + [
                Evidence(type="acceptance_criterion", source="task_description", entity_id=task.key, label=f"criterion_{i+1}", value=item)
                for i, item in enumerate(criteria)
            ],
        )

    async def dependencies(self, args: dict[str, str]) -> CapabilityResult:
        task = await self._task(args["task_key"])
        if task is None:
            return self._not_found(args["task_key"])
        dependency_rows = []
        evidence = self._evidence(task)
        for key in task.depends_on:
            dep = await self.adapter.get_task(key)
            row = {
                "key": key,
                "found": dep is not None,
                "title": dep.title if dep else None,
                "status": dep.status.value if dep else None,
                "completed": dep.is_completed if dep else None,
            }
            dependency_rows.append(row)
            evidence.append(Evidence(type="dependency", source="as21", entity_id=task.key, label=key, value=row))
        unresolved = [row for row in dependency_rows if not row["found"] or not row["completed"]]
        return CapabilityResult(
            answer=f"{task.key}: зависимостей {len(dependency_rows)}, незавершенных/не найденных {len(unresolved)}.",
            data={"task_key": task.key, "dependencies": dependency_rows, "unresolved_count": len(unresolved)},
            evidence=evidence,
        )

    async def blockers(self, args: dict[str, str]) -> CapabilityResult:
        task = await self._task(args["task_key"])
        if task is None:
            return self._not_found(args["task_key"])
        dependency_rows = []
        for key in task.depends_on:
            dep = await self.adapter.get_task(key)
            if dep is None or not dep.is_completed:
                dependency_rows.append({"key": key, "status": dep.status.value if dep else "not_found"})
        reasons = []
        if task.is_blocked:
            reasons.append("Статус задачи означает ожидание информации")
        if dependency_rows:
            reasons.append("Есть незавершенные зависимости")
        blocked = bool(reasons)
        return CapabilityResult(
            answer=f"{task.key}: {'есть признаки блокировки' if blocked else 'явных блокировок не найдено'}.",
            data={"task_key": task.key, "blocked": blocked, "reasons": reasons, "unresolved_dependencies": dependency_rows, "status": task.status.value},
            evidence=self._evidence(task) + [Evidence(type="blocker", source="deterministic", entity_id=task.key, label="blocked", value=blocked)],
        )

    async def similar(self, args: dict[str, str]) -> CapabilityResult:
        task = await self._task(args["task_key"])
        if task is None:
            return self._not_found(args["task_key"])
        candidates = await self.adapter.search_tasks("")
        source_tokens = self._tokens(f"{task.title} {task.description or ''}")
        rows = []
        for other in candidates:
            if other.key == task.key:
                continue
            other_tokens = self._tokens(f"{other.title} {other.description or ''}")
            union = source_tokens | other_tokens
            similarity = round(len(source_tokens & other_tokens) / len(union), 3) if union else 0.0
            if similarity <= 0:
                continue
            rows.append({"key": other.key, "title": other.title, "similarity": similarity, "status": other.status.value})
        rows.sort(key=lambda item: item["similarity"], reverse=True)
        rows = rows[:5]
        return CapabilityResult(
            answer=f"Для {task.key} найдено похожих задач: {len(rows)}.",
            data={"task_key": task.key, "matches": rows, "method": "token_jaccard_v1"},
            evidence=self._evidence(task) + [Evidence(type="similar_task", source="as21+deterministic", entity_id=item["key"], label=item["title"], value=item["similarity"]) for item in rows],
        )

    async def _task(self, key: str) -> Task | None:
        return await self.adapter.get_task(key.upper())

    @staticmethod
    def _extract_criteria(description: str) -> list[str]:
        if not description:
            return []
        lines = []
        for line in description.splitlines():
            cleaned = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", line).strip()
            if cleaned and cleaned != line.strip():
                lines.append(cleaned)
        return lines

    @staticmethod
    def _looks_testable(text: str) -> bool:
        lowered = text.casefold()
        signals = ("долж", "если", "когда", "не более", "не менее", "равен", "отображ", "возвращ", "создан", "доступ", "works", "must", "should")
        return any(signal in lowered for signal in signals) or bool(re.search(r"\d", text))

    @staticmethod
    def _tokens(text: str) -> set[str]:
        stop = {"для", "the", "and", "или", "это", "with", "from", "create", "add", "user", "task"}
        return {token for token in re.findall(r"[A-Za-zА-Яа-я0-9]{3,}", text.casefold()) if token not in stop}

    @staticmethod
    def _evidence(task: Task) -> list[Evidence]:
        return [
            Evidence(type="task", source="as21", entity_id=task.key, label="title", value=task.title),
            Evidence(type="task", source="as21", entity_id=task.key, label="status", value=task.status.value),
            Evidence(type="task", source="as21", entity_id=task.key, label="description", value=task.description),
        ]

    @staticmethod
    def _not_found(key: str) -> CapabilityResult:
        normalized = key.upper()
        return CapabilityResult(answer=f"Задача {normalized} не найдена.", data={"task_key": normalized, "found": False}, evidence=[Evidence(type="task_lookup", source="as21", entity_id=normalized, label="lookup", value="not_found")])
