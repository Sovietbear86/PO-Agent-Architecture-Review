"""Fail-closed, caller-authorized policy for sprint forecasting.

AS21 supplies current statusType but does not publish terminal categories.
An explicit product policy is required; observed values alone are not policy.
This module is offline-only and does not enable a live forecast endpoint.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass(frozen=True)
class SprintForecastPolicy:
    timezone_name: str
    working_weekdays: tuple[int, ...]
    terminal_status_types: frozenset[str]
    authority: str
    approved_at: datetime


def validate_forecast_policy(policy: SprintForecastPolicy | None) -> tuple[ZoneInfo, tuple[int, ...], frozenset[str]]:
    if not isinstance(policy, SprintForecastPolicy):
        raise ValueError("forecast_product_policy_missing")
    if not isinstance(policy.authority, str) or not policy.authority.strip():
        raise ValueError("forecast_policy_authority_missing")
    if not isinstance(policy.approved_at, datetime) or policy.approved_at.tzinfo is None:
        raise ValueError("forecast_policy_approval_unverified")
    if not isinstance(policy.timezone_name, str) or not policy.timezone_name.strip():
        raise ValueError("forecast_timezone_unconfigured")
    try:
        zone = ZoneInfo(policy.timezone_name)
    except (ZoneInfoNotFoundError, ValueError, TypeError) as exc:
        raise ValueError("forecast_timezone_invalid") from exc
    weekdays = policy.working_weekdays
    if not isinstance(weekdays, tuple) or not weekdays or len(set(weekdays)) != len(weekdays):
        raise ValueError("forecast_working_calendar_missing")
    if any(type(x) is not int or x not in range(7) for x in weekdays):
        raise ValueError("forecast_working_calendar_invalid")
    terminal = policy.terminal_status_types
    if not isinstance(terminal, frozenset) or not terminal:
        raise ValueError("forecast_terminal_policy_missing")
    if any(not isinstance(x, str) or not x or x != x.strip() for x in terminal):
        raise ValueError("forecast_terminal_policy_invalid")
    return zone, weekdays, terminal
