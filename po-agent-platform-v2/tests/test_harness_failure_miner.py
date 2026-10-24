from po_agent.harness.eval_store import EvalSeed
from po_agent.harness.failure_miner import FailureMiner


def _seed(eval_id: str, query: str, expected_intent: str, skill_id: str) -> EvalSeed:
    return EvalSeed(
        eval_id=eval_id,
        source_trace_id=f"trace-{eval_id}",
        source_feedback_id=f"feedback-{eval_id}",
        created_at=f"2026-08-12T20:00:0{eval_id}+00:00",
        query=query,
        expected_intent=expected_intent,
        source_versions={"skill_id": skill_id, "agent": "2.1-recovery"},
    )


def test_failure_miner_groups_repeated_intent_mismatches():
    miner = FailureMiner()
    seeds = [
        _seed("1", "Покажи WMB-101", "task_summary", "task-lookup"),
        _seed("2", "Покажи WMB-102", "task_summary", "task-lookup"),
    ]
    clusters = miner.mine(seeds)
    assert len(clusters) == 1
    cluster = clusters[0]
    assert cluster.category == "intent_mismatch"
    assert cluster.count == 2
    assert cluster.expected_intents == ("task_summary",)
    assert cluster.affected_skill_ids == ("task-lookup",)
    assert "before proposing a rule change" in cluster.recommendation


def test_failure_miner_threshold_filters_one_off_noise():
    miner = FailureMiner()
    seeds = [
        _seed("1", "A", "task_summary", "task-lookup"),
        _seed("2", "B", "release_progress", "release-health"),
    ]
    assert miner.mine(seeds, min_occurrences=2) == []


def test_failure_miner_separates_different_failure_types():
    miner = FailureMiner()
    intent_seed = _seed("1", "A", "task_summary", "task-lookup")
    entity_seed = EvalSeed(
        eval_id="2", source_trace_id="t2", source_feedback_id="f2",
        created_at="2026-08-12T20:00:02+00:00", query="что с ней?",
        expected_entity="WMB-101", source_versions={"skill_id": "task-search"},
    )
    clusters = miner.mine([intent_seed, entity_seed])
    assert {c.category for c in clusters} == {"intent_mismatch", "entity_resolution"}


def test_failure_miner_only_proposes_review_not_mutation():
    seed = _seed("1", "Покажи WMB-101", "task_summary", "task-lookup")
    cluster = FailureMiner().mine([seed])[0]
    assert "Review" in cluster.recommendation
    assert "proposing" in cluster.recommendation
