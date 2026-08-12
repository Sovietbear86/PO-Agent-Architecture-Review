"""Deterministic task-definition quality analysis.

The score measures how well a task is *stated*, not whether it is currently
assigned, labelled, attached to files, or moved through workflow. Operational
metadata must not lower the quality score of an otherwise well-written task.

LLM explanation is intentionally outside this service. The Harness may ask an
LLM to explain this immutable deterministic result, but an LLM never calculates
or changes the score.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from po_agent.domain.models import Task


@dataclass(frozen=True)
class QualityRuleResult:
    id: str
    passed: bool
    penalty: int
    message: str
    recommendation: str | None = None


class TaskQualityAnalysis:
    """Evaluate task statement quality using stable, auditable rules."""

    ACCEPTANCE_MARKERS = (
        "acceptance",
        "критерии приемки",
        "критерии приёмки",
        "готово когда",
        "definition of done",
        "dod",
        "ожидаемый результат",
    )
    CONTEXT_MARKERS = (
        "цель",
        "проблем",
        "зачем",
        "контекст",
        "business",
        "бизнес",
        "пользователь",
    )

    def analyze_deterministic(self, task: Task) -> dict[str, Any]:
        title = (task.title or "").strip()
        description = (task.description or "").strip()
        normalized = description.casefold()

        rules = [
            self._rule(
                "title_present",
                bool(title),
                25,
                "Не указан заголовок задачи",
                "Добавить короткий предметный заголовок",
            ),
            self._rule(
                "title_specific",
                len(title) >= 10,
                10,
                "Заголовок слишком короткий и может быть неоднозначным",
                "Уточнить объект и ожидаемое изменение в заголовке",
            ),
            self._rule(
                "description_present",
                bool(description),
                25,
                "Отсутствует описание задачи",
                "Описать цель, требуемое изменение и ожидаемый результат",
            ),
            self._rule(
                "description_substantive",
                len(description) >= 40,
                15,
                "Описание слишком короткое для однозначной постановки",
                "Добавить контекст и конкретику о требуемом результате",
            ),
            self._rule(
                "goal_or_context",
                self._contains_any(normalized, self.CONTEXT_MARKERS) or len(description) >= 120,
                10,
                "Неочевидны цель или контекст задачи",
                "Добавить зачем нужна задача / какую проблему она решает",
            ),
            self._rule(
                "acceptance_expectations",
                self._contains_any(normalized, self.ACCEPTANCE_MARKERS)
                or self._has_structured_expectations(description),
                15,
                "Не найдены проверяемые ожидания или критерии приемки",
                "Добавить критерии, по которым можно однозначно принять результат",
            ),
        ]

        score = max(0, 100 - sum(rule.penalty for rule in rules if not rule.passed))
        if score >= 85:
            level = "good"
        elif score >= 65:
            level = "fair"
        elif score >= 40:
            level = "poor"
        else:
            level = "very_poor"

        missing = [rule.id for rule in rules if not rule.passed]
        issues = [rule.message for rule in rules if not rule.passed]
        recommendations = [
            rule.recommendation
            for rule in rules
            if not rule.passed and rule.recommendation
        ]

        return {
            "score": score,
            "quality_level": level,
            "missing_elements": missing,
            "issues": issues,
            "recommendations": recommendations,
            "rules": [
                {
                    "id": rule.id,
                    "passed": rule.passed,
                    "penalty": rule.penalty if not rule.passed else 0,
                    "message": rule.message,
                }
                for rule in rules
            ],
            "metrics": {
                "title_length": len(title),
                "description_length": len(description),
            },
        }

    def calculate_quality_score(self, task: Task) -> int:
        return int(self.analyze_deterministic(task)["score"])

    def generate_quality_report(self, task: Task) -> dict[str, Any]:
        analysis = self.analyze_deterministic(task)
        return {
            "task_key": task.key,
            "task_title": task.title,
            **analysis,
        }

    @staticmethod
    def _rule(
        rule_id: str,
        passed: bool,
        penalty: int,
        message: str,
        recommendation: str | None,
    ) -> QualityRuleResult:
        return QualityRuleResult(rule_id, passed, penalty, message, recommendation)

    @staticmethod
    def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
        return any(marker in text for marker in markers)

    @staticmethod
    def _has_structured_expectations(description: str) -> bool:
        if not description:
            return False
        bullet_lines = sum(
            1
            for line in description.splitlines()
            if re.match(r"^\s*(?:[-*•]|\d+[.)])\s+", line)
        )
        return bullet_lines >= 2
