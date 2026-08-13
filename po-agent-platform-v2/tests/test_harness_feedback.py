import pytest

from po_agent.harness import HarnessRequest, build_fake_runtime


@pytest.mark.asyncio
async def test_feedback_is_linked_to_existing_trace_versions_and_eval_loop():
    runtime = build_fake_runtime()
    response = await runtime.process(HarnessRequest(query="Покажи WMB-102", session_id="fb-session"))

    record = runtime.submit_feedback(
        response.trace_id,
        "down",
        correction="Нужно было объяснить причину блокировки",
        expected_intent="task_blocker_analysis",
        expected_entity="WMB-102",
        comment="use as eval seed",
    )
    assert record.trace_id == response.trace_id
    assert record.session_id == "fb-session"
    assert record.rating == "down"

    saved = runtime.feedback.by_trace(response.trace_id)
    assert len(saved) == 1
    assert saved[0].correction == "Нужно было объяснить причину блокировки"
    assert saved[0].metadata["skill_id"] == "task-lookup"
    assert saved[0].metadata["agent_version"] == "2.1-recovery"

    # Corrective feedback is automatically converted into an offline candidate;
    # it does not directly rewrite or promote production behavior.
    candidates = runtime.evals.candidates()
    assert len(candidates) == 1
    assert candidates[0].source_trace_id == response.trace_id
    assert candidates[0].expected_intent == "task_blocker_analysis"
    assert candidates[0].expected_entity == "WMB-102"


@pytest.mark.asyncio
async def test_positive_feedback_does_not_mutate_runtime_or_create_failure_seed():
    runtime = build_fake_runtime()
    response = await runtime.process(HarnessRequest(query="Покажи WMB-101", session_id="fb-positive"))
    runtime.submit_feedback(response.trace_id, "up")

    assert runtime.evals.candidates() == []
    repeat = await runtime.process(HarnessRequest(query="Покажи WMB-101", session_id="fb-positive"))
    assert repeat.skill_id == "task-lookup"
    assert repeat.data["task"]["key"] == "WMB-101"


def test_feedback_rejects_unknown_trace_and_invalid_rating():
    runtime = build_fake_runtime()
    with pytest.raises(ValueError, match="unknown trace_id"):
        runtime.submit_feedback("missing", "down")

    from po_agent.harness.feedback_store import make_feedback
    with pytest.raises(ValueError, match="rating"):
        make_feedback(trace_id="x", session_id=None, rating="maybe")
