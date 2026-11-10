"""SberProject version catalogue facade (read-only, source-proven, fail-closed).

The authenticated corporate HTTPS read endpoint is provisioned externally.
This service never handles the user's password or browser cookies and never
claims that a version's task membership is known.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from urllib.parse import urlsplit

import httpx
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/v1/sberproject-read", tags=["sberproject-read"])
_VALID_PRODUCTS = {"OLP", "DMS"}
_ALLOWED_FIELDS = (
    "id", "versionId", "versionNumber", "workflowStatus", "beginDate",
    "endDate", "releaseDate", "owner", "manager", "architect", "has_more",
)
_MAX_ROWS = 20


def _source_config():
    url = os.environ.get("SBERPROJECT_CATALOG_READ_URL", "").strip()
    token = os.environ.get("SBERPROJECT_READ_ACCESS_TOKEN", "").strip()
    if not url or not token:
        raise HTTPException(503, detail={"reason": "sberproject_auth_required"})
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise HTTPException(503, detail={"reason": "sberproject_source_unavailable"})
    # Provision only an official, pre-approved corporate HTTPS read endpoint.
    # URLs are fixed by operators, never supplied by HTTP clients.
    return url, token


def _catalog_response(payload: object, product: str, limit: int) -> dict:
    if not isinstance(payload, dict):
        raise HTTPException(502, detail={"reason": "sberproject_incomplete"})
    rows = payload.get("results")
    meta = payload.get("meta")
    if not isinstance(rows, list) or not isinstance(meta, dict):
        raise HTTPException(502, detail={"reason": "sberproject_incomplete"})
    if any(not isinstance(row, dict) for row in rows):
        raise HTTPException(502, detail={"reason": "sberproject_incomplete"})
    if len(rows) > limit:
        raise HTTPException(502, detail={"reason": "sberproject_page_over_limit"})
    has_more = meta.get("has_more")
    if not isinstance(has_more, bool):
        raise HTTPException(502, detail={"reason": "sberproject_pagination_unknown"})
    safe_rows = []
    for row in rows:
        code = row.get("id") or row.get("versionId")
        version = row.get("versionNumber")
        if not isinstance(code, str) or not code or not isinstance(version, str) or not version:
            raise HTTPException(502, detail={"reason": "sberproject_incomplete"})
        safe_rows.append({field: row[field] for field in _ALLOWED_FIELDS if field in row
                          and isinstance(row[field], (str, int, float, bool, type(None)))})
    # No "task_count": a missing membership link must never become a false zero.
    return {
        "status": "COMPLETE" if not has_more else "PARTIAL",
        "source": "SBERPROJECT",
        "product": product,
        "versions": safe_rows,
        "has_more": has_more,
        "next_offset": meta.get("next_offset") if has_more and isinstance(meta.get("next_offset"), int) else None,
        "total": meta.get("total") if isinstance(meta.get("total"), int) else None,
        "as_of": datetime.now(timezone.utc).isoformat(),
        "membership_status": "SOURCE_UNVERIFIED",
    }


@router.get("/versions")
async def sberproject_versions(
    product: str = Query(...),
    limit: int = Query(20, ge=1, le=_MAX_ROWS),
    offset: int = Query(0, ge=0, le=500),
):
    product = product.strip().upper()
    if product not in _VALID_PRODUCTS:
        raise HTTPException(400, detail={"reason": "invalid_product"})
    url, token = _source_config()
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=False, trust_env=True) as client:
            response = await client.get(
                url, params={"product": product, "limit": limit, "offset": offset},
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            )
    except (httpx.TimeoutException, httpx.TransportError):
        raise HTTPException(503, detail={"reason": "sberproject_source_unavailable"}) from None
    if response.status_code in (401, 403):
        raise HTTPException(503, detail={"reason": "sberproject_auth_required"})
    if response.status_code != 200:
        raise HTTPException(503, detail={"reason": "sberproject_source_unavailable"})
    try:
        payload = response.json()
    except ValueError:
        raise HTTPException(502, detail={"reason": "sberproject_incomplete"}) from None
    return _catalog_response(payload, product, limit)
