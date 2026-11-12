"""Bounded AS21 point-read shape adapter for release-linked tasks.

Pure conversion of existing /api/v1/swtr-read/tasks/{code} responses.
Never queries a space, guesses a version UUID, or invents task fields.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from .release_membership_contract import MembershipUnverified

_TASK_KEY = re.compile(r"^[A-Z][A-Z0-9]*-\d+$")


def _unit(payload: Any) -> Mapping[str, Any]:
    """Only accept an explicitly identified point-read task unit."""
    if not isinstance(payload, Mapping):
        raise MembershipUnverified("as21_point_read_invalid")
    wrapper = payload.get("unit", payload)
    if not isinstance(wrapper, Mapping):
        raise MembershipUnverified("as21_point_read_invalid")
    return wrapper


def _text(value: Any) -> str | None:
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, Mapping):
        for field in ("name", "title", "value", "displayName"):
            result = value.get(field)
            if isinstance(result, str) and result.strip():
                return result.strip()
    return None


def _versions(value: Any) -> list[dict[str, str]]:
    """Preserve explicit AS21 version codes; never equate them to release IDs."""
    if isinstance(value, Mapping):
        value = value.get("content", value.get("elems"))
    if not isinstance(value, list):
        raise MembershipUnverified("as21_version_link_unverified")
    items = []
    for record in value:
        if not isinstance(record, Mapping):
            raise MembershipUnverified("as21_version_link_unverified")
        code = record.get("code")
        if not isinstance(code, str) or not code.strip():
            raise MembershipUnverified("as21_version_link_unverified")
        items.append({"code": code.strip()})
    return items


def normalize_as21_point_read(task_key: str, payload: Any) -> dict[str, Any]:
    """Normalize one canonical AS21 read_unit response.

    Identifiers and fix_version_s must be explicitly sourced. Missing
    optional labels remain None, rather than fabricated placeholders.
    """
    if not isinstance(task_key, str) or not _TASK_KEY.fullmatch(task_key):
        raise MembershipUnverified("invalid_as21_task_key")
    if not isinstance(payload, Mapping):
        raise MembershipUnverified("as21_point_read_invalid")
    envelope_key = payload.get("task_code")
    if envelope_key is not None and envelope_key != task_key:
        raise MembershipUnverified("as21_task_identity_mismatch")
    unit = _unit(payload)
    attrs = unit.get("attributes")
    if attrs is not None and not isinstance(attrs, Mapping):
        raise MembershipUnverified("as21_point_read_invalid")
    attrs = attrs if isinstance(attrs, Mapping) else {}
    actual_key = unit.get("code")
    if actual_key != task_key:
        raise MembershipUnverified("as21_task_identity_mismatch")
    relation = attrs.get("fix_version_s", unit.get("fix_version_s"))
    return {
        "key": task_key,
        "title": _text(attrs.get("title", unit.get("title"))),
        "status": _text(attrs.get("workflow_status", unit.get("workflow_status"))),
        "assignee": _text(attrs.get("assigned_to", unit.get("assigned_to"))),
        "fix_version_s": _versions(relation),
    }
