"""Composition + AS21 point read orchestration: no network or service state."""
import pytest

from app.services.sberproject.release_task_adapter import (
    fetch_linked_release_tasks_from_sources,
)
from app.services.sberproject.release_membership_contract import MembershipUnverified


def composition(p, v):
    return {
        "product": p, "version_id": v,
        "source_operation": "searchTaskCr",
        "source_complete": True,
        "source_has_more": False,
        "source_total": 2,
        "tasks": [
            {"issueKey": "OLP-123", "source": "swtr"},
            {"issueKey": None, "source": "project"},
        ],
    }


def point(key):
    return {
        "task_code": key,
        "unit": {"code": key, "attributes": {
            "title": "Excel pivot task",
            "workflow_status": {"name": "In Progress"},
            "fix_version_s": [{"code": "as21-version-uuid"}],
        }},
    }


def test_only_explicit_linked_as21_tasks_are_fetched():
    seen = []
    def read(key):
        seen.append(key)
        return point(key)

    output = fetch_linked_release_tasks_from_sources(
        product="OLP", version_id="OLP.78",
        as21_version_uuid="as21-version-uuid",
        fetch_composition_source=composition,
        fetch_as21_point_source=read,
    )
    assert seen == ["OLP-123"]
    assert output["linked_count"] == 1
    assert output["internal_without_as21_key"] == 1
    assert output["linked_tasks"][0]["status"] == "In Progress"
    assert output["membership_status"] == "PARTIAL_SOURCE_PROVEN"
    assert output["complete"] is False
    assert all(output[key] is None for key in (
        "scope", "completed", "wip", "readiness", "delivery_forecast",
    ))


def test_no_as21_calls_on_unproven_composition():
    def invalid(p, v):
        result = composition(p, v)
        result["source_complete"] = None
        return result

    def forbidden(_):
        raise AssertionError("must not call AS21 when composition is unverified")

    with pytest.raises(MembershipUnverified):
        fetch_linked_release_tasks_from_sources(
            product="OLP", version_id="OLP.78",
            as21_version_uuid="as21-version-uuid",
            fetch_composition_source=invalid,
            fetch_as21_point_source=forbidden,
        )


def test_rejects_wrong_as21_version_relation():
    def wrong(key):
        result = point(key)
        result["unit"]["attributes"]["fix_version_s"] = [{"code": "different-uuid"}]
        return result
    with pytest.raises(MembershipUnverified):
        fetch_linked_release_tasks_from_sources(
            product="OLP", version_id="OLP.78",
            as21_version_uuid="as21-version-uuid",
            fetch_composition_source=composition,
            fetch_as21_point_source=wrong,
        )
