import pytest

from po_agent.adapters.fake import FakeAS21Adapter
from po_agent.harness.dialogue_runtime import SemanticFrame
from po_agent.harness.entity_grounding import GroundedEntityResolver, TeamDirectory, TeamDirectoryEntry
from po_agent.harness.learned_semantics import LearnedSemanticsStore


@pytest.mark.asyncio
async def test_person_and_sprint_shorthand_resolve_from_source_without_declension_table(tmp_path):
    team = TeamDirectory((
        TeamDirectoryEntry("Garanin.R.V", "Гаранин Родион Владимирович", ("WMB",)),
        TeamDirectoryEntry("Ivanov.I.I", "Иванов Иван Иванович", ("WMB",)),
    ))
    resolver = GroundedEntityResolver(FakeAS21Adapter(), team=team)
    frame = SemanticFrame(
        canonical_query="найди задачи исполнитель {member_login} в спринте {sprint_id}",
        slots={"person_raw": "Гаранин", "sprint_raw": "WMB 1"},
        llm_used=True,
    )
    grounded = await resolver.ground(frame, "Покажи задачи Гаранина в WMB 1")
    assert grounded.clarifications == []
    assert "Garanin.R.V" in grounded.canonical_query
    assert "WMB-SPRNT-1" in grounded.canonical_query


@pytest.mark.asyncio
async def test_unknown_person_requires_clarification_instead_of_guessing():
    team = TeamDirectory((TeamDirectoryEntry("Ivanov.I.I", "Иванов Иван Иванович"),))
    resolver = GroundedEntityResolver(FakeAS21Adapter(), team=team)
    frame = SemanticFrame(
        canonical_query="найди задачи исполнитель {member_login}",
        slots={"person_raw": "Неизвестный"},
        llm_used=True,
    )
    grounded = await resolver.ground(frame, "Покажи задачи Неизвестного")
    assert grounded.clarifications[0].field == "member_login"
    assert "Не нашёл" in grounded.clarifications[0].question


@pytest.mark.asyncio
async def test_ambiguous_person_returns_grounded_options():
    team = TeamDirectory((
        TeamDirectoryEntry("Ivanov.I.I", "Иванов Иван Иванович"),
        TeamDirectoryEntry("Ivanov.P.P", "Иванов Петр Петрович"),
    ))
    resolver = GroundedEntityResolver(FakeAS21Adapter(), team=team)
    frame = SemanticFrame(
        canonical_query="найди задачи исполнитель {member_login}",
        slots={"person_raw": "Иванов"},
        llm_used=True,
    )
    grounded = await resolver.ground(frame, "Покажи задачи Иванова")
    assert grounded.clarifications[0].field == "member_login"
    assert set(grounded.clarifications[0].options) == {"Ivanov.I.I", "Ivanov.P.P"}


@pytest.mark.asyncio
async def test_business_term_is_clarified_until_learned_then_resolved(tmp_path):
    store = LearnedSemanticsStore(tmp_path / "semantics.json")
    resolver = GroundedEntityResolver(FakeAS21Adapter(), semantics=store)
    frame = SemanticFrame(
        canonical_query="найди задачи статус {status}",
        slots={"status_raw": "открытые", "status_semantic": "open_tasks"},
        llm_used=True,
    )
    first = await resolver.ground(frame, "Покажи открытые задачи")
    assert first.clarifications[0].field == "status"
    store.learn_explicit_definition(
        term="open_tasks",
        meaning="In Progress",
        source_trace_id="trace-1",
    )
    second = await resolver.ground(frame, "Покажи открытые задачи")
    assert second.clarifications == []
    assert second.canonical_query == "найди задачи статус In Progress"
