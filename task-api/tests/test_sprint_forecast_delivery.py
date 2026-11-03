"""Offline scalar Delivery Forecast contract: no AS21 calls, no task-key leaks."""
from datetime import date, datetime, timezone
from copy import deepcopy
import pytest

from app.services.sprint_forecast_delivery import approved_policy, scalar_delivery_forecast
from app.services.sprint_forecast_policy import SprintForecastPolicy


def proof():
    return {
        "sprint_id": "PRD-SPRNT-1", "source": "REAL_AS21",
        "status": "SOURCE_PROVEN", "scope_total": 6, "closed_total": 4,
        "snapshot_observed_at": "2026-10-27T12:00:00+00:00",
        "closed_at_by_task": {
            "PRD-1": "2026-10-20T10:00:00+00:00",
            "PRD-2": "2026-10-21T10:00:00+00:00",
            "PRD-3": "2026-10-22T10:00:00+00:00",
            "PRD-4": "2026-10-23T10:00:00+00:00",
        },
    }


def predict(p=None):
    return scalar_delivery_forecast(
        proof() if p is None else p, sprint_id="PRD-SPRNT-1",
        start=date(2026, 10, 19), end=date(2026, 10, 30),
        policy=approved_policy(),
    )


def test_owner_approved_policy_is_explicit_and_not_derived_from_as21():
    policy = approved_policy()
    assert policy.terminal_status_types == frozenset({"done"})
    assert policy.timezone_name == "Europe/Moscow"
    assert policy.working_weekdays == (0, 1, 2, 3, 4)
    assert policy.approved_at.tzinfo is not None


def test_ready_is_scalar_source_proven_without_task_keys_or_baseline():
    output = predict()
    assert output["status"] == "READY"
    assert output["source"] == "REAL_AS21"
    assert output["sprint_id"] == "PRD-SPRNT-1"
    assert output["scope_total"] == 6
    assert output["closed_total"] == 4
    assert output["committed_predictability"] is None
    assert 0 <= output["forecast_completion_percent"] <= 100
    assert "closed_at_by_task" not in output
    assert "history_by_task" not in output
    assert not any(key.startswith("PRD-") for key in output)


@pytest.mark.parametrize("mutate,reason", [
    ({"status": "READY"}, "forecast_provenance_unverified"),
    ({"source": "LOCAL_CACHE"}, "forecast_provenance_unverified"),
    ({"sprint_id": "PRD-SPRNT-2"}, "forecast_provenance_unverified"),
    ({"closed_total": 5}, "closure_count_mismatch"),
    ({"closed_total": True}, "invalid_scope_counts"),
    ({"scope_total": 3}, "invalid_scope_counts"),
    ({"snapshot_observed_at": "bad"}, "sprint_snapshot_unverified"),
    ({"snapshot_observed_at": "2026-10-27T12:00:00"}, "sprint_snapshot_timezone_missing"),
])
def test_malformed_proof_never_returns_numeric_forecast(mutate, reason):
    output = predict({**proof(), **mutate})
    assert output["status"] == "INSUFFICIENT_EVIDENCE"
    assert output["reason"] == reason
    assert output["forecast_completion_percent"] is None
    assert output["committed_predictability"] is None


def test_future_close_fails_closed():
    p = proof()
    p["closed_at_by_task"]["PRD-4"] = "2100-10-23T10:00:00+00:00"
    out = predict(p)
    assert out["reason"] == "closure_out_of_scope"
    assert out["forecast_completion_percent"] is None


def test_missing_timestamp_for_closed_member_fails_closed():
    p = proof()
    p["closed_at_by_task"].pop("PRD-4")
    assert predict(p)["reason"] == "closure_count_mismatch"


def test_incomplete_observation_does_not_fake_zero():
    p = proof()
    p["closed_total"] = 1
    p["closed_at_by_task"] = {"PRD-1": "2026-10-20T10:00:00+00:00"}
    out = predict(p)
    assert out["status"] == "INSUFFICIENT_EVIDENCE"
    assert out["reason"] == "insufficient_closure_events"


def test_different_policy_is_not_silently_assumed():
    policy = SprintForecastPolicy(
        timezone_name="Europe/Moscow",
        working_weekdays=(0, 1, 2, 3, 4),
        terminal_status_types=frozenset({"done"}),
        authority="",
        approved_at=datetime(2026, 11, 3, tzinfo=timezone.utc),
    )
    with pytest.raises(ValueError, match="forecast_policy_authority_missing"):
        scalar_delivery_forecast(
            proof(), sprint_id="PRD-SPRNT-1", start=date(2026, 10, 19),
            end=date(2026, 10, 30), policy=policy,
        )
