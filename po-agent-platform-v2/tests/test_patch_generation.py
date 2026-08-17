import hashlib
import pytest

from po_agent.harness.patch_generation import (
    BoundedPatchGenerator,
    FileDraft,
    PatchGenerationPolicy,
)
from po_agent.harness.sandbox_patch import PatchOperation


ROOT = "po-agent-platform-v2/src/po_agent/harness"
TARGET = f"{ROOT}/example.py"
NEW_TARGET = f"{ROOT}/new_example.py"


def test_generate_replace_binds_baseline_hash():
    result = BoundedPatchGenerator().generate(
        drafts=[FileDraft(path=TARGET, content="new\n")],
        authorized_target_files=[TARGET],
        baseline_files={TARGET: "old\n"},
    )
    change = result.changes[0]
    assert change.operation is PatchOperation.REPLACE
    assert change.expected_before_sha256 == hashlib.sha256(b"old\n").hexdigest()
    assert result.target_files == (TARGET,)


def test_generate_create_has_no_baseline_hash():
    result = BoundedPatchGenerator().generate(
        drafts=[FileDraft(path=NEW_TARGET, content="created\n")],
        authorized_target_files=[NEW_TARGET],
        baseline_files={NEW_TARGET: None},
    )
    assert result.changes[0].operation is PatchOperation.CREATE
    assert result.changes[0].expected_before_sha256 is None


def test_rejects_unauthorized_target():
    with pytest.raises(ValueError, match="not authorized"):
        BoundedPatchGenerator().generate(
            drafts=[FileDraft(path=TARGET, content="x")],
            authorized_target_files=[NEW_TARGET],
            baseline_files={TARGET: None},
        )


def test_rejects_path_traversal():
    with pytest.raises(ValueError, match="unsafe repository path"):
        BoundedPatchGenerator().generate(
            drafts=[FileDraft(path=f"{ROOT}/../escape.py", content="x")],
            authorized_target_files=[f"{ROOT}/../escape.py"],
            baseline_files={},
        )


def test_rejects_operation_baseline_mismatch():
    with pytest.raises(ValueError, match="operation does not match"):
        BoundedPatchGenerator().generate(
            drafts=[FileDraft(path=TARGET, content="x", operation=PatchOperation.CREATE)],
            authorized_target_files=[TARGET],
            baseline_files={TARGET: "exists"},
        )


def test_rejects_duplicate_targets():
    with pytest.raises(ValueError, match="duplicate target"):
        BoundedPatchGenerator().generate(
            drafts=[FileDraft(path=TARGET, content="a"), FileDraft(path=TARGET, content="b")],
            authorized_target_files=[TARGET],
            baseline_files={TARGET: None},
        )


def test_enforces_file_limit():
    policy = PatchGenerationPolicy(max_files=1)
    with pytest.raises(ValueError, match="max_files"):
        BoundedPatchGenerator(policy).generate(
            drafts=[FileDraft(path=TARGET, content="a"), FileDraft(path=NEW_TARGET, content="b")],
            authorized_target_files=[TARGET, NEW_TARGET],
            baseline_files={},
        )


def test_enforces_per_file_size_limit():
    policy = PatchGenerationPolicy(max_file_chars=2)
    with pytest.raises(ValueError, match="max_file_chars"):
        BoundedPatchGenerator(policy).generate(
            drafts=[FileDraft(path=TARGET, content="abc")],
            authorized_target_files=[TARGET],
            baseline_files={},
        )


def test_enforces_total_size_limit():
    policy = PatchGenerationPolicy(max_total_chars=3, max_file_chars=3)
    with pytest.raises(ValueError, match="max_total_chars"):
        BoundedPatchGenerator(policy).generate(
            drafts=[FileDraft(path=TARGET, content="ab"), FileDraft(path=NEW_TARGET, content="cd")],
            authorized_target_files=[TARGET, NEW_TARGET],
            baseline_files={},
        )


def test_baseline_reader_supported():
    result = BoundedPatchGenerator().generate(
        drafts=[FileDraft(path=TARGET, content="after")],
        authorized_target_files=[TARGET],
        baseline_reader=lambda path: "before" if path == TARGET else None,
    )
    assert result.changes[0].operation is PatchOperation.REPLACE


def test_requires_baseline_source():
    with pytest.raises(ValueError, match="baseline source"):
        BoundedPatchGenerator().generate(
            drafts=[FileDraft(path=TARGET, content="x")],
            authorized_target_files=[TARGET],
        )


def test_generation_is_data_only_and_non_executing():
    result = BoundedPatchGenerator().generate(
        drafts=[FileDraft(path=NEW_TARGET, content="print('never executed')\n")],
        authorized_target_files=[NEW_TARGET],
        baseline_files={},
    )
    assert result.changes[0].content == "print('never executed')\n"
