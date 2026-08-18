from __future__ import annotations

from pathlib import Path

import pytest

from po_agent.harness.evolution_lifecycle import ControlledImprovementLifecycle, PromotionPolicy
from po_agent.harness.production_runtime import (
    ProductionHarnessRuntimeConfig,
    build_production_harness_runtime,
)


class _NeverRunExperimentRunner:
    def run(self, **kwargs):  # pragma: no cover - composition tests must not execute experiments
        raise AssertionError("experiment runner must not execute during composition")


def _build(tmp_path: Path, *, lifecycle: ControlledImprovementLifecycle | None = None):
    config = ProductionHarnessRuntimeConfig.in_directory(
        tmp_path,
        signing_key=b"p" * 32,
    )
    return build_production_harness_runtime(
        config=config,
        experiment_runner=_NeverRunExperimentRunner(),
        lifecycle=lifecycle or ControlledImprovementLifecycle(),
        fingerprint_resolver=lambda candidate_id: "f" * 64,
    )


def test_config_requires_durable_databases() -> None:
    with pytest.raises(ValueError, match="durable on-disk"):
        ProductionHarnessRuntimeConfig(
            state_db_path=":memory:",
            audit_db_path="audit.sqlite3",
            signing_key=b"x" * 32,
        )
    with pytest.raises(ValueError, match="durable on-disk"):
        ProductionHarnessRuntimeConfig(
            state_db_path="state.sqlite3",
            audit_db_path=":memory:",
            signing_key=b"x" * 32,
        )


def test_config_rejects_weak_signing_key(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="at least 32 bytes"):
        ProductionHarnessRuntimeConfig.in_directory(tmp_path, signing_key=b"short")


def test_factory_creates_canonical_fail_closed_runtime(tmp_path: Path) -> None:
    runtime = _build(tmp_path)
    try:
        status = runtime.status
        assert status.durable_governance is True
        assert status.human_approval_required is True
        assert status.autonomous_promotion_enabled is False
        assert status.autonomous_rollback_enabled is False
        assert status.monitoring_has_rollback_authority is False
        assert runtime.orchestrator is not None
        assert runtime.governance is not None
        assert (tmp_path / "governance_state.sqlite3").exists()
        assert (tmp_path / "governance_audit.sqlite3").exists()
    finally:
        runtime.close()


def test_runtime_rejects_policy_without_human_approval(tmp_path: Path) -> None:
    lifecycle = ControlledImprovementLifecycle(
        PromotionPolicy(require_human_approval=False)
    )
    config = ProductionHarnessRuntimeConfig.in_directory(
        tmp_path,
        signing_key=b"k" * 32,
    )
    with pytest.raises(ValueError, match="requires human approval"):
        build_production_harness_runtime(
            config=config,
            experiment_runner=_NeverRunExperimentRunner(),
            lifecycle=lifecycle,
            fingerprint_resolver=lambda candidate_id: "f" * 64,
        )


def test_runtime_close_is_idempotent_and_fail_closed(tmp_path: Path) -> None:
    runtime = _build(tmp_path)
    runtime.close()
    runtime.close()
    with pytest.raises(RuntimeError, match="runtime is closed"):
        _ = runtime.status
    with pytest.raises(RuntimeError, match="runtime is closed"):
        _ = runtime.orchestrator


def test_context_manager_closes_runtime(tmp_path: Path) -> None:
    runtime = _build(tmp_path)
    with runtime as active:
        assert active.status.durable_governance is True
    with pytest.raises(RuntimeError, match="runtime is closed"):
        _ = runtime.governance


def test_public_runtime_has_no_direct_approval_bypass(tmp_path: Path) -> None:
    runtime = _build(tmp_path)
    try:
        assert not hasattr(runtime, "approve")
        assert not hasattr(runtime, "mark_promoted")
        assert not hasattr(runtime, "apply_release")
        assert not hasattr(runtime, "auto_promote")
        assert not hasattr(runtime, "auto_rollback")
    finally:
        runtime.close()
