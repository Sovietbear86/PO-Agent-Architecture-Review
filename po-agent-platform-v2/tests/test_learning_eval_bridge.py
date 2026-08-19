from datetime import datetime

from po_agent.evaluation.runner import EvalReport
from po_agent.evolution.eval_bridge import snapshot_from_eval_report


def test_eval_report_bridge_preserves_comparable_evidence():
    report = EvalReport(
        run_id="run-1",
        timestamp=datetime(2026, 8, 19, 12, 0, 0),
        total_cases=8,
        passed_cases=7,
        failed_cases=1,
        pass_rate=87.5,
        results=[],
    )
    snap = snapshot_from_eval_report(
        report,
        false_green_count=1,
        error_count=2,
        metadata={"case_set": "core8"},
    )
    assert snap.total_cases == 8
    assert snap.passed_cases == 7
    assert snap.false_green_count == 1
    assert snap.error_count == 2
    assert snap.metadata["run_id"] == "run-1"
    assert snap.metadata["case_set"] == "core8"
