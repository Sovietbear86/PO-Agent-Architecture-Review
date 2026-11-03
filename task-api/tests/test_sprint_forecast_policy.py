"""No AS21 or runtime effects: policy must be explicitly authorized."""
from datetime import datetime, timezone
import pytest

from app.services.sprint_forecast_policy import (
    SprintForecastPolicy, validate_forecast_policy,
)


def sample(**kwargs):
    from dataclasses import replace
    base = SprintForecastPolicy(
        timezone_name="Europe/Moscow",
        working_weekdays=(0, 1, 2, 3, 4),
        terminal_status_types=frozenset({"done"}),
        authority="product-owner-approved-configuration",
        approved_at=datetime(2026, 11, 2, tzinfo=timezone.utc),
    )
    return replace(base, **kwargs)


def test_explicit_contract_is_not_automatic_default():
    with pytest.raises(ValueError, match="forecast_product_policy_missing"):
        validate_forecast_policy(None)


def test_authorized_policy_keeps_exact_source_type_values():
    zone, weekdays, terminal = validate_forecast_policy(sample())
    assert str(zone) == "Europe/Moscow"
    assert weekdays == (0, 1, 2, 3, 4)
    assert terminal == frozenset({"done"})


@pytest.mark.parametrize("value,reason", [
    ({"authority": ""}, "forecast_policy_authority_missing"),
    ({"approved_at": datetime(2026, 11, 2)}, "forecast_policy_approval_unverified"),
    ({"timezone_name": ""}, "forecast_timezone_unconfigured"),
    ({"timezone_name": "Unknown/NoSuchZone"}, "forecast_timezone_invalid"),
    ({"working_weekdays": ()}, "forecast_working_calendar_missing"),
    ({"working_weekdays": (0, 0)}, "forecast_working_calendar_missing"),
    ({"working_weekdays": (True, 2)}, "forecast_working_calendar_invalid"),
    ({"terminal_status_types": frozenset()}, "forecast_terminal_policy_missing"),
    ({"terminal_status_types": frozenset({" done"})}, "forecast_terminal_policy_invalid"),
])
def test_invalid_policy_fails_closed(value, reason):
    with pytest.raises(ValueError, match=reason):
        validate_forecast_policy(sample(**value))


@pytest.mark.parametrize("weekdays", [
    ([], 1),
    ({}, 1),
    ([1], 2),
    ({"weekday": 1}, 3),
    (0, ["bad"]),
    (1, None),
])
def test_unhashable_or_malformed_weekdays_fail_closed(weekdays):
    with pytest.raises(ValueError, match="forecast_working_calendar_invalid"):
        validate_forecast_policy(sample(working_weekdays=weekdays))


def test_non_tuple_weekdays_fail_closed():
    with pytest.raises(ValueError, match="forecast_working_calendar_missing"):
        validate_forecast_policy(sample(working_weekdays=[0, 1, 2, 3, 4]))
