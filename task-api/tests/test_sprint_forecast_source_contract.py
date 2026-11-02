"""D2 source-boundary unit tests; no AS21/LLM/network access."""
import pytest

from app.services.sprint_forecast_source import (
    validate_complete_sprint_collection,
    complete_workflow_history,
)


def collection(**overrides):
    data = {"complete": True, "membership_proven": True,
            "complete_tasks": [{"source_id": "PRD-17", "source_data": {"sprint_membership_proven": True}}]}
    data.update(overrides)
    return data


def history(**overrides):
    data = {"task_code": "PRD-17",
            "page_info": {"complete": True, "has_next": False},
            "events": [{"task_code": "PRD-17", "field_code": "workflow_status",
                        "event_id": "e-1", "old_value": "In progress",
                        "new_value": "Done", "changed_at": "2026-10-21T15:00:00Z"},
                       {"task_code": "PRD-17", "field_code": "assigned_to",
                        "event_id": "e-2", "changed_at": "2026-10-21T15:01:00Z"}]}
    data.update(overrides)
    return data


def test_complete_collection_passes_with_proven_membership():
    assert len(validate_complete_sprint_collection(collection())) == 1


@pytest.mark.parametrize("change,reason", [
    ({"complete": False}, "sprint_membership_incomplete"),
    ({"membership_proven": False}, "sprint_membership_incomplete"),
    ({"complete_tasks": [collection()["complete_tasks"][0]] * 2}, "duplicate_or_missing_task_id"),
    ({"complete_tasks": [{"source_id": "PRD-17", "source_data": {}}]}, "task_sprint_membership_unproven"),
])
def test_collection_fail_closed(change, reason):
    with pytest.raises(ValueError, match=reason):
        validate_complete_sprint_collection(collection(**change))


def test_source_collection_limit():
    with pytest.raises(ValueError, match="sprint_membership_over_limit"):
        validate_complete_sprint_collection(collection(), max_tasks=0)


def test_workflow_history_preserves_only_authoritative_status_changes():
    events = complete_workflow_history(history(), "PRD-17")
    assert len(events) == 1
    assert events[0]["changed_at"] == "2026-10-21T15:00:00+00:00"


@pytest.mark.parametrize("change,reason", [
    ({"page_info": {"complete": False, "has_next": True}}, "task_history_incomplete"),
    ({"task_code": "PRD-99"}, "task_history_identity_mismatch"),
    ({"events": [{"task_code": "PRD-17", "field_code": "workflow_status", "changed_at": "bad"}]}, "invalid_closure_timestamp"),
    ({"events": [{"task_code": "PRD-17", "field_code": "workflow_status", "changed_at": "2026-10-21T15:00:00"}]}, "history_timezone_missing"),
])
def test_history_fail_closed(change, reason):
    with pytest.raises(ValueError, match=reason):
        complete_workflow_history(history(**change), "PRD-17")


@pytest.mark.parametrize('invalid_value', [None, [], 'invalid', 10, False])
def test_source_data_type_is_validated(invalid_value):
    payload = collection(complete_tasks=[{'source_id': 'PRD-17', 'source_data': invalid_value}])
    with pytest.raises(ValueError, match='task_sprint_membership_unproven'):
        validate_complete_sprint_collection(payload)


def test_missing_as21_event_id_uses_scoped_local_identity_not_source_id():
    payload = history(events=[{
        "task_code": "PRD-17", "field_code": "workflow_status",
        "event_id": None, "old_value": "In progress", "new_value": "Done",
        "changed_at": "2026-10-21T15:00:00Z",
    }])
    rows = complete_workflow_history(payload, "PRD-17")
    assert len(rows) == 1
    assert rows[0]["event_id"].startswith("local:")
    assert rows[0]["event_identity_source"] == "local"
    assert rows == complete_workflow_history(payload, "PRD-17")


def test_duplicate_no_id_transition_is_rejected_not_counted_twice():
    event = {
        "task_code": "PRD-17", "field_code": "workflow_status",
        "event_id": None, "old_value": "In progress", "new_value": "Done",
        "changed_at": "2026-10-21T15:00:00Z",
    }
    with pytest.raises(ValueError, match="duplicate_status_event"):
        complete_workflow_history(history(events=[event, dict(event)]), "PRD-17")


def test_no_id_missing_transition_fields_must_fail_closed():
    event = {
        "task_code": "PRD-17", "field_code": "workflow_status",
        "event_id": None, "new_value": "Done",
        "changed_at": "2026-10-21T15:00:00Z",
    }
    with pytest.raises(ValueError, match="status_event_identity_unverified"):
        complete_workflow_history(history(events=[event]), "PRD-17")


def test_authoritative_status_types_survive_source_validation():
    event = {
        "task_code": "PRD-17", "field_code": "workflow_status",
        "event_id": None, "old_value": "In progress", "new_value": "Resolved",
        "from_status_type": "IN_PROGRESS", "to_status_type": "DONE",
        "changed_at": "2026-10-21T15:00:00Z",
    }
    rows = complete_workflow_history(history(events=[event]), "PRD-17")
    assert rows[0]["to_status_type"] == "DONE"
    assert rows[0]["from_status_type"] == "IN_PROGRESS"
    assert rows[0]["event_identity_source"] == "local"


def test_unknown_status_type_does_not_get_guessed_from_display_name():
    event = {
        "task_code": "PRD-17", "field_code": "workflow_status",
        "event_id": None, "old_value": "In progress", "new_value": "Resolved",
        "changed_at": "2026-10-21T15:00:00Z",
    }
    rows = complete_workflow_history(history(events=[event]), "PRD-17")
    assert rows[0]["to_status_type"] is None
