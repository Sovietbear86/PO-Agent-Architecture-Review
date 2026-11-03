"""Offline source-proof → calculator adapter contract tests."""
from datetime import date, datetime, timezone

import pytest

from po_agent.sprint.delivery_forecast_adapter import forecast_from_proven_closures


AS_OF = datetime(2026, 10, 27, 12, tzinfo=timezone.utc)


def source_proof():
    return {
        "status": "SOURCE_PROVEN",
        "source": "REAL_AS21",
        "sprint_id": "PRD-SPRNT-1",
        "scope_total": 6,
        "closed_total": 4,
        "closed_at_by_task": {
            "PRD-1": "2026-10-20T12:00:00Z",
            "PRD-2": "2026-10-21T12:00:00Z",
            "PRD-3": "2026-10-22T12:00:00Z",
            "PRD-4": "2026-10-23T12:00:00Z",
        },
        "forecast": None,
        "committed_predictability": None,
    }


def run(proof=None, **overrides):
    args = {
        "sprint_start": date(2026, 10, 19),
        "sprint_end": date(2026, 10, 30),
        "as_of": AS_OF,
        "product_timezone": "Europe/Moscow",
        "working_weekdays": (0, 1, 2, 3, 4),
    }
    args.update(overrides)
    return forecast_from_proven_closures(
        source_proof() if proof is None else proof, **args)


def test_calculates_from_source_proof_without_committed_baseline():
    x = run()
    assert x["status"] == "READY"
    assert x["scope_total"] == 6
    assert x["closed_total"] == 4
    assert x["forecast_scope_kind"] == "current_scope_not_committed"
    assert x["committed_predictability"] is None


@pytest.mark.parametrize("changed,reason", [
    ({"status": "READY"}, "closure_provenance_missing"),
    ({"source": "LOCAL_CACHE"}, "closure_provenance_missing"),
    ({"closed_total": 5}, "closure_count_mismatch"),
    ({"scope_total": 2}, "invalid_scope_counts"),
    ({"closed_at_by_task": {"PRD-1": "not a date"}, "closed_total": 1}, "closure_evidence_malformed"),
    ({"closed_at_by_task": {"PRD-1": "2026-10-20T09:00:00"}, "closed_total": 1}, "closure_timezone_missing"),
])
def test_invalid_proof_never_looks_like_forecast(changed, reason):
    value = run({**source_proof(), **changed})
    assert value["status"] == "INSUFFICIENT_EVIDENCE"
    assert value["reason"] == reason
    assert value["forecast"] is None


@pytest.mark.parametrize("config,reason", [
    ({"product_timezone": "Bad/Fake"}, "product_timezone_invalid"),
    ({"working_weekdays": ([1], 2)}, "working_calendar_unverified"),
    ({"working_weekdays": (True, 1)}, "working_calendar_unverified"),
    ({"working_weekdays": ()}, "working_calendar_unverified"),
    ({"as_of": datetime(2026, 10, 27)}, "timezone_missing"),
])
def test_invalid_product_config_fails_closed(config, reason):
    x = run(**config)
    assert x["status"] == "INSUFFICIENT_EVIDENCE"
    assert x["reason"] == reason
    assert x["forecast"] is None


def test_reopened_task_omitted_from_verified_closures():
    proof = source_proof()
    proof["closed_total"] = 3
    proof["closed_at_by_task"].pop("PRD-4")
    x = run(proof)
    assert x["status"] == "READY"
    assert x["closed_total"] == 3
    assert x["committed_predictability"] is None


def test_out_of_sprint_closure_does_not_produce_forecast():
    proof = source_proof()
    proof["closed_at_by_task"]["PRD-4"] = "2026-10-31T23:00:00Z"
    x = run(proof)
    assert x["status"] == "INSUFFICIENT_EVIDENCE"
    assert x["reason"] == "closure_out_of_scope"
