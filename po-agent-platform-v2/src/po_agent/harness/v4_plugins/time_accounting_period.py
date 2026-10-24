"""A230R3.1: source-filtered person/date worklogs — additive V4 plugin.

Uses AS21 timesheet report by worklog AUTHOR externalId, not task assignee.
Never falls back to creation-date task search or per-task scans.
"""
from __future__ import annotations

import re
from datetime import date, timedelta, datetime
from typing import Any
from zoneinfo import ZoneInfo

from ..agent_core_v4 import CapabilitySpecV4, SkillSpecV4, V4CapabilityUnavailable, V4NeedsClarification
from ..agent_core_v4_completion import CompletionRequirement
from ..contracts import CapabilityResult, Evidence
from ..v4_plugin_registry import CapabilityBindingV4, UIContractV4, V4SkillPlugin

_MOSCOW = ZoneInfo("Europe/Moscow")


def parse_worklog_period(args: dict[str, str], today: date | None = None) -> tuple[str, str]:
    """Explicit inclusive dates or last N calendar days/weeks, never creation dates."""
    current = today or datetime.now(_MOSCOW).date()
    raw_from = str(args.get("date_from") or args.get("from") or "").strip()
    raw_to = str(args.get("date_to") or args.get("to") or "").strip()
    period = str(args.get("period") or args.get("date_range") or "").casefold().strip()
    if raw_from and raw_to:
        def parse_date(value: str) -> date:
            if value.casefold() in {"сегодня", "today"}:
                return current
            try:
                return date.fromisoformat(value)
            except ValueError:
                return datetime.strptime(value, "%d.%m.%Y").date()
        try:
            start, finish = parse_date(raw_from), parse_date(raw_to)
        except ValueError as exc:
            raise V4NeedsClarification("Укажите даты списаний в формате ДД.ММ.ГГГГ или ГГГГ-ММ-ДД.") from exc
    else:
        # A complete two-date natural-language range can be in a single field.
        tokens = re.findall(r"\b(?:\d{2}\.\d{2}\.\d{4}|\d{4}-\d{2}-\d{2})\b", period)
        if len(tokens) == 2:
            return parse_worklog_period({"date_from": tokens[0], "date_to": tokens[1]}, current)
        one = re.search(r"\bс\s+(\d{2}\.\d{2}\.\d{4}|\d{4}-\d{2}-\d{2})\s+по\s+(?:сегодня|today)\b", period)
        if one:
            return parse_worklog_period({"date_from": one.group(1), "date_to": "сегодня"}, current)
        fixed = {
            "сегодня": (current, current),
            "today": (current, current),
            "вчера": (current - timedelta(days=1), current - timedelta(days=1)),
            "за неделю": (current - timedelta(days=6), current),
            "последняя неделя": (current - timedelta(days=6), current),
            "за месяц": (current - timedelta(days=29), current),
            "последний месяц": (current - timedelta(days=29), current),
            "этот месяц": (current.replace(day=1), current),
        }
        if period in fixed:
            start, finish = fixed[period]
            return start.isoformat(), finish.isoformat()
        match = re.fullmatch(
            r"(?:за\s+|в\s+|за\s+последние\s+|последние\s+|последних\s+)?"
            r"(\d{1,3})\s*(недел[ьюияь]?|недели|недель|weeks?|дн(?:я|ей|и)|days?)",
            period,
        )
        if match is None:
            raise V4NeedsClarification(
                "Уточните период списаний: например, «за последние 2 недели» "
                "или «с 01.10.2026 по сегодня»."
            )
        n = int(match.group(1))
        unit = match.group(2)
        days = n * 7 if unit.startswith("недел") or unit.startswith("week") else n
        if days < 1 or days > 366:
            raise V4NeedsClarification("Период списаний должен быть от 1 до 366 дней.")
        start, finish = current - timedelta(days=days - 1), current
    if start > finish or finish > current or (finish - start).days > 366:
        raise V4NeedsClarification("Период списаний должен быть упорядоченным, не более 366 дней и без будущих дат.")
    return start.isoformat(), finish.isoformat()


