import pytest

from po_agent.harness import HarnessRequest, build_fake_runtime
from po_agent.harness.eval_store import seed_from_feedback


@pytest.mark.asyncio
async def test_negative_feedback_can_be_explicitly_curated_into_eval_seed():
    runtime = build_fake_runtime()
    response = await runtime.process(HarnessRequest(query="Покажи WMB-102", session_id="eval-s1"))
    feedback = runtime.submit_feedback(
        response.trace_id,
        "down",
        correction="Нужно показать блокировку задачи",
        expected_intent="task_blocker_analysis",
        expected_entity="WMB-102",
        comment="routing failure seed",
    )

    seed = runtime.create_eval_seed(response.trace_id, feedback.feedback_id)
    assert seed.query == "Покажи WMB-102"
    assert seed.expected_intent == "task_blocker_analysis"
    assert seed.expected_entity == "WMB-102"
    assert seed.expected_facts == ["Нужно показать блокировку задачи"]
    assert seed.source_versions["skill_id"] == "task-lookup"
    assert seed.status == "candidate"
    assert runtime.evals.get(seed.eval_id) == seed


@pytest.mark.asyncio
async def test_eval_seed_creation_is_not_automatic_and_does_not_change_router():
    runtime = build_fake_runtime()
    response = await runtime.process(HarnessRequest(query="Покажи WMB-101", session_id="eval-s2"))
    feedback = runtime.submit_feedback(
        response.trace_id,
        "down",
        expected_intent="task_summary",
    )

    assert runtime.evals.candidates() == []
    seed = runtime.create_eval_seed(response.trace_id, feedback.feedback_id)
    assert [item.eval_id for item in runtime.evals.candidates()] == [seed.eval_id]

    again = await runtime.process(HarnessRequest(query="Покажи WMB-101", session_id="eval-s2"))
    assert again.skill_id == "task-lookup"


@pytest.mark.asyncio
async def test_plain_positive_feedback_is_not_a_failure_eval_seed():
    runtime = build_fake_runtime()
    response = await runtime.process(HarnessRequest(query="Покажи WMB-101", session_id="eval-positive"))
    feedback = runtime.submit_feedback(response.trace_id, "up")

    with pytest.raises(ValueError, match="not an eval failure seed"):
        runtime.create_eval_seed(response.trace_id, feedback.feedback_id)


@pytest.mark.asyncio
async def test_eval_seed_requires_feedback_from_same_trace():
    runtime = build_fake_runtime()
    first = await runtime.process(HarnessRequest(query="Покажи WMB-101", session_id="eval-match"))
    second = await runtime.process(HarnessRequest(query="Покажи WMB-102", session_id="eval-match"))
    feedback = runtime.submit_feedback(second.trace_id, "down", expected_intent="task_summary")

    with pytest.raises(ValueError, match="unknown feedback_id"):
        runtime.create_eval_seed(first.trace_id, feedback.feedback_id)
