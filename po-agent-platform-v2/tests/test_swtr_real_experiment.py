from __future__ import annotations

import hashlib

import pytest

from po_agent.adapters.swtr_shadow import SWTRShadowBatch, SWTRTaskSnapshot
from po_agent.harness.swtr_real_evaluation import AgentObservation, RealShadowPolicy
from po_agent.harness.swtr_real_experiment import (
    ExperimentStatus,
    SWTRRealExperimentRunner,
)


def _case(key: str, title: str = "Task") -> SWTRTaskSnapshot:
    payload = '{"key":"%s","source":"swtr","title":"%s"}' % (key, title)
    return SWTRTaskSnapshot(
        task_key=key,
        source="swtr",
        payload_json=payload,
        content_sha256=hashlib.sha256(payload.encode()).hexdigest(),
    )


def _batch(*cases: SWTRTaskSnapshot) -> SWTRShadowBatch:
    return SWTRShadowBatch.build(cases)


def _agent(score: float):
    def run(snapshot):
        return AgentObservation(
            answer=f"answer:{snapshot['key']}",
            score=score,
            grounded=True,
            latency_ms=1.0,
            llm_calls=1,
        )

    return run


class _FailIfTouchedSource:
    async def capture_keys(self, keys):
        raise AssertionError("source must not be touched for run_frozen_batch")

    async def capture_query(self, query, *, limit=None):
        raise AssertionError("source must not be touched for run_frozen_batch")


class _CountingSource:
    def __init__(self, batch: SWTRShadowBatch):
        self.batch = batch
        self.key_calls = 0
        self.query_calls = 0

    async def capture_keys(self, keys):
        self.key_calls += 1
        return self.batch

    async def capture_query(self, query, *, limit=None):
        self.query_calls += 1
        return self.batch


def test_frozen_batch_never_reaches_live_source():
    runner = SWTRRealExperimentRunner(
        _FailIfTouchedSource(),
        policy=RealShadowPolicy(min_improved_cases=1),
    )
    result = runner.run_frozen_batch(
        _batch(_case("SWTR-1")),
        experiment_id="exp-001",
        baseline_id="baseline-v1",
        candidate_id="candidate-v2",
        baseline_agent=_agent(0.4),
        candidate_agent=_agent(0.9),
    )
    assert result.status is ExperimentStatus.APPROVAL_REQUIRED
    assert result.manifest.task_keys == ("SWTR-1",)


def test_manifest_and_report_are_reproducible_for_same_frozen_inputs():
    runner = SWTRRealExperimentRunner(
        _FailIfTouchedSource(),
        policy=RealShadowPolicy(min_improved_cases=1),
    )
    kwargs = dict(
        batch=_batch(_case("SWTR-2"), _case("SWTR-1")),
        experiment_id="exp-002",
        baseline_id="baseline-v1",
        candidate_id="candidate-v2",
        baseline_agent=_agent(0.5),
        candidate_agent=_agent(0.8),
    )
    first = runner.run_frozen_batch(**kwargs)
    second = runner.run_frozen_batch(**kwargs)

    assert first.manifest.manifest_sha256 == second.manifest.manifest_sha256
    assert first.evidence.run_sha256 == second.evidence.run_sha256
    assert first.report_sha256 == second.report_sha256
    assert first.manifest.task_keys == ("SWTR-1", "SWTR-2")


def test_manifest_changes_when_corpus_changes():
    runner = SWTRRealExperimentRunner(
        _FailIfTouchedSource(),
        policy=RealShadowPolicy(min_improved_cases=1),
    )
    one = runner.run_frozen_batch(
        _batch(_case("SWTR-1", "A")),
        experiment_id="exp-003",
        baseline_id="baseline-v1",
        candidate_id="candidate-v2",
        baseline_agent=_agent(0.5),
        candidate_agent=_agent(0.8),
    )
    two = runner.run_frozen_batch(
        _batch(_case("SWTR-1", "B")),
        experiment_id="exp-003",
        baseline_id="baseline-v1",
        candidate_id="candidate-v2",
        baseline_agent=_agent(0.5),
        candidate_agent=_agent(0.8),
    )
    assert one.manifest.batch_sha256 != two.manifest.batch_sha256
    assert one.manifest.manifest_sha256 != two.manifest.manifest_sha256
    assert one.report_sha256 != two.report_sha256


