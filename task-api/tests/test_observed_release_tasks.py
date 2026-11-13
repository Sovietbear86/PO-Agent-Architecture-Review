"""Observed links remain partial even when real AS21 point reads succeed."""
import pytest
from fastapi import HTTPException

from app.services.sberproject.release_observations import observed_release_links
from app.services.sberproject.release_membership_contract import MembershipUnverified
from app.routers import sberproject_release_tasks as route


def observed_payload():
    return {"results": [
        {"issueKey": "OLP-12", "source": "swtr"},
        {"issueKey": None, "source": "project"},
    ], "meta": {"total": 2, "has_more": False}}


def test_cli_defaults_not_treated_as_full_release():
    result = observed_release_links(product="OLP", version_id="OLP.78", payload=observed_payload())
    assert result["membership_status"] == "OBSERVED_LINKS_UNVERIFIED"
    assert result["complete"] is False
    assert result["observed_count"] == 1
    assert result["scope"] is None
    assert result["readiness"] is None


def test_rejects_wrong_version_and_duplicate_keys():
    with pytest.raises(MembershipUnverified):
        observed_release_links(
            product="OLP", version_id="OLP.78",
            payload={**observed_payload(), "versionId": "OLP.79"},
        )
    with pytest.raises(MembershipUnverified):
        observed_release_links(
            product="OLP", version_id="OLP.78",
            payload={"results": [{"issueKey": "OLP-12", "source": "swtr"}] * 2},
        )


@pytest.mark.asyncio
async def test_default_disabled(monkeypatch):
    monkeypatch.delenv("SBERPROJECT_RELEASE_OBSERVATIONS_ENABLED", raising=False)
    with pytest.raises(HTTPException) as exc:
        await route.get_observed_release_tasks("OLP", "OLP.78")
    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_real_identities_still_not_claim_complete(monkeypatch):
    monkeypatch.setenv("SBERPROJECT_RELEASE_OBSERVATIONS_ENABLED", "1")

    def observe(product, version_id, cfg):
        return observed_release_links(
            product=product, version_id=version_id, payload=observed_payload(),
        )

    async def task(key):
        return {"task_code": key, "unit": {
            "unit": {"code": key, "attributes": {
                "title": "Task from AS21",
                "workflow_status": {"name": "In Progress"},
                "assigned_to": {"name": "Engineer"},
            }}
        }}

    monkeypatch.setattr(route.skill_bridge, "release_observations", observe)
    import app.routers.swtr_read as swtr_read
    monkeypatch.setattr(swtr_read, "get_task_raw", task)
    result = await route.get_observed_release_tasks("OLP", "OLP.78")
    assert result["linked_tasks"][0]["key"] == "OLP-12"
    assert result["linked_tasks"][0]["title"] == "Task from AS21"
    assert result["complete"] is False
    assert result["scope"] is None
    assert result["delivery_forecast"] is None


@pytest.mark.asyncio
async def test_source_failure_prevents_as21_reads(monkeypatch):
    monkeypatch.setenv("SBERPROJECT_RELEASE_OBSERVATIONS_ENABLED", "1")
    def observe(product, version_id, cfg):
        raise route.skill_bridge.SkillBridgeError(route.skill_bridge.REASON_INCOMPLETE)
    monkeypatch.setattr(route.skill_bridge, "release_observations", observe)
    import app.routers.swtr_read as swtr_read
    async def forbidden(key):
        raise AssertionError("AS21 must not be called on bad release source")
    monkeypatch.setattr(swtr_read, "get_task_raw", forbidden)
    with pytest.raises(HTTPException) as exc:
        await route.get_observed_release_tasks("OLP", "OLP.78")
    assert exc.value.status_code == 502
