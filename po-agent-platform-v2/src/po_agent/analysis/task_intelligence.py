"""Deterministic task-intelligence capabilities for Gate E Wave 1.

These analyzers consume only canonical Task facts. They never infer missing AS21
history/dependency data: unavailable source facts are reported explicitly so the
Harness can fail closed or explain limited evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Iterable, Any

from po_agent.analysis.task_quality import TaskQualityAnalysis
from po_agent.domain.models import Task, TaskStatus


def _now_like(value: datetime) -> datetime:
    if value.tzinfo is None:
        return datetime.now()
    return datetime.now(value.tzinfo)


@dataclass(frozen=True)
class TaskIntelligenceAnalysis:
    quality: TaskQualityAnalysis = TaskQualityAnalysis()

    def missing_requirements(self, task: Task) -> dict[str, Any]:
        result = self.quality.analyze_deterministic(task)
        return {
            "task_key": task.key,
            "missing_elements": result["missing_elements"],
            "recommendations": result["recommendations"],
            "complete": not result["missing_elements"],
            "source_grounded": True,
        }

    def acceptance_analysis(self, task: Task) -> dict[str, Any]:
        result = self.quality.analyze_deterministic(task)
        rule = next(r for r in result["rules"] if r["id"] == "acceptance_expectations")
        return {
            "task_key": task.key,
            "testable": bool(rule["passed"]),
            "reason": None if rule["passed"] else rule["message"],
            "recommendation": None if rule["passed"] else "Добавить проверяемые критерии приемки",
            "source_grounded": True,
        }

    def dependency_analysis(self, task: Task) -> dict[str, Any]:
        dependencies = list(task.depends_on or [])
        return {
            "task_key": task.key,
            "depends_on": dependencies,
            "dependency_count": len(dependencies),
            "has_dependencies": bool(dependencies),
            "source_grounded": True,
            "evidence_limited": not bool(dependencies),
            "limitation": "canonical dependency list is empty; no dependency is invented" if not dependencies else None,
        }

    def history(self, task: Task) -> dict[str, Any]:
        transitions = sorted(task.status_transitions or [], key=lambda item: item.timestamp)
        return {
            "task_key": task.key,
            "transitions": [
                {
                    "from_status": item.from_status.value,
                    "to_status": item.to_status.value,
                    "timestamp": item.timestamp.isoformat(),
                    "author": item.author,
                }
                for item in transitions
            ],
            "transition_count": len(transitions),
            "history_available": bool(transitions),
            "source_grounded": True,
            "limitation": None if transitions else "canonical status history is unavailable; no history is invented",
        }

    def time_in_status(self, task: Task, now: datetime | None = None) -> dict[str, Any]:
        transitions = sorted(task.status_transitions or [], key=lambda item: item.timestamp)
        if not transitions:
            return {
                "task_key": task.key,
                "status": task.status.value,
                "hours": None,
                "history_available": False,
                "source_grounded": True,
                "limitation": "status history required for deterministic time-in-status",
            }
        start = transitions[-1].timestamp
        end = now or _now_like(start)
        return {
            "task_key": task.key,
            "status": task.status.value,
            "hours": max(0.0, (end - start).total_seconds() / 3600),
            "since": start.isoformat(),
            "history_available": True,
            "source_grounded": True,
        }

    def aging(self, task: Task, now: datetime | None = None, threshold_days: int = 14) -> dict[str, Any]:
        end = now or _now_like(task.created_at)
        age_days = max(0, (end - task.created_at).days)
        active = not task.is_completed
        return {
            "task_key": task.key,
            "age_days": age_days,
            "active": active,
            "threshold_days": threshold_days,
            "is_aging": active and age_days >= threshold_days,
            "source_grounded": True,
        }

    def blocker_analysis(self, task: Task) -> dict[str, Any]:
        status_blocked = task.status == TaskStatus.NEED_INFO
        dependencies = list(task.depends_on or [])
        return {
            "task_key": task.key,
            "blocked": status_blocked or bool(dependencies),
            "status_blocked": status_blocked,
            "dependency_evidence": dependencies,
            "source_grounded": True,
            "note": "dependencies are evidence candidates, not assumed unresolved blockers" if dependencies else None,
        }

    def similar_tasks(self, task: Task, corpus: Iterable[Task], threshold: float = 0.55, limit: int = 5) -> dict[str, Any]:
        needle = self._search_text(task)
        matches = []
        for candidate in corpus:
            if candidate.key == task.key:
                continue
            score = SequenceMatcher(None, needle, self._search_text(candidate)).ratio()
            if score >= threshold:
                matches.append({"task_key": candidate.key, "title": candidate.title, "similarity": round(score, 4)})
        matches.sort(key=lambda item: (-item["similarity"], item["task_key"]))
        return {
            "task_key": task.key,
            "threshold": threshold,
            "matches": matches[:limit],
            "candidate_count": len(matches),
            "source_grounded": True,
        }

    @staticmethod
    def _search_text(task: Task) -> str:
        return " ".join(filter(None, [task.title, task.description or ""])).casefold().strip()
