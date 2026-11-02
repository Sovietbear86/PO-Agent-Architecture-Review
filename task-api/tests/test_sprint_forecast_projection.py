"""Deterministic source projection contract tests. Synthetic; no AS21 calls."""
from datetime import datetime, timezone

import pytest

from app.services.sprint_forecast_projection import verify_forecast_closure_inputs


AS_OF = datetime(2026, 10, 25, tzinfo=timezone.utc)


def sample():
    return {
        "sprint_id": "PRD-SPRNT-1", "complete": True, "membership_proven": True,
        "source": "REAL_AS21", "task_count": 2, "history_complete_count": 2,
        "history_by_task": {
            "PRD-1": [
                {"event_id": "e1", "changed_at": "2026-10-20T09:00:00+00:00"},
                {"event_id": "e2", "changed_at": "2026-10-21T09:00:00+00:00"},
            ],
            "PRD-2": [
                {"event_id": "e3", "changed_at": "2026-10-20T10:00:00+00:00"},
            ],
        },
    }


def project(data=None, *, current=None, events=None, terminal=None, at=AS_OF):
    return verify_forecast_closure_inputs(
        data if data is not None else sample(),
        current_status_types=current if current is not None else {"PRD-1": "DONE", "PRD-2": "IN_PROGRESS"},
        terminal_status_types=terminal if terminal is not None else frozenset({"DONE"}),
        event_status_types=events if events is not None else {
            "PRD-1": {"e1": "IN_PROGRESS", "e2": "DONE"},
            "PRD-2": {"e3": "IN_PROGRESS"},
        }, as_of=at)


def test_proven_closed_count_no_computed_forecast():
    x = project()
    assert x["closed_total"] == 1
    assert x["scope_total"] == 2
    assert x["closed_at_by_task"]["PRD-1"] == "2026-10-21T09:00:00+00:00"
    assert x["forecast"] is None
    assert x["committed_predictability"] is None


def test_reopening_invalidates_old_closure():
    data = sample()
    data["history_by_task"]["PRD-1"].append({
        "event_id": "e4", "changed_at": "2026-10-22T09:00:00+00:00"})
    out = project(
        data, current={"PRD-1": "IN_PROGRESS", "PRD-2": "IN_PROGRESS"},
        events={"PRD-1": {"e1": "IN_PROGRESS", "e2": "DONE", "e4": "IN_PROGRESS"},
                "PRD-2": {"e3": "IN_PROGRESS"}})
    assert out["closed_total"] == 0


@pytest.mark.parametrize("change,reason", [
    ({"complete": False}, "forecast_source_incomplete"),
    ({"source": "LOCAL_CACHE"}, "forecast_source_not_authoritative"),
    ({"membership_proven": False}, "forecast_source_not_authoritative"),
    ({"task_count": 9}, "forecast_scope_mismatch"),
    ({"history_complete_count": 1}, "forecast_history_incomplete"),
])
def test_source_mismatch_fails_closed(change, reason):
    with pytest.raises(ValueError, match=reason):
        project({**sample(), **change})


def test_missing_status_classification_fails_closed():
    with pytest.raises(ValueError, match="current_status_contract_incomplete"):
        project(current={"PRD-1": "DONE"})
    with pytest.raises(ValueError, match="event_status_contract_incomplete"):
        project(events={"PRD-1": {"e1": "IN_PROGRESS", "e2": "DONE"}})
    with pytest.raises(ValueError, match="terminal_status_contract_missing"):
        project(terminal=frozenset())


def test_mismatch_between_history_and_current_status_fails():
    with pytest.raises(ValueError, match="current_status_history_mismatch"):
        project(current={"PRD-1": "IN_PROGRESS", "PRD-2": "IN_PROGRESS"})


def test_missing_authoritative_transition_type_fails():
    with pytest.raises(ValueError, match="status_transition_type_unverified"):
        project(events={"PRD-1": {"e1": "IN_PROGRESS"}, "PRD-2": {"e3": "IN_PROGRESS"}})


def test_future_event_and_naive_as_of_fail():
    data = sample()
    data["history_by_task"]["PRD-1"][-1]["changed_at"] = "2026-12-21T09:00:00+00:00"
    with pytest.raises(ValueError, match="status_transition_outside_snapshot"):
        project(data)
    with pytest.raises(ValueError, match="forecast_as_of_timezone_missing"):
        project(at=datetime(2026, 10, 25))


def test_event_order_and_event_id_fail():
    data = sample()
    data["history_by_task"]["PRD-1"][1]["changed_at"] = "2026-10-19T09:00:00+00:00"
    with pytest.raises(ValueError, match="status_transition_order_unverified"):
        project(data)
    data = sample()
    data["history_by_task"]["PRD-1"][1]["event_id"] = "e1"
    with pytest.raises(ValueError, match="status_event_identity_unverified"):
        project(data)


def test_missing_terminal_closure_is_not_assumed():
    data = sample()
    data["history_by_task"]["PRD-1"] = []
    with pytest.raises(ValueError, match="terminal_closure_event_missing"):
        project(data, events={"PRD-1": {}, "PRD-2": {"e3": "IN_PROGRESS"}})


def test_source_status_type_binding_uses_exact_declared_lowercase():
    from app.services.sprint_forecast_projection import bind_source_status_types

    data = sample()
    data["history_by_task"]["PRD-1"][0]["to_status_type"] = "in_progress"
    data["history_by_task"]["PRD-1"][1]["to_status_type"] = "done"
    data["history_by_task"]["PRD-2"][0]["to_status_type"] = "in_progress"
    out = bind_source_status_types(
        data,
        current_status_types={"PRD-1": "done", "PRD-2": "in_progress"},
        terminal_status_types=frozenset({"done"}),
        as_of=AS_OF,
    )
    assert out["closed_total"] == 1
    assert out["closed_at_by_task"]["PRD-1"] == "2026-10-21T09:00:00+00:00"
    assert out["committed_predictability"] is None
    assert out["forecast"] is None


def test_source_binding_missing_status_type_fails_closed():
    from app.services.sprint_forecast_projection import bind_source_status_types

    data = sample()
    data["history_by_task"]["PRD-1"][0]["to_status_type"] = "in_progress"
    data["history_by_task"]["PRD-1"][1]["to_status_type"] = None
    data["history_by_task"]["PRD-2"][0]["to_status_type"] = "in_progress"
    with pytest.raises(ValueError, match="status_transition_type_unverified"):
        bind_source_status_types(
            data,
            current_status_types={"PRD-1": "done", "PRD-2": "in_progress"},
            terminal_status_types=frozenset({"done"}),
            as_of=AS_OF,
        )


def test_source_binding_never_guesses_terminal_set_from_labels():
    from app.services.sprint_forecast_projection import bind_source_status_types

    data = sample()
    for events in data["history_by_task"].values():
        for event in events:
            event["to_status_type"] = "done"
    with pytest.raises(ValueError, match="terminal_status_contract_missing"):
        bind_source_status_types(
            data,
            current_status_types={"PRD-1": "done", "PRD-2": "done"},
            terminal_status_types=frozenset(),
            as_of=AS_OF,
        )
