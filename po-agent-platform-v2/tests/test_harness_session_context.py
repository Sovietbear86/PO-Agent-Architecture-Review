import pytest

from po_agent.harness import HarnessRequest, build_fake_runtime


@pytest.mark.asyncio
async def test_task_follow_up_resolves_only_inside_same_session():
    runtime = build_fake_runtime()
    first = await runtime.process(HarnessRequest(query="Покажи WMB-102", session_id="ctx-task"))
    assert first.skill_id == "task-lookup"

    follow = await runtime.process(HarnessRequest(query="что с ней?", session_id="ctx-task"))
    assert follow.skill_id == "task-lookup"
    assert follow.data["task"]["key"] == "WMB-102"

    other = await runtime.process(HarnessRequest(query="что с ней?", session_id="ctx-other"))
    assert other.skill_id == "task-search"


@pytest.mark.asyncio
async def test_release_follow_up_reuses_selected_release_without_copying_history():
    runtime = build_fake_runtime()
    selected = await runtime.process(HarnessRequest(query="Состояние WMB-2024-Q3", session_id="ctx-release"))
    assert selected.skill_id == "release-health"

    risks = await runtime.process(HarnessRequest(query="а какие там риски?", session_id="ctx-release"))
    assert risks.skill_id == "release-risk-queue"
    assert risks.data["release_id"] == "WMB-2024-Q3"

    records = runtime.history.by_session("ctx-release")
    assert records[-1].request == "а какие там риски?"


@pytest.mark.asyncio
async def test_sprint_follow_up_uses_current_sprint():
    runtime = build_fake_runtime()
    await runtime.process(HarnessRequest(query="Покажи WMB-SPRNT-1", session_id="ctx-sprint"))
    velocity = await runtime.process(HarnessRequest(query="а velocity там какой?", session_id="ctx-sprint"))
    assert velocity.skill_id == "sprint-velocity"
    assert velocity.data["sprint_id"] == "WMB-SPRNT-1"


@pytest.mark.asyncio
async def test_unrelated_new_query_is_not_polluted_by_session_context():
    runtime = build_fake_runtime()
    await runtime.process(HarnessRequest(query="Покажи WMB-101", session_id="ctx-clean"))
    result = await runtime.process(HarnessRequest(query="Найди login", session_id="ctx-clean"))
    assert result.skill_id == "task-search"
    assert result.data["filters"]["phrase"] == "login"


def test_session_context_can_be_explicitly_cleared():
    runtime = build_fake_runtime()
    ctx = runtime.sessions.get("clear-me")
    ctx.current_task = "WMB-101"
    runtime.sessions.clear("clear-me")
    assert runtime.sessions.snapshot("clear-me").current_task is None