def test_manifest_binds_policy_and_agent_identity():
    batch = _batch(_case("SWTR-4"))
    first = SWTRRealExperimentRunner(
        _FailIfTouchedSource(),
        policy=RealShadowPolicy(min_improved_cases=1, min_score_delta=0.05),
    ).run_frozen_batch(
        batch,
        experiment_id="exp-004",
        baseline_id="baseline-v1",
        candidate_id="candidate-v2",
        baseline_agent=_agent(0.5),
        candidate_agent=_agent(0.8),
    )
    second = SWTRRealExperimentRunner(
        _FailIfTouchedSource(),
        policy=RealShadowPolicy(min_improved_cases=1, min_score_delta=0.10),
    ).run_frozen_batch(
        batch,
        experiment_id="exp-004",
        baseline_id="baseline-v1",
        candidate_id="candidate-v3",
        baseline_agent=_agent(0.5),
        candidate_agent=_agent(0.8),
    )
    assert first.manifest.policy_sha256 != second.manifest.policy_sha256
    assert first.manifest.manifest_sha256 != second.manifest.manifest_sha256


@pytest.mark.asyncio
async def test_run_keys_captures_source_exactly_once_before_evaluation():
    source = _CountingSource(_batch(_case("SWTR-5")))
    runner = SWTRRealExperimentRunner(
        source,
        policy=RealShadowPolicy(min_improved_cases=1),
    )
    result = await runner.run_keys(
        ["SWTR-5"],
        experiment_id="exp-005",
        baseline_id="baseline-v1",
        candidate_id="candidate-v2",
        baseline_agent=_agent(0.4),
        candidate_agent=_agent(0.9),
    )
    assert source.key_calls == 1
    assert source.query_calls == 0
    assert result.status is ExperimentStatus.APPROVAL_REQUIRED


@pytest.mark.asyncio
async def test_run_query_captures_source_exactly_once_before_evaluation():
    source = _CountingSource(_batch(_case("SWTR-6")))
    runner = SWTRRealExperimentRunner(
        source,
        policy=RealShadowPolicy(min_improved_cases=1),
    )
    await runner.run_query(
        "project = PO",
        experiment_id="exp-006",
        baseline_id="baseline-v1",
        candidate_id="candidate-v2",
        baseline_agent=_agent(0.4),
        candidate_agent=_agent(0.9),
        limit=5,
    )
    assert source.query_calls == 1
    assert source.key_calls == 0


def test_regression_is_terminal_rejected_and_never_promoted():
    runner = SWTRRealExperimentRunner(
        _FailIfTouchedSource(),
        policy=RealShadowPolicy(min_improved_cases=1),
    )
    result = runner.run_frozen_batch(
        _batch(_case("SWTR-7")),
        experiment_id="exp-007",
        baseline_id="baseline-v1",
        candidate_id="candidate-v2",
        baseline_agent=_agent(0.9),
        candidate_agent=_agent(0.2),
    )
    assert result.status is ExperimentStatus.REJECTED
    assert not hasattr(runner, "promote")
    assert not hasattr(runner, "rollback")
    assert not hasattr(runner, "approve")


def test_invalid_identity_fails_closed_before_agent_execution():
    calls = []

    def agent(snapshot):
        calls.append(snapshot)
        return AgentObservation(answer="x", score=1.0, grounded=True)

    runner = SWTRRealExperimentRunner(
        _FailIfTouchedSource(),
        policy=RealShadowPolicy(min_improved_cases=1),
    )
    with pytest.raises(ValueError, match="must differ"):
        runner.run_frozen_batch(
            _batch(_case("SWTR-8")),
            experiment_id="exp-008",
            baseline_id="same",
            candidate_id="same",
            baseline_agent=agent,
            candidate_agent=agent,
        )
    assert calls == []
