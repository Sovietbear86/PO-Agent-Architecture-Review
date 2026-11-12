"""A230R3.58: gated API contract tests; no network, no live sources."""
import pytest
from fastapi import HTTPException

from app.routers import sberproject_read
from app.routers.sberproject_release_tasks import read_linked_tasks
from app.services.sberproject.release_membership_contract import MembershipUnverified


def test_route_registered_under_existing_facade():
    paths = [r.path for r in sberproject_read.router.routes]
    assert "/api/v1/sberproject-read/releases/{product}/{version_id}/linked-tasks" in paths


def test_missing_authoritative_as21_identity_fails_closed_before_sources():
    def forbidden(*args):
        raise AssertionError("No source calls without independently verified UUID")

    with pytest.raises(MembershipUnverified, match="as21_version_identity_unverified"):
        read_linked_tasks(
            product="OLP", version_id="OLP.78",
            release_reader=forbidden, point_reader=forbidden,
        )


def test_wrong_as21_version_identity_is_rejected():
    with pytest.raises(MembershipUnverified, match="as21_version_identity_unverified"):
        read_linked_tasks(
            product="OLP", version_id="OLP.78",
            version_resolver=lambda p, v: "",
        )


def test_does_not_read_as21_without_source_completeness():
    def source(p, v):
        return {
            "product": p, "version_id": v,
            "source_operation": "searchTaskCr",
            "source_complete": False,
            "source_has_more": False,
            "source_total": 1,
            "tasks": [{"issueKey": "OLP-1", "source": "swtr"}],
        }

    def forbidden(key):
        raise AssertionError("AS21 must not be called without source proof")

    with pytest.raises(MembershipUnverified, match="release_composition_unverified"):
        read_linked_tasks(
            product="OLP", version_id="OLP.78",
            release_reader=source,
            version_resolver=lambda p, v: "verified-as21-version-uuid",
            point_reader=forbidden,
        )


def test_rejects_invalid_release_id_before_any_resolver():
    with pytest.raises(MembershipUnverified, match="invalid_release_identity"):
        read_linked_tasks(
            product="OLP", version_id="../../etc/passwd",
            version_resolver=lambda p, v: "unused",
        )


@pytest.mark.asyncio
async def test_disabled_route_ignores_client_attempts(monkeypatch):
    from app.routers.sberproject_release_tasks import get_release_linked_tasks
    monkeypatch.delenv("SBERPROJECT_RELEASE_TASKS_ENABLED", raising=False)
    with pytest.raises(HTTPException) as exc:
        await get_release_linked_tasks("OLP", "OLP.78")
    assert exc.value.status_code == 503
    assert exc.value.detail["reason"] == "release_task_binding_not_enabled"
