"""Generic normalization of human period references for sprint matching.

This module is lexical only: it maps month/year/period wording (e.g. "август",
"августовский спринт", "2026-08", "August 2026") to a (month, year) constraint.
It contains no entity names, spaces, sprint ids or routing rules. The identity
of a matching sprint is always proven from source data by the calling
capability; when several source sprints match, the caller must return typed
ambiguity instead of silently choosing one.
"""
from __future__ import annotations

import calendar
import re
from typing import Any, Mapping

# Generic month stems (Russian + English). Inflected and adjectival forms
# share a stable prefix with the stem ("августовский" -> "август").
_MONTH_STEMS_RU = (
    "январ", "феврал", "март", "апрел", "май", "июн",
    "июл", "август", "сентябр", "октябр", "ноябр", "декабр",
)
_MONTH_STEMS_EN = (
    "jan", "feb", "mar", "apr", "may", "jun",
    "jul", "aug", "sep", "oct", "nov", "dec",
)


def parse_period(reference: str) -> tuple[int | None, int | None]:
    """Return (month, year) for a human period reference.

    month is 1..12 or None; year is 1900..2100 or None. Returns (None, None)
    when no period is recognizable — the caller must clarify, not guess.
    """
    text = str(reference or "").casefold()
    tokens = re.findall(r"[a-zа-яё0-9][a-zа-яё0-9.\-]*", text)
    month: int | None = None
    year: int | None = None
    for token in tokens:
        if month is None:
            for index, stem in enumerate(_MONTH_STEMS_RU, start=1):
                if token.startswith(stem):
                    month = index
                    break
            if month is None:
                for index, stem in enumerate(_MONTH_STEMS_EN, start=1):
                    if token.startswith(stem):
                        month = index
                        break
        if year is None and re.fullmatch(r"(19|20)\d{2}", token):
            year = int(token)
    if month is None or year is None:
        # ISO-like "2026-08", "2026/08", "2026-08-16": YYYY-MM[-DD].
        iso = re.search(r"\b(19|20)(\d{2})[./\-](\d{2})(?:[./\-]\d{1,2})?\b", text)
        if iso:
            candidate_year = int(iso.group(1) + iso.group(2))
            candidate_month = int(iso.group(3))
            if year is None:
                year = candidate_year
            if month is None and 1 <= candidate_month <= 12:
                month = candidate_month
        # "08.2026" / "08/2026": MM.YYYY.
        if month is None and year is None:
            mmyy = re.search(r"\b(\d{2})[./](19|20)(\d{2})\b", text)
            if mmyy and 1 <= int(mmyy.group(1)) <= 12:
                month = int(mmyy.group(1))
                year = int(mmyy.group(2) + mmyy.group(3))
    if month is not None and not 1 <= month <= 12:
        month = None
    return month, year


def sprint_overlaps_period(
    sprint: Mapping[str, Any],
    month: int,
    year: int | None,
) -> bool:
    """True when the source sprint interval overlaps the referenced month.

    The sprint interval comes from source data (start_at/finish_at). When the
    reference carries no year, the month is matched against the sprint's own
    year span, so a year-less "август" only matches sprints that actually
    span an August.
    """
    start = _parse_dt(sprint.get("start_at"))
    finish = _parse_dt(sprint.get("finish_at"))
    if start is None or finish is None:
        # A source sprint without a readable period can never be proven to
        # match a period reference.
        return False
    years = range(start.year, finish.year + 1) if year is None else [year]
    for candidate_year in years:
        month_start = _dt(candidate_year, month, 1)
        last_day = calendar.monthrange(candidate_year, month)[1]
        month_end = _dt(candidate_year, month, last_day, 23, 59, 59)
        if start <= month_end and finish >= month_start:
            return True
    return False


def _parse_dt(value: Any):
    if not value or not isinstance(value, str):
        return None
    try:
        from datetime import datetime

        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _dt(year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0):
    from datetime import datetime

    return datetime(year, month, day, hour, minute, second)