def build_member_worklogs_period(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        member = str(args.get("member_login") or "").strip()
        if not member:
            raise V4NeedsClarification("Укажите сотрудника, чьи списания нужно показать.")
        reader = getattr(runtime.adapter, "get_member_worklogs_period", None)
        if reader is None:
            raise V4CapabilityUnavailable("Получение списаний сотрудника за произвольный период недоступно в источнике.")
        start, finish = parse_worklog_period(args)
        space = str(args.get("space") or "").strip().upper() or None
        unit = str(args.get("unit") or "").strip().upper() or None
        try:
            result = await reader(member, start, finish, space=space, unit=unit)
        except Exception as exc:
            # Do not mask AS21 source failure as real zero hours.
            raise V4CapabilityUnavailable("REAL AS21 не подтвердил полный отчёт по списаниям сотрудника.") from exc
        if result.get("complete") is not True or result.get("source") != "REAL_AS21":
            raise V4CapabilityUnavailable("Неполные данные REAL AS21: сумма списаний недостоверна.")
        rows = result.get("entries")
        if not isinstance(rows, list):
            raise V4CapabilityUnavailable("REAL AS21 не вернул подтверждённый список списаний.")
        total = result.get("total_hours")
        if not isinstance(total, (float, int)) or len(rows) != result.get("worklog_count"):
            raise V4CapabilityUnavailable("Некорректная агрегация списаний.")
        evidence = [
            Evidence(type="worklog", source="as21", entity_id=str(row.get("id") or ""),
                     label=str(row.get("date") or ""), value=row.get("duration_hours"))
            for row in rows
        ]
        if not evidence:
            evidence = [Evidence(type="worklog_report", source="as21",
                                 entity_id=member, label="Полный отчёт REAL AS21", value=0)]
        scope = f" в {space}" if space else ""
        return CapabilityResult(
            answer=(f"Списания {member}{scope} с {start} по {finish}: "
                    f"{len(rows)} записей, {float(total):g} ч."
                    + (" Нулевой результат подтверждён полным отчётом AS21." if not rows else "")),
            data={**result, "period_start": start, "period_finish": finish,
                  "worklogs": rows, "source": "REAL_AS21"},
            evidence=evidence,
        )
    return execute


CAPABILITIES = (
    CapabilitySpecV4(
        "member.worklogs_period",
        "List actual time worklogs of one canonical employee by logged-on date range, optionally space and unit. No sprint needed.",
        {
            "member_login": "required canonical externalId from member.resolve",
            "period": "date range, e.g. 'за последние 2 недели', or use date_from and date_to",
            "date_from": "optional inclusive start YYYY-MM-DD, when period not supplied",
            "date_to": "optional inclusive end YYYY-MM-DD, when period not supplied",
            "space": "optional AS21 product space",
            "unit": "optional AS21 task unit",
        },
    ),
)
SKILLS = (
    SkillSpecV4(
        "member.worklogs_period",
        "Show actual logged work hours and entries of one employee for any explicit or relative calendar period, without requiring a sprint.",
        (
            "For requests about person worklogs by date ('списания за 2 недели', 'с даты по сегодня'), use this skill, NEVER task.search_created, task.search or member.worklogs with a mandatory sprint.",
            "Resolve the employee to canonical AS21 worklog author externalId with member.resolve. Keep optional space and unit constraints, never silently broaden.",
            "Pass relative wording as period or two explicit dates as date_from/date_to. These are WORKLOG dates, not task creation or sprint dates.",
            "Call member.worklogs_period. Zero hours may be reported only when source pagination is complete. If date is missing, ask ONLY for period, preserving member/space context.",
        ),
        ("member.resolve", "member.worklogs_period"),
        completion=(CompletionRequirement("member.worklogs_period",
            data_keys=("member_login", "date_from", "date_to", "worklog_count", "complete"),
            covers_resolved_constraints=True),),
    ),
)
BINDINGS = (
    CapabilityBindingV4("member.worklogs_period", handler_builder=build_member_worklogs_period),
)
UI = {
    "member.worklogs_period": UIContractV4(
        "analysis", preferred_widget="member_worklogs_period",
        required_fields=("member_login", "worklog_count", "total_hours", "complete"),
    ),
}
PLUGIN = V4SkillPlugin(
    plugin_id="builtin.time_accounting.period",
    skills=SKILLS, capabilities=CAPABILITIES, bindings=BINDINGS, ui=UI,
)
