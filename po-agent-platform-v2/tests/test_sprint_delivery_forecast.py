"""Source-complete deterministic forecast regression (no AS21 credentials)."""
from dataclasses import replace
from datetime import date, datetime, timezone

from po_agent.sprint.delivery_forecast import SprintForecastInput, forecast_sprint


UTC = timezone.utc


def sample(**kwargs):
    base = SprintForecastInput(
        sprint_key="PRD-SPRINT-5",
        sprint_start=date(2026, 10, 19),
        sprint_end=date(2026, 10, 30),
        as_of=datetime(2026, 10, 23, 18, tzinfo=UTC),
        scope_total=20,
        closed_total=5,
        closed_at=tuple(datetime(2026, 10, 19 + i, 16, tzinfo=UTC) for i in range(5)),
        complete_membership=True,
        complete_closure_timestamps=True,
        working_weekdays=(0, 1, 2, 3, 4),
    )
    return replace(base, **kwargs)


def test_forecast_is_current_scope_not_committed_predictability():
    report = forecast_sprint(sample())
    assert report["status"] == "READY"
    assert report["elapsed_workdays"] == 5
    assert report["remaining_workdays"] == 5
    assert report["forecast_completion_percent"] == 50.0
    assert report["committed_predictability"] is None
    assert report["forecast_scope_kind"] == "current_scope_not_committed"
    assert report["confidence_state"] == "heuristic_no_probability_claim"


def test_at_sprint_end_remaining_days_zero_no_fake_completed_scope():
    report = forecast_sprint(sample(
        as_of=datetime(2026, 10, 30, 19, tzinfo=UTC)))
    assert report["remaining_workdays"] == 0
    assert report["forecast_completion_percent"] == 25.0


def test_complete_zero_closures_is_insufficient_not_fabricated_zero():
    out = forecast_sprint(sample(closed_total=0, closed_at=()))
    assert out["status"] == "INSUFFICIENT_EVIDENCE"
    assert out["reason"] == "insufficient_closure_events"
    assert out["forecast"] is None


def test_source_outage_not_silent_zero():
    report = forecast_sprint(sample(source_available=False))
    assert report["status"] == "SOURCE_UNAVAILABLE"
    assert report["forecast"] is None


def test_non_real_source_cannot_claim_forecast():
    report = forecast_sprint(sample(source="LOCAL_CACHE"))
    assert report["status"] == "INSUFFICIENT_EVIDENCE"
    assert report["reason"] == "source_not_authoritative"


def test_reject_incomplete_or_incorrect_closure_evidence():
    cases = [
        ({"complete_membership": False}, "incomplete_sprint_membership"),
        ({"complete_closure_timestamps": False}, "incomplete_closure_history"),
        ({"closed_at": ()}, "closure_count_mismatch"),
        ({"closed_at": sample().closed_at + sample().closed_at[:1]}, "closure_count_mismatch"),
        ({"closed_at": (datetime(2026, 11, 1, tzinfo=UTC),) + sample().closed_at[1:]}, "closure_out_of_scope"),
        ({"closed_at": (datetime(2026, 10, 18, tzinfo=UTC),) + sample().closed_at[1:]}, "closure_out_of_scope"),
    ]
    for values, reason in cases:
        out = forecast_sprint(sample(**values))
        assert out["status"] == "INSUFFICIENT_EVIDENCE"
        assert out["reason"] == reason


def test_reject_unverified_calendar_and_naive_timestamps():
    assert forecast_sprint(sample(working_weekdays=None))["reason"] == "working_calendar_unverified"
    assert forecast_sprint(sample(working_weekdays=(0, 0)))["reason"] == "working_calendar_invalid"
    assert forecast_sprint(sample(as_of=datetime(2026, 10, 23)))["reason"] == "timezone_missing"
    assert forecast_sprint(sample(closed_at=(datetime(2026, 10, 19),) + sample().closed_at[1:]))["reason"] == "timezone_missing"


def test_invalid_scope_empty_and_future_start_fail_closed():
    assert forecast_sprint(sample(scope_total=4))["reason"] == "invalid_scope_counts"
    assert forecast_sprint(sample(scope_total=0, closed_total=0, closed_at=()))["reason"] == "empty_sprint_scope"
    assert forecast_sprint(sample(as_of=datetime(2026, 10, 18, tzinfo=UTC)))["reason"] == "sprint_not_started"
