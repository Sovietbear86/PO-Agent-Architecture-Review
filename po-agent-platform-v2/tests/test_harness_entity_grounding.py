import pytest

from po_agent.adapters.fake import FakeAS21Adapter
from po_agent.harness.dialogue_runtime import SemanticFrame
from po_agent.harness.entity_grounding import GroundedEntityResolver, TeamDirectory, TeamDirectoryEntry
from po_agent.harness.learned_semantics import LearnedSemanticsStore
from po_agent.harness.live_entity_grounding import LiveGroundedEntityResolver


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


@pytest.mark.asyncio
async def test_llm_proposed_unknown_login_is_rejected_even_if_user_text_contains_it():
    resolver = GroundedEntityResolver(FakeAS21Adapter())
    frame = SemanticFrame(
        canonical_query="найди задачи исполнитель {member_login}",
        slots={"member_login": "Plausible.ButMissing"},
        llm_used=True,
    )
    grounded = await resolver.ground(frame, "Покажи задачи Plausible.ButMissing")
    assert "member_login" not in grounded.slots
    assert grounded.clarifications[0].field == "member_login"
    assert "по данным источника" in grounded.clarifications[0].question


@pytest.mark.asyncio
async def test_llm_proposed_unknown_sprint_and_release_are_rejected():
    resolver = GroundedEntityResolver(FakeAS21Adapter())
    frame = SemanticFrame(
        canonical_query="найди задачи в {sprint_id} релиз {release_id}",
        slots={"sprint_id": "WMB-SPRNT-999", "release_id": "WMB-2099-Q9"},
        llm_used=True,
    )
    grounded = await resolver.ground(frame, "Покажи задачи")
    assert "sprint_id" not in grounded.slots
    assert "release_id" not in grounded.slots
    assert {item.field for item in grounded.clarifications} == {"sprint_id", "release_id"}


@pytest.mark.asyncio
async def test_llm_proposed_unknown_status_is_rejected_but_virtual_filter_is_allowed():
    resolver = GroundedEntityResolver(FakeAS21Adapter())
    invalid = SemanticFrame(
        canonical_query="найди задачи статус {status}",
        slots={"status": "Almost Done"},
        llm_used=True,
    )
    rejected = await resolver.ground(invalid, "Покажи почти готовые")
    assert "status" not in rejected.slots
    assert rejected.clarifications[0].field == "status"

    virtual = SemanticFrame(
        canonical_query="найди задачи статус {status}",
        slots={"status": "not_completed"},
        llm_used=True,
    )
    accepted = await resolver.ground(virtual, "Покажи незавершённые")
    assert accepted.clarifications == []
    assert accepted.slots["status"] == "not_completed"


@pytest.mark.asyncio
async def test_live_release_raw_resolves_even_when_provider_omits_release_placeholder():
    resolver = LiveGroundedEntityResolver(FakeAS21Adapter())
    frame = SemanticFrame(
        canonical_query="покажи здоровье релиза",
        intent_hint="release_health",
        slots={},
        llm_used=True,
    )

    grounded = await resolver.ground(frame, "Покажи здоровье релиза WMB-2024-Q3")

    assert grounded.clarifications == []
    assert grounded.slots["release_id"] == "WMB-2024-Q3"
    assert "WMB-2024-Q3" in grounded.canonical_query
    assert "{release_id}" not in grounded.canonical_query


@pytest.mark.asyncio
async def test_live_release_placeholder_repair_remains_fail_closed_for_unknown_release():
    resolver = LiveGroundedEntityResolver(FakeAS21Adapter())
    frame = SemanticFrame(
        canonical_query="покажи здоровье релиза",
        intent_hint="release_health",
        slots={},
        llm_used=True,
    )

    grounded = await resolver.ground(frame, "Покажи здоровье релиза NONEXISTENT")

    assert "release_id" not in grounded.slots
    assert grounded.clarifications
    assert grounded.clarifications[0].field == "release_id"
