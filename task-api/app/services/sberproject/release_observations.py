"""Bounded, explicitly non-exhaustive SberProject task-link observations.

The installed sbt-project CLI exposes release(<exact version id>) rows, but
its pagination metadata is client-generated. Those rows can be displayed as
observations, NEVER as the authoritative full release scope. In particular
zero observed rows is not equivalent to an empty release.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from .release_membership_contract import MembershipUnverified

_TASK_KEY = re.compile(r"^[A-Z][A-Z0-9]*-\d+$")
MAX_OBSERVED_ROWS = 100


def observed_release_links(
    *, product: str, version_id: str, payload: Mapping[str, Any],
) -> dict[str, Any]:
    if product not in ("OLP", "DMS") or not isinstance(version_id, str) or not version_id.strip():
        raise MembershipUnverified("invalid_release_identity")
    if not isinstance(payload, Mapping):
        raise MembershipUnverified("release_source_invalid")
    # Do not trust a mismatched version if the CLI includes an identifier.
    for field in ("version_id", "versionId", "releaseId"):
        identity = payload.get(field)
        if identity is not None and identity != version_id:
            raise MembershipUnverified("release_source_mismatch")
    rows = payload.get("results")
    if not isinstance(rows, list):
        raise MembershipUnverified("release_source_invalid")
    if len(rows) > MAX_OBSERVED_ROWS:
        raise MembershipUnverified("release_observation_over_limit")

    linked = []
    seen = set()
    internal_seen = 0
    for row in rows:
        if not isinstance(row, Mapping):
            raise MembershipUnverified("invalid_release_task_row")
        key = row.get("issueKey")
        if key is None:
            internal_seen += 1
            continue
        if not isinstance(key, str) or not _TASK_KEY.fullmatch(key):
            raise MembershipUnverified("unverified_release_task_link")
        if row.get("source") != "swtr" or key in seen:
            raise MembershipUnverified("unverified_or_duplicate_release_task_link")
        seen.add(key)
        linked.append(key)

    return {
        "product": product,
        "version_id": version_id,
        "membership_status": "OBSERVED_LINKS_UNVERIFIED",
        "complete": False,
        "observed_rows": len(rows),
        "observed_internal_rows": internal_seen,
        "observed_issue_keys": linked,
        "observed_count": len(linked),
        "scope": None,
        "completed": None,
        "wip": None,
        "readiness": None,
        "delivery_forecast": None,
    }
