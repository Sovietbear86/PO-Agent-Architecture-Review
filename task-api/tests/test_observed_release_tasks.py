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


def test_live_observation_reader_reuses_accounting_object_cli(monkeypatch):
    """A230R3.64: do not call cmdRelease with human release display ID."""
    from app.services.sberproject import skill_bridge

    calls = []
    def fake_run(cmd, args, timeout, ca_bundle):
        calls.append((cmd, args, timeout, ca_bundle))
        import json
        return 0, json.dumps(observed_payload()), ""

    monkeypatch.setattr(skill_bridge, "_run_skill", fake_run)
    cfg = skill_bridge.SkillBridgeConfig(
        enabled=True, skill_cmd="/tmp/sbt-project.sh", ca_bundle="/tmp/corp-ca.pem", timeout=15.0
    )
    result = skill_bridge.release_observations("OLP", "OLP.78", cfg)
    assert calls == [(
        "/tmp/sbt-project.sh", ["tasks", "OLP.78", "--accounting-object"],
        15.0, "/tmp/corp-ca.pem",
    )]
    assert result["observed_count"] == 1
    assert result["complete"] is False
    assert result["scope"] is None


def test_accounting_object_observations_are_not_complete_at_32_rows():
    """Reported source composition: 6 AS21 keys, 26 SberProject-only rows."""
    rows = [
        {"issueKey": f"OLP-{i}", "source": "swtr"} for i in range(1, 7)
    ] + [{"issueKey": None, "source": "project"} for _ in range(26)]
    result = observed_release_links(
        product="OLP", version_id="OLP.78",
        payload={"results": rows, "meta": {"total": 32, "has_more": False}},
    )
    assert result["observed_rows"] == 32
    assert result["observed_internal_rows"] == 26
    assert result["observed_count"] == 6
    assert result["complete"] is False
    assert result["readiness"] is None
