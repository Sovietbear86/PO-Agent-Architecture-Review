"""Read-only Agent gateway for bounded release observations.

Provides the same-origin route used by the frontend. Only forwards to the
already-configured Task API; never accepts an arbitrary URL, credentials, or
task population from the browser. The Task API feature flag remains final.
"""
from __future__ import annotations

import re

import httpx
from fastapi import APIRouter, HTTPException

from po_agent.config import get_settings

router = APIRouter(tags=["sberproject-release-observations"])
_VALID_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,119}$")


@router.get("/sberproject-read/releases/{product}/{version_id}/observed-tasks")
async def observed_release_tasks_proxy(product: str, version_id: str):
    normalized = product.strip().upper()
    if normalized not in {"OLP", "DMS"} or not _VALID_ID.fullmatch(version_id):
        raise HTTPException(400, detail={"reason": "invalid_release_identity"})
    settings = get_settings()
    base = settings.task_api_base_url.rstrip("/")
    # Fixed server-side destination; no externally supplied host, port or path.
    url = f"{base}/api/v1/sberproject-read/releases/{normalized}/{version_id}/observed-tasks"
    try:
        async with httpx.AsyncClient(
            timeout=max(1, min(settings.task_api_timeout_seconds, 120)),
            follow_redirects=False,
        ) as client:
            response = await client.get(url, headers={"Accept": "application/json"})
    except (httpx.TimeoutException, httpx.TransportError):
        raise HTTPException(503, detail={"reason": "task_api_source_unavailable"}) from None
    if response.status_code != 200:
        # Do not accidentally interpret unavailable/disabled as an empty list.
        reason = "release_observations_unavailable"
        try:
            detail = response.json().get("detail", {})
            if isinstance(detail, dict) and isinstance(detail.get("reason"), str):
                reason = detail["reason"]
        except (ValueError, AttributeError):
            pass
        if response.status_code == 400:
            raise HTTPException(400, detail={"reason": reason})
        raise HTTPException(503 if response.status_code >= 500 else 502, detail={"reason": reason})
    try:
        data = response.json()
    except ValueError:
        raise HTTPException(502, detail={"reason": "invalid_task_api_response"}) from None
    if not isinstance(data, dict) or (
        data.get("product") != normalized
        or data.get("version_id") != version_id
        or data.get("membership_status") != "OBSERVED_LINKS_UNVERIFIED"
        or data.get("complete") is not False
        or not isinstance(data.get("linked_tasks"), list)
    ):
        raise HTTPException(502, detail={"reason": "unverified_task_api_response"})
    return data
