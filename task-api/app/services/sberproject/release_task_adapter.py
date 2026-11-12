"""Single-release read-only linked task projection.

Dependencies are injected; no direct AS21/SberProject calls, credentials or Core V4
changes. Do not wire to live route until source adapters return authoritative
release-task rows, a verified AS21 version UUID, and complete point reads.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .release_membership_contract import MembershipUnverified, verified_partial_links

MAX_RELEASE_ROWS = 100
MAX_POINT_READS = 100


def fetch_linked_release_tasks(
    *,
    product: str,
    version_id: str,
    as21_version_uuid: str,
    fetch_release: Callable[[str, str], Mapping[str, Any]],
    fetch_as21_task: Callable[[str], Mapping[str, Any]],
) -> dict[str, Any]:
    """One exact version, at most 100 source rows; no enumerating entire workspaces.

    The SberProject reader must explicitly attest its version-scoped pagination
    is complete. No guessed zeros, no synthetic status, no release-wide KPIs.
    The AS21 UUID must come from a separately verified AS21 version record.
    """
    if product not in {"OLP", "DMS"} or not isinstance(version_id, str) or not version_id:
        raise MembershipUnverified("invalid_release_identity")
    if not isinstance(as21_version_uuid, str) or not as21_version_uuid.strip():
        raise MembershipUnverified("as21_version_identity_unverified")

    source = fetch_release(product, version_id)
    if not isinstance(source, Mapping) or source.get("product") != product or source.get("version_id") != version_id:
        raise MembershipUnverified("release_source_mismatch")
    # A partial release page must not masquerade as a complete 7-row sample.
    if source.get("complete") is not True:
        raise MembershipUnverified("release_composition_unverified")
    rows = source.get("tasks")
    if not isinstance(rows, (list, tuple)) or len(rows) > MAX_RELEASE_ROWS:
        raise MembershipUnverified("release_composition_invalid_or_over_limit")
    # COMPLETE here means all SberProject composition pages were read, not that
    # all AS21 tasks with a fix_version_s relation have been enumerated.
    # Require explicit source count and stable version-level identity.
    source_total = source.get("total")
    if type(source_total) is not int or source_total != len(rows):
        raise MembershipUnverified("release_composition_count_unverified")
    if source.get("has_more") is not False:
        raise MembershipUnverified("release_composition_pagination_unverified")

    keys = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise MembershipUnverified("invalid_release_task_row")
        key = row.get("issueKey")
        if key is None:
            continue
        if not isinstance(key, str) or not key or row.get("source") != "swtr":
            raise MembershipUnverified("unverified_release_task_link")
        keys.append(key)
    if len(keys) > MAX_POINT_READS or len(keys) != len(set(keys)):
        raise MembershipUnverified("duplicate_or_over_limit_links")

    records: dict[str, Mapping[str, Any]] = {}
    for key in keys:
        record = fetch_as21_task(key)
        if not isinstance(record, Mapping):
            raise MembershipUnverified("as21_point_read_unavailable")
        records[key] = record

    evidence = verified_partial_links(
        product=product, version_id=version_id, release_tasks=rows,
        as21_records=records, as21_version_uuid=as21_version_uuid
    )
    # The projection intentionally omits task-wide statuses and aggregates;
    # display the source-proven subset, not an invented release readiness.
    return {
        "product": product,
        "version_id": version_id,
        "membership_status": evidence.membership_status,
        "complete": False,
        "source_release_rows": evidence.source_release_rows,
        "linked_count": len(evidence.linked_task_ids),
        "internal_without_as21_key": evidence.internal_without_as21_key,
        "linked_tasks": [
            {
                "key": key,
                "title": record.get("title") if isinstance(record.get("title"), str) else None,
                "status": record.get("status") if isinstance(record.get("status"), str) else None,
                "assignee": record.get("assignee") if isinstance(record.get("assignee"), str) else None,
            }
            for key in evidence.linked_task_ids
            for record in (records[key],)
        ],
        "scope": None,
        "completed": None,
        "wip": None,
        "readiness": None,
        "delivery_forecast": None,
    }
