"""Pure contract tests: AS21 identity and source version proof."""
import pytest

from app.services.sberproject.as21_point_adapter import normalize_as21_point_read
from app.services.sberproject.release_membership_contract import MembershipUnverified


def task():
    return {
        "task_code": "OLP-123",
        "unit": {
            "code": "OLP-123",
            "attributes": {
                "title": "Check Excel pivot",
                "workflow_status": {"name": "In Progress"},
                "assigned_to": {"name": "Developer"},
                "fix_version_s": [{"code": "verified-as21-version-uuid"}],
            },
        },
    }


def test_normalizes_one_verified_point_read():
    assert normalize_as21_point_read("OLP-123", task()) == {
        "key": "OLP-123",
        "title": "Check Excel pivot",
        "status": "In Progress",
        "assignee": "Developer",
        "fix_version_s": [{"code": "verified-as21-version-uuid"}],
    }


@pytest.mark.parametrize("mutation", [
    lambda p: p.update(task_code="DMS-3"),
    lambda p: p["unit"].update(code="DMS-3"),
    lambda p: p["unit"]["attributes"].update(fix_version_s=None),
    lambda p: p["unit"]["attributes"].update(fix_version_s=["a fake version"]),
    lambda p: p["unit"]["attributes"].update(fix_version_s=[{"name": "OLP 1.9"}]),
])
def test_fails_closed_on_missing_identity_or_version(mutation):
    value = task()
    mutation(value)
    with pytest.raises(MembershipUnverified):
        normalize_as21_point_read("OLP-123", value)


def test_unverified_missing_optional_labels_are_null():
    value = task()
    value["unit"]["attributes"].pop("title")
    value["unit"]["attributes"].pop("assigned_to")
    value["unit"]["attributes"].pop("workflow_status")
    normalized = normalize_as21_point_read("OLP-123", value)
    assert normalized["title"] is None
    assert normalized["assignee"] is None
    assert normalized["status"] is None


def test_rejects_forged_flat_task_without_unit_identity():
    with pytest.raises(MembershipUnverified):
        normalize_as21_point_read("OLP-123", {"task_code": "OLP-123", "unit": {}})
