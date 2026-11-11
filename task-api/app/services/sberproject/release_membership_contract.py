"""Source-proven version/task membership contract (no AS21 access or writes).

A release version ID and an AS21 task version code belong to different ID
domains. Only an authoritative, explicit link allows readiness metrics.
Unverified or partial membership must NEVER be displayed as zero tasks or 100%.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


class MembershipUnverified(ValueError):
    """The source has not established an exhaustive membership mapping."""


@dataclass(frozen=True)
class MembershipProof:
    product: str
    version_id: str
    as21_task_ids: tuple[str, ...]
    source: str
    complete: bool
    mapping_field: str


def verify_membership(
    *,
    product: str,
    version_id: str,
    task_ids: Sequence[str],
    proof: Mapping[str, Any],
) -> MembershipProof:
    """Validate an externally acquired explicit source link, never infer by name.

    This function does not query systems. The caller must separately obtain
    an authoritative snapshot from SberProject/AS21 with verified pagination.
    """
    if product not in ("OLP", "DMS") or not version_id or not isinstance(version_id, str):
        raise MembershipUnverified("invalid_release_identity")
    if not isinstance(proof, Mapping):
        raise MembershipUnverified("missing_membership_proof")
    if proof.get("source") not in ("SBERPROJECT", "AS21"):
        raise MembershipUnverified("untrusted_membership_source")
    if proof.get("product") != product or proof.get("version_id") != version_id:
        raise MembershipUnverified("membership_release_mismatch")
    if proof.get("complete") is not True or proof.get("snapshot_valid") is not True:
        raise MembershipUnverified("membership_incomplete")
    if proof.get("mapping_field") not in ("fix_version_s", "source_id", "issueKey"):
        raise MembershipUnverified("membership_mapping_not_authoritative")
    if not isinstance(task_ids, (tuple, list)) or not all(
        isinstance(task_id, str) and task_id.strip() and task_id == task_id.strip()
        for task_id in task_ids
    ):
        raise MembershipUnverified("invalid_task_ids")
    if len(task_ids) != len(set(task_ids)):
        raise MembershipUnverified("duplicate_task_ids")
    if proof.get("declared_count") != len(task_ids) or type(proof.get("declared_count")) is not int:
        raise MembershipUnverified("membership_count_mismatch")
    return MembershipProof(
        product=product, version_id=version_id, as21_task_ids=tuple(task_ids),
        source=proof["source"], complete=True, mapping_field=proof["mapping_field"]
    )


def readiness_counts(membership: MembershipProof, statuses: Mapping[str, str], terminal: frozenset[str]) -> dict[str, int]:
    """Counts only when statuses are source-declared, complete and consistent."""
    if not membership.complete:
        raise MembershipUnverified("membership_incomplete")
    if set(statuses) != set(membership.as21_task_ids) or not terminal:
        raise MembershipUnverified("task_status_coverage_incomplete")
    if any(not isinstance(s, str) or not s for s in statuses.values()):
        raise MembershipUnverified("invalid_task_status")
    done = sum(statuses[i] in terminal for i in membership.as21_task_ids)
    return {"scope": len(membership.as21_task_ids), "completed": done, "remaining": len(statuses)-done}


@dataclass(frozen=True)
class PartialReleaseEvidence:
    """Visible source-confirmed links; NOT a complete release task population."""
    product: str
    version_id: str
    linked_task_ids: tuple[str, ...]
    source_release_rows: int
    internal_without_as21_key: int
    membership_status: str = "PARTIAL_SOURCE_PROVEN"
    complete: bool = False


def verified_partial_links(
    *,
    product: str,
    version_id: str,
    release_tasks: Sequence[Mapping[str, Any]],
    as21_records: Mapping[str, Mapping[str, Any]],
    as21_version_uuid: str,
) -> PartialReleaseEvidence:
    """Verify only explicitly linked release entries against individual AS21 records.

    Does not establish completeness or compute release-wide metrics. The caller
    must bind as21_version_uuid using an independently read AS21 version record;
    a version's display name alone is not an identity proof.
    """
    if product not in ("OLP", "DMS") or not isinstance(version_id, str) or not version_id:
        raise MembershipUnverified("invalid_release_identity")
    if not isinstance(as21_version_uuid, str) or not as21_version_uuid.strip():
        raise MembershipUnverified("as21_version_identity_unverified")
    if not isinstance(release_tasks, (list, tuple)) or not isinstance(as21_records, Mapping):
        raise MembershipUnverified("invalid_release_task_sources")
    linked: list[str] = []
    internal = 0
    for row in release_tasks:
        if not isinstance(row, Mapping):
            raise MembershipUnverified("invalid_release_task_row")
        key = row.get("issueKey")
        if key is None:
            internal += 1
            continue
        if not isinstance(key, str) or not key or key != key.strip() or row.get("source") != "swtr":
            raise MembershipUnverified("unverified_release_task_link")
        if key in linked:
            raise MembershipUnverified("duplicate_release_task_link")
        record = as21_records.get(key)
        if not isinstance(record, Mapping) or record.get("key") != key:
            raise MembershipUnverified("as21_task_identity_mismatch")
        versions = record.get("fix_version_s")
        if not isinstance(versions, (tuple, list)) or as21_version_uuid not in [
            v.get("code") for v in versions if isinstance(v, Mapping)
        ]:
            raise MembershipUnverified("as21_version_link_mismatch")
        linked.append(key)
    return PartialReleaseEvidence(
        product=product, version_id=version_id, linked_task_ids=tuple(linked),
        source_release_rows=len(release_tasks), internal_without_as21_key=internal
    )
