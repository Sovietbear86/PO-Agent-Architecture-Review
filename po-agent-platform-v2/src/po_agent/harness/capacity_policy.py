"""Owner-approved default capacity policy for 2026 Russia.

The policy intentionally follows the product-owner formula:
average 2026 working days per month * 0.87 * 8 hours/day.

Official 2026 production calendar:
- 247 working days
- 40-hour week => 8 hours/day baseline

This is a product policy baseline, not a REAL AS21 fact.
"""
from __future__ import annotations

RU_2026_WORKING_DAYS = 247
MONTHS_PER_YEAR = 12
WEEKLY_HOURS = 40.0
WORKDAYS_PER_WEEK = 5.0
DAILY_HOURS = WEEKLY_HOURS / WORKDAYS_PER_WEEK
AVAILABLE_CAPACITY_FACTOR = 0.87
DAYS_PER_YEAR_2026 = 365
ANNUAL_AVAILABLE_CAPACITY_HOURS_2026 = (
    RU_2026_WORKING_DAYS * DAILY_HOURS * AVAILABLE_CAPACITY_FACTOR
)
AVERAGE_AVAILABLE_CAPACITY_HOURS_PER_CALENDAR_DAY_2026 = (
    ANNUAL_AVAILABLE_CAPACITY_HOURS_2026 / DAYS_PER_YEAR_2026
)

AVERAGE_WORKING_DAYS_PER_MONTH_2026 = RU_2026_WORKING_DAYS / MONTHS_PER_YEAR
DEFAULT_AVAILABLE_WORKING_DAYS_PER_MONTH_2026 = (
    AVERAGE_WORKING_DAYS_PER_MONTH_2026 * AVAILABLE_CAPACITY_FACTOR
)
DEFAULT_AVAILABLE_CAPACITY_HOURS_PER_MONTH_2026 = round(
    DEFAULT_AVAILABLE_WORKING_DAYS_PER_MONTH_2026 * DAILY_HOURS,
    2,
)

CAPACITY_POLICY_ID = "RU_2026_AVG_WORKDAYS_X_0_87_40H_WEEK"


def default_monthly_capacity() -> dict[str, float | int | str]:
    return {
        "policy_id": CAPACITY_POLICY_ID,
        "working_days_2026": RU_2026_WORKING_DAYS,
        "average_working_days_per_month": round(AVERAGE_WORKING_DAYS_PER_MONTH_2026, 4),
        "availability_factor": AVAILABLE_CAPACITY_FACTOR,
        "weekly_hours": WEEKLY_HOURS,
        "daily_hours": DAILY_HOURS,
        "available_working_days_per_month": round(DEFAULT_AVAILABLE_WORKING_DAYS_PER_MONTH_2026, 4),
        "available_capacity_hours_per_month": DEFAULT_AVAILABLE_CAPACITY_HOURS_PER_MONTH_2026,
        "source": "OWNER_POLICY",
    }


def available_capacity_for_calendar_days(calendar_days: float) -> dict[str, float | int | str]:
    """Owner-policy capacity normalized to an arbitrary calendar-length window.

    The product policy deliberately uses the 2026 annual average workday density
    rather than a date-specific holiday calendar. This keeps the denominator
    consistent with the owner's "average working days in 2026 × 0.87" rule.
    """
    days = max(float(calendar_days), 0.0)
    hours = days * AVERAGE_AVAILABLE_CAPACITY_HOURS_PER_CALENDAR_DAY_2026
    return {
        **default_monthly_capacity(),
        "calendar_days": round(days, 4),
        "available_capacity_hours_for_period": round(hours, 2),
        "normalization": "2026_annual_average_workday_density",
    }
