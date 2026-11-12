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

from fastapi import APIRouter, HTTPException, Query

from app.services.sberproject import skill_bridge
from app.services.sberproject.release_membership_contract import MembershipUnverified
from app.services.sberproject.release_task_adapter import (
    fetch_linked_release_tasks_from_sources,
)

router = APIRouter(prefix="/api/v1/sberproject-read", tags=["sberproject-read"])
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
    enabled: bool = Query(False, exclude=True),
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
