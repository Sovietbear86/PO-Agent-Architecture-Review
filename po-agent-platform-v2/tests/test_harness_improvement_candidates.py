from po_agent.harness.failure_miner import FailureCluster
from po_agent.harness.improvement_candidates import ImprovementCandidateGenerator


def test_intent_failure_generates_non_executable_routing_proposal():
    cluster = FailureCluster(
        key="intent_mismatch:task-lookup->task_summary",
        category="intent_mismatch",
        count=3,
        eval_ids=("e1", "e2", "e3"),
        queries=("q1", "q2", "q3"),
        expected_intents=("task_summary",),
        affected_skill_ids=("task-lookup",),
        recommendation="Review deterministic routing.",
    )
    candidate = ImprovementCandidateGenerator().generate(cluster)
    assert candidate.kind == "routing_rule"
    assert candidate.status == "draft"
    assert candidate.requires_human_approval is True
    assert candidate.proposed_change["apply"] is False
    assert candidate.source_eval_ids == ("e1", "e2", "e3")


def test_entity_failure_generates_context_proposal_not_patch():
    cluster = FailureCluster(
        key="entity_resolution:WMB-101",
        category="entity_resolution",
        count=2,
        eval_ids=("e1", "e2"),
        queries=("что с ней?", "а там?"),
        expected_intents=(),
        affected_skill_ids=("task-search",),
        recommendation="Review entity resolution.",
    )
    candidate = ImprovementCandidateGenerator().generate(cluster)
    assert candidate.kind == "context_rule"
    assert candidate.proposed_change["action"] == "review_entity_resolution"
    assert candidate.proposed_change["apply"] is False


def test_candidate_rationale_preserves_evidence_count():
    cluster = FailureCluster(
        key="uncategorized:manual_review", category="uncategorized", count=4,
        eval_ids=("1", "2", "3", "4"), queries=("a", "b", "c", "d"),
        expected_intents=(), affected_skill_ids=(), recommendation="Manual triage required.",
    )
    candidate = ImprovementCandidateGenerator().generate(cluster)
    assert "4 curated evaluation seed(s)" in candidate.rationale
    assert candidate.proposed_change["apply"] is False
