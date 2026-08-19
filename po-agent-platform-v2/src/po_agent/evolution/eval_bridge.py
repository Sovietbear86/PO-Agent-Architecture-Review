"""Bridge existing evaluation reports into Learning Loop 012 snapshots."""
from typing import Any, Dict, Optional

from po_agent.evaluation.runner import EvalReport
from po_agent.evolution.learning_loop import EvaluationSnapshot


def snapshot_from_eval_report(
    report: EvalReport,
    *,
    false_green_count: int = 0,
    error_count: int = 0,
    metadata: Optional[Dict[str, Any]] = None,
) -> EvaluationSnapshot:
    """Create an immutable promotion-gate snapshot from the existing EvalRunner report.

    False-green and execution-error counters stay explicit because they come from
    safety/e2e evaluators rather than the structural routing EvalRunner itself.
    """
    return EvaluationSnapshot(
        total_cases=report.total_cases,
        passed_cases=report.passed_cases,
        false_green_count=false_green_count,
        error_count=error_count,
        metadata={
            "run_id": report.run_id,
            "timestamp": report.timestamp.isoformat(),
            **dict(metadata or {}),
        },
    )


__all__ = ["snapshot_from_eval_report"]
