"""No fabricated release membership or completion metrics."""
import importlib.util
from pathlib import Path

import pytest

FILE = Path(__file__).resolve().parents[1] / "app/services/sberproject/release_membership_contract.py"
SPEC = importlib.util.spec_from_file_location("release_membership_contract", FILE)
assert SPEC and SPEC.loader
import sys
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


def valid_proof():
    return dict(source="AS21", product="OLP", version_id="OLP.78",
                complete=True, snapshot_valid=True, mapping_field="fix_version_s",
                declared_count=2)


def test_source_proven_tasks_allow_metrics():
    membership = module.verify_membership(product="OLP", version_id="OLP.78",
                                          task_ids=["OLP-1", "OLP-2"], proof=valid_proof())
    assert module.readiness_counts(membership, {"OLP-1": "done", "OLP-2": "in_progress"},
                                   frozenset({"done"})) == {
                                       "scope": 2, "completed": 1, "remaining": 1
                                   }


@pytest.mark.parametrize("mutation", [
    {"complete": False}, {"snapshot_valid": False}, {"source": "UNKNOWN"},
    {"product": "DMS"}, {"version_id": "OLP.79"}, {"mapping_field": "display_name"},
    {"declared_count": 3},
])
def test_invalid_provenance_fails_closed(mutation):
    proof = valid_proof()
    proof.update(mutation)
    with pytest.raises(module.MembershipUnverified):
        module.verify_membership(product="OLP", version_id="OLP.78",
                                 task_ids=["OLP-1", "OLP-2"], proof=proof)


def test_duplicate_ids_fail_closed():
    with pytest.raises(module.MembershipUnverified):
        module.verify_membership(product="OLP", version_id="OLP.78",
                                 task_ids=["OLP-1", "OLP-1"], proof=valid_proof())


def test_incomplete_status_snapshot_fails_closed():
    membership = module.verify_membership(product="OLP", version_id="OLP.78",
                                          task_ids=["OLP-1", "OLP-2"], proof=valid_proof())
    with pytest.raises(module.MembershipUnverified):
        module.readiness_counts(membership, {"OLP-1": "done"}, frozenset({"done"}))
