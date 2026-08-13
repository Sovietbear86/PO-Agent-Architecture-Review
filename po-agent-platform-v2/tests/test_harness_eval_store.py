import pytest

from po_agent.harness import HarnessRequest, build_fake_runtime


@pytest.mark.asyncio
async def test_negative_feedback_is_automatically_curated_into_eval_seed():
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

    seeds = runtime.evals.candidates()
    assert len(seeds) == 1
    seed = seeds[0]
    assert seed.source_feedback_id == feedback.feedback_id
    assert seed.query == "Покажи WMB-102"
    assert seed.expected_intent == "task_blocker_analysis"
    assert seed.expected_entity == "WMB-102"
    assert seed.expected_facts == ["Нужно показать блокировку задачи"]
    assert seed.source_versions["skill_id"] == "task-lookup"
    assert seed.status == "candidate"


@pytest.mark.asyncio
async def test_automatic_eval_seed_does_not_change_router_or_promote_behavior():
    runtime = build_fake_runtime()
    response = await runtime.process(HarnessRequest(query="Покажи WMB-101", session_id="eval-s2"))
    runtime.submit_feedback(
        response.trace_id,
        "down",
        expected_intent="task_summary",
    )

    candidates = runtime.evals.candidates()
    assert len(candidates) == 1
    assert candidates[0].expected_intent == "task_summary"

    # Learning data is collected automatically, but production behavior still
    # changes only through the existing offline-eval / approval / promotion gate.
    again = await runtime.process(HarnessRequest(query="Покажи WMB-101", session_id="eval-s2"))
    assert again.skill_id == "task-lookup"


@pytest.mark.asyncio
async def test_plain_positive_feedback_is_not_a_failure_eval_seed():
    runtime = build_fake_runtime()
    response = await runtime.process(HarnessRequest(query="Покажи WMB-101", session_id="eval-positive"))
    feedback = runtime.submit_feedback(response.trace_id, "up")
    assert runtime.evals.candidates() == []

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
