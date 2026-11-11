"""Single version source bridge contract. No network, no credentials."""
import importlib.util
import sys
import types
from pathlib import Path

import pytest

base = Path(__file__).resolve().parents[1] / "app/services/sberproject"

# Import directly from package if available in repository test runtime.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.sberproject.release_task_adapter import fetch_linked_release_tasks
from app.services.sberproject.release_membership_contract import MembershipUnverified


def source(product, version):
    return {"product": product, "version_id": version, "complete": True, "tasks": [
        {"issueKey": "STS-579398", "source": "swtr"},
        {"issueKey": "STS-579399", "source": "swtr"},
        {"issueKey": None},
        {"issueKey": None},
    ]}


def task(key):
    return {"key": key, "fix_version_s": [{"code": "uuid-1"}],
            "title": "Example task", "status": "in progress", "assignee": "Test"}


def test_one_version_only_and_no_fake_release_metrics():
    seen = []
    def read_task(key):
        seen.append(key)
        return task(key)
    result = fetch_linked_release_tasks(product="OLP", version_id="OLP.78",
        as21_version_uuid="uuid-1", fetch_release=source, fetch_as21_task=read_task)
    assert seen == ["STS-579398", "STS-579399"]
    assert result["membership_status"] == "PARTIAL_SOURCE_PROVEN"
    assert result["linked_count"] == 2
    assert result["internal_without_as21_key"] == 2
    assert not result["complete"]
    assert all(result[x] is None for x in ("scope", "completed", "wip", "readiness", "delivery_forecast"))


def test_incomplete_source_never_point_reads():
    called = []
    def incomplete(product, version):
        result = source(product, version)
        result["complete"] = False
        return result
    with pytest.raises(MembershipUnverified):
        fetch_linked_release_tasks(product="OLP", version_id="OLP.78",
            as21_version_uuid="uuid-1", fetch_release=incomplete,
            fetch_as21_task=lambda key: called.append(key))
    assert not called


def test_wrong_task_version_fails_closed():
    with pytest.raises(MembershipUnverified):
        fetch_linked_release_tasks(product="OLP", version_id="OLP.78",
            as21_version_uuid="uuid-other", fetch_release=source, fetch_as21_task=task)


def test_excessive_release_scope_rejected_before_reads():
    called = []
    def huge(p, v):
        return {"product": p, "version_id": v, "complete": True,
                "tasks": [{"issueKey": f"STS-{i}", "source": "swtr"} for i in range(101)]}
    with pytest.raises(MembershipUnverified):
        fetch_linked_release_tasks(product="OLP", version_id="OLP.78",
            as21_version_uuid="uuid-1", fetch_release=huge,
            fetch_as21_task=lambda key: called.append(key))
    assert called == []


def test_duplicate_link_fails_before_point_reads():
    called = []
    def dup(p, v):
        s = source(p, v)
        s["tasks"].append({"issueKey": "STS-579398", "source": "swtr"})
        return s
    with pytest.raises(MembershipUnverified):
        fetch_linked_release_tasks(product="OLP", version_id="OLP.78",
            as21_version_uuid="uuid-1", fetch_release=dup,
            fetch_as21_task=lambda key: called.append(key))
    assert not called
