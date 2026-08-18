from dataclasses import dataclass

import pytest

from po_agent.harness.swtr_real_evaluation import AgentObservation, RealShadowPolicy, ShadowDecision
from po_agent.harness.swtr_real_experiment import ExperimentStatus
from po_agent.harness.swtr_real_pilot import SWTRFirstRealPilot


@dataclass
class _Manifest:
    manifest_sha256: str = "m" * 64
    task_keys: tuple[str, ...] = ("A", "B")

@dataclass
class _Obs:
    score: float
    grounded: bool = True
    hallucination: bool = False
    wrong_skill: bool = False
    provider_error: bool = False

@dataclass
class _Case:
    task_key: str
    content_sha256: str
    decision: ShadowDecision
    baseline: _Obs
    candidate: _Obs
    score_delta: float
    evidence_sha256: str

@dataclass
class _Evidence:
    cases: tuple
    improved_cases: int
    equivalent_cases: int
    regressed_cases: int
    blocked_cases: int

@dataclass
class _Result:
    manifest: _Manifest
    evidence: _Evidence
    status: ExperimentStatus
    report_sha256: str = "r" * 64


class _Runner:
    def __init__(self, result):
        self.result = result
        self.calls = []

    async def run_keys(self, keys, **kwargs):
        self.calls.append((tuple(keys), kwargs))
        return self.result


def _result(status=ExperimentStatus.APPROVAL_REQUIRED):
    cases = (
        _Case("A", "a" * 64, ShadowDecision.IMPROVED, _Obs(.5), _Obs(.8), .3, "1" * 64),
        _Case("B", "b" * 64, ShadowDecision.EQUIVALENT, _Obs(.7), _Obs(.71), .01, "2" * 64),
    )
    return _Result(_Manifest(), _Evidence(cases, 1, 1, 0, 0), status)


def test_pilot_bounds_are_small_and_explicit():
    runner = _Runner(_result())
    with pytest.raises(ValueError):
        SWTRFirstRealPilot(runner, max_pilot_cases=11)
    pilot = SWTRFirstRealPilot(runner, max_pilot_cases=2)
    with pytest.raises(ValueError):
        pilot._normalize_keys([], 2)
    with pytest.raises(ValueError):
        pilot._normalize_keys(["A", "A"], 2)
    with pytest.raises(ValueError):
        pilot._normalize_keys(["A", "B", "C"], 2)


@pytest.mark.asyncio
async def test_pilot_delegates_exactly_one_explicit_key_run_and_reports_evidence():
    runner = _Runner(_result())
    pilot = SWTRFirstRealPilot(runner, max_pilot_cases=2)
    report = await pilot.run_keys(
        ["B", "A"], experiment_id="pilot-1", baseline_id="base", candidate_id="cand",
        baseline_agent=lambda _: None, candidate_agent=lambda _: None,
    )
    assert len(runner.calls) == 1
    assert runner.calls[0][0] == ("B", "A")
    assert [c.task_key for c in report.cases] == ["A", "B"]
    assert report.cases[0].decision is ShadowDecision.IMPROVED
    assert report.summary == "status=approval_required; cases=2; improved=1; equivalent=1; regressed=0; blocked=0"
    assert len(report.pilot_sha256) == 64
    assert SWTRFirstRealPilot.requires_human_review(report) is True


def test_pilot_report_is_deterministic_and_status_bound():
    first = SWTRFirstRealPilot._report(_result())
    second = SWTRFirstRealPilot._report(_result())
    assert first.pilot_sha256 == second.pilot_sha256
    rejected = SWTRFirstRealPilot._report(_result(ExperimentStatus.REJECTED))
    assert rejected.pilot_sha256 != first.pilot_sha256
    assert SWTRFirstRealPilot.requires_human_review(rejected) is False


@pytest.mark.asyncio
async def test_pilot_fails_closed_when_manifest_corpus_differs():
    result = _result()
    result.manifest = _Manifest(task_keys=("A", "EVIL"))
    pilot = SWTRFirstRealPilot(_Runner(result), max_pilot_cases=2)
    with pytest.raises(RuntimeError):
        await pilot.run_keys(
            ["A", "B"], experiment_id="pilot-1", baseline_id="base", candidate_id="cand",
            baseline_agent=lambda _: None, candidate_agent=lambda _: None,
        )


def test_public_pilot_has_no_promotion_or_mutation_api():
    forbidden = {
        "promote", "rollback", "approve", "apply", "execute", "update_task",
        "transition_task", "change_status", "add_comment", "upload_attachment",
    }
    assert forbidden.isdisjoint(set(dir(SWTRFirstRealPilot)))
