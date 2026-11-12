"""Strict bounded SberProject release-composition gate.

The current CLI's meta.total=mapped.length and has_more=false are
client-side defaults, not source evidence. Reject until a registered
source operation provides explicit completeness for the exact version.
"""
from __future__ import annotations
from collections.abc import Callable, Mapping
from typing import Any
from .release_membership_contract import MembershipUnverified

MAX_RELEASE_ROWS = 100


def normalize_release_composition(
    *, product: str, version_id: str, payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Accept only exact-version, source-attested, complete composition.

    source_complete and source_total must come from the upstream
    SberProject operation, never synthesized by the CLI mapper.
    """
    if product not in {"OLP", "DMS"} or not isinstance(version_id, str) or not version_id.strip():
        raise MembershipUnverified("invalid_release_identity")
    if not isinstance(payload, Mapping):
        raise MembershipUnverified("release_composition_unverified")
    if payload.get("product") != product or payload.get("version_id") != version_id:
        raise MembershipUnverified("release_source_mismatch")
    if payload.get("source_operation") != "searchTaskCr":
        raise MembershipUnverified("release_composition_source_unverified")
    if payload.get("source_complete") is not True:
        raise MembershipUnverified("release_composition_unverified")
    if payload.get("source_has_more") is not False:
        raise MembershipUnverified("release_composition_pagination_unverified")
    raw = payload.get("tasks")
    count = payload.get("source_total")
    if not isinstance(raw, list) or len(raw) > MAX_RELEASE_ROWS:
        raise MembershipUnverified("release_composition_invalid_or_over_limit")
    if type(count) is not int or count != len(raw):
        raise MembershipUnverified("release_composition_count_unverified")
    rows = []
    seen: set[str] = set()
    for entry in raw:
        if not isinstance(entry, Mapping):
            raise MembershipUnverified("invalid_release_task_row")
        key = entry.get("issueKey")
        source = entry.get("source")
        if key is None:
            rows.append({"issueKey": None, "source": source})
            continue
        if not isinstance(key, str) or not key.strip() or key != key.strip():
            raise MembershipUnverified("unverified_release_task_link")
        if source != "swtr" or key in seen:
            raise MembershipUnverified("unverified_or_duplicate_release_task_link")
        seen.add(key)
        rows.append({"issueKey": key, "source": source})
    return {
        "product": product, "version_id": version_id, "tasks": rows,
        "total": count, "has_more": False, "complete": True,
    }


def fetch_release_composition(
    product: str, version_id: str,
    *, fetch_source: Callable[[str, str], Mapping[str, Any]],
) -> dict[str, Any]:
    """One exact release, injected reader, no tenant-wide scans."""
    if product not in {"OLP", "DMS"} or not isinstance(version_id, str) or not version_id.strip():
        raise MembershipUnverified("invalid_release_identity")
    return normalize_release_composition(
        product=product, version_id=version_id,
        payload=fetch_source(product, version_id),
    )
