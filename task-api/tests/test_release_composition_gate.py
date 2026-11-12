"""Contract tests for source-attested SberProject composition (no live calls)."""
import pytest

from app.services.sberproject.release_composition import (
    fetch_release_composition,
    normalize_release_composition,
)
from app.services.sberproject.release_membership_contract import MembershipUnverified


def proven(**overrides):
    payload = {
        "product": "OLP",
        "version_id": "OLP.78",
        "source_operation": "searchTaskCr",
        "source_complete": True,
        "source_has_more": False,
        "source_total": 3,
        "tasks": [
            {"issueKey": "OLP-123", "source": "swtr"},
            {"issueKey": "DMS-777", "source": "swtr"},
            {"issueKey": None, "source": "project"},
        ],
    }
    payload.update(overrides)
    return payload


def test_accepts_proven_partial_links_not_complete_as21_membership():
    result = fetch_release_composition(
        "OLP", "OLP.78", fetch_source=lambda product, version: proven()
    )
    assert result["total"] == 3
    assert result["complete"] is True
    assert result["tasks"][2]["issueKey"] is None


@pytest.mark.parametrize("changes", [
    {"source_operation": None},
    {"source_complete": False},
    {"source_complete": None},
    {"source_has_more": True},
    {"source_has_more": None},
    {"source_total": 2},
    {"source_total": True},
    {"product": "DMS"},
    {"version_id": "OLP.79"},
    {"tasks": [{"issueKey": "OLP-123", "source": "swtr"}]},
    {"tasks": [{"issueKey": "OLP-123", "source": "swtr"}] * 101},
    {"tasks": [{"issueKey": "OLP-123", "source": "swtr"}] * 3},
])
def test_rejects_unproven_or_inconsistent_composition(changes):
    with pytest.raises(MembershipUnverified):
        normalize_release_composition(product="OLP", version_id="OLP.78", payload=proven(**changes))


def test_legacy_cli_metadata_is_not_source_attestation():
    with pytest.raises(MembershipUnverified):
        normalize_release_composition(
            product="OLP", version_id="OLP.78",
            payload={"product": "OLP", "version_id": "OLP.78",
                     "results": proven()["tasks"],
                     "meta": {"total": 3, "has_more": False}},
        )


def test_empty_without_source_proof_is_not_zero():
    with pytest.raises(MembershipUnverified):
        normalize_release_composition(
            product="OLP", version_id="OLP.78",
            payload=proven(tasks=[], source_total=0, source_complete=None),
        )


def test_verified_empty_composition_is_allowed():
    assert normalize_release_composition(
        product="OLP", version_id="OLP.78",
        payload=proven(tasks=[], source_total=0),
    )["total"] == 0
