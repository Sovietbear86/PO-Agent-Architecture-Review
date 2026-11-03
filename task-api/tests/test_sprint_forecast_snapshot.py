"""Offline current statusType snapshot validation; no source calls or writes."""
import pytest

from app.services.sprint_forecast_snapshot import extract_sprint_current_status_types


def _item(key="PRD-1", value=None):
    if value is None:
        value = {"name": "Resolved", "statusType": "done"}
    return {
        "source_id": key,
        "status": "Resolved",  # human-language status NEVER used as a type
        "source_data": {
            "sprint_membership_proven": True,
            "swtr_attributes": [{"code": "workflow_status", "value": value}],
        },
    }


def _sprint(*tasks):
    return {
        "sprint_id": "PRD-SPRNT-1",
        "complete": True,
        "membership_proven": True,
        "complete_tasks": list(tasks) if tasks else [_item()],
    }


def test_source_declared_type_is_exact_case_and_does_not_use_display_status():
    row = _sprint(_item(), _item("PRD-2", {"name": "В работе", "statusType": "in_progress"}))
    assert extract_sprint_current_status_types(row) == {"PRD-1": "done", "PRD-2": "in_progress"}


def test_same_declared_type_in_duplicate_attribute_is_safe():
    row = _sprint(_item())
    row["complete_tasks"][0]["source_data"]["swtr_attributes"].append(
        {"code": "workflow_status", "value": {"name": "Закрыто", "statusType": "done"}})
    assert extract_sprint_current_status_types(row) == {"PRD-1": "done"}


@pytest.mark.parametrize("value", [
    {"name": "Resolved"}, {"name": "Resolved", "statusType": None},
    {"name": "Resolved", "statusType": []}, "done", 17, {},
    {"name": "Resolved", "statusType": " done "},
])
def test_missing_or_malformed_type_fails_closed(value):
    with pytest.raises(ValueError, match="current_status_type_unverified"):
        extract_sprint_current_status_types(_sprint(_item(value=value)))


def test_only_display_status_fails_closed():
    row = _sprint(_item())
    row["complete_tasks"][0]["source_data"]["swtr_attributes"] = []
    with pytest.raises(ValueError, match="current_status_type_unverified"):
        extract_sprint_current_status_types(row)


def test_conflicting_types_fail_closed():
    row = _sprint(_item())
    row["complete_tasks"][0]["source_data"]["swtr_attributes"].append(
        {"code": "workflow_status", "value": {"statusType": "in_progress"}})
    with pytest.raises(ValueError, match="current_status_type_conflict"):
        extract_sprint_current_status_types(row)


def test_missing_attributes_does_not_guess_status():
    row = _sprint(_item())
    row["complete_tasks"][0]["source_data"].pop("swtr_attributes")
    with pytest.raises(ValueError, match="current_status_source_missing"):
        extract_sprint_current_status_types(row)


def test_incomplete_scope_must_fail_before_extraction():
    row = _sprint(_item())
    row["complete"] = False
    with pytest.raises(ValueError, match="sprint_membership_incomplete"):
        extract_sprint_current_status_types(row)


def test_snapshot_excludes_unscoped_tasks_and_bad_identity():
    row = _sprint(_item(), _item())
    with pytest.raises(ValueError, match="duplicate_or_missing_task_id"):
        extract_sprint_current_status_types(row)


def test_nested_status_type_code_is_source_declared():
    row = _sprint(_item(value={"statusType": {"code": "done"}}))
    assert extract_sprint_current_status_types(row) == {"PRD-1": "done"}


def test_non_dict_payload_fails_closed():
    with pytest.raises(ValueError, match="sprint_source_malformed"):
        extract_sprint_current_status_types(None)
