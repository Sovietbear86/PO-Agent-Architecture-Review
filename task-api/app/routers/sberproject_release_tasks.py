"""Read-only release-linked tasks endpoint, guarded until source proofs exist.

Important: this endpoint intentionally does NOT accept an AS21 version UUID
from the caller. Version identity must be resolved independently from an
authoritative AS21 version record before any point read can be performed.
The current CLI cannot attest composition completeness, so live requests
fail closed rather than display invented/partial scope counts.
"""
from __future__ import annotations

import asyncio
import os
import re
from collections.abc import Mapping
from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.sberproject import skill_bridge
from app.services.sberproject.release_membership_contract import MembershipUnverified
from app.services.sberproject.release_task_adapter import (
    fetch_linked_release_tasks_from_sources,
)

router = APIRouter(tags=["sberproject-read"])
_RELEASE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$")

# No misleading default binding between SberProject version ID and AS21 UUID.
# Source resolver and point-reader are explicit injection seams for a later
# certified live-source implementation, not user-controllable HTTP parameters.


def _unavailable_version_identity(product: str, version_id: str) -> str:
    raise MembershipUnverified("as21_version_identity_unverified")


def _unavailable_point_read(task_key: str) -> Mapping[str, Any]:
    raise MembershipUnverified("as21_point_read_unavailable")


def read_linked_tasks(
    *, product: str, version_id: str,
    release_reader=None,
    version_resolver=None,
    point_reader=None,
) -> dict[str, Any]:
    """Blocking orchestration; no raw SberProject/AS21 credentials in output."""
    if product not in {"OLP", "DMS"} or not _RELEASE_ID.fullmatch(version_id):
        raise MembershipUnverified("invalid_release_identity")

    # The request must use independently sourced AS21 identity, never a guessed
    # version name, CLI release ID, or client-supplied UUID.
    resolve = version_resolver or _unavailable_version_identity
    as21_uuid = resolve(product, version_id)
    if not isinstance(as21_uuid, str) or not as21_uuid.strip():
        raise MembershipUnverified("as21_version_identity_unverified")

    if release_reader is None:
        cfg = skill_bridge.SkillBridgeConfig.from_env(os.environ)
        release_reader = lambda p, v: skill_bridge.release_composition(p, v, cfg)

    return fetch_linked_release_tasks_from_sources(
        product=product, version_id=version_id,
        as21_version_uuid=as21_uuid,
        fetch_composition_source=release_reader,
        fetch_as21_point_source=point_reader or _unavailable_point_read,
    )


@router.get("/releases/{product}/{version_id}/linked-tasks")
async def get_release_linked_tasks(
    product: str,
    version_id: str,
):
    """Disabled by default and source-proven only.

    Feature-flag is server side; no user query can enable it.
    """
    product = product.strip().upper()
    if product not in {"OLP", "DMS"} or not _RELEASE_ID.fullmatch(version_id):
        raise HTTPException(400, detail={"reason": "invalid_release_identity"})
    if os.environ.get("SBERPROJECT_RELEASE_TASKS_ENABLED", "").lower() not in {"1", "true", "on"}:
        raise HTTPException(503, detail={"reason": "release_task_binding_not_enabled"})
    try:
        return await asyncio.to_thread(read_linked_tasks, product=product, version_id=version_id)
    except skill_bridge.SkillBridgeError as exc:
        status = 503 if exc.reason in {skill_bridge.REASON_AUTH, skill_bridge.REASON_UNAVAILABLE} else 502
        raise HTTPException(status, detail={"reason": exc.reason}) from None
    except MembershipUnverified as exc:
        # A source-proof failure is never a zero-task result or a 100% KPI.
        raise HTTPException(502, detail={"reason": str(exc)}) from None


@router.get("/releases/{product}/{version_id}/observed-tasks")
async def get_observed_release_tasks(product: str, version_id: str):
    """Show bounded live tasks, explicitly NOT the complete release population.

    No AS21 release UUID is guessed. We verify each task identity with a
    direct point read, but do not claim AS21 fix-version membership.
    """
    product = product.strip().upper()
    if product not in {"OLP", "DMS"} or not _RELEASE_ID.fullmatch(version_id):
        raise HTTPException(400, detail={"reason": "invalid_release_identity"})
    if os.environ.get("SBERPROJECT_RELEASE_OBSERVATIONS_ENABLED", "").lower() not in {"1", "true", "on"}:
        raise HTTPException(503, detail={"reason": "release_observations_not_enabled"})
    cfg = skill_bridge.SkillBridgeConfig.from_env(os.environ)
    try:
        observations = await asyncio.to_thread(
            skill_bridge.release_observations, product, version_id, cfg,
        )
    except skill_bridge.SkillBridgeError as exc:
        status = 503 if exc.reason in {skill_bridge.REASON_AUTH, skill_bridge.REASON_UNAVAILABLE} else 502
        raise HTTPException(status, detail={"reason": exc.reason}) from None

    # Live point reads are intentionally bounded. Never silently truncate a
    # release or pretend an observed set is its full population.
    keys = observations["observed_issue_keys"]
    if len(keys) > 20:
        raise HTTPException(502, detail={"reason": "release_observation_point_read_limit"})
    from app.routers.swtr_read import get_task_raw, _unwrap_task_unit
    from app.services.sberproject.as21_point_adapter import _text
    tasks = []
    for key in keys:
        payload = await get_task_raw(key)
        unit = _unwrap_task_unit(payload.get("unit"))
        if not isinstance(unit, Mapping) or unit.get("code") != key:
            raise HTTPException(502, detail={"reason": "as21_task_identity_mismatch"})
        attrs = unit.get("attributes")
        attrs = attrs if isinstance(attrs, Mapping) else {}
        tasks.append({
            "key": key,
            "title": _text(attrs.get("title", unit.get("title"))),
            "status": _text(attrs.get("workflow_status", unit.get("workflow_status"))),
            "assignee": _text(attrs.get("assigned_to", unit.get("assigned_to"))),
            "source": "SBERPROJECT_OBSERVED_AS21_IDENTITY_VERIFIED",
        })
    # Observed count refers ONLY to listed links. KPI fields remain null.
    return {
        "product": product,
        "version_id": version_id,
        "membership_status": "OBSERVED_LINKS_UNVERIFIED",
        "complete": False,
        "observed_count": len(tasks),
        "observed_rows": observations["observed_rows"],
        "observed_internal_rows": observations["observed_internal_rows"],
        "linked_tasks": tasks,
        "scope": None, "completed": None, "wip": None,
        "readiness": None, "delivery_forecast": None,
    }
