import asyncio
import types

from po_agent.harness.dialogue_runtime import ClarificationNeed, SemanticFrame
from po_agent.harness.entity_grounding import TeamDirectory, TeamDirectoryEntry
from po_agent.harness.production_entity_grounding_v2 import ProductionEntityResolverV2


def _resolver_with_identities(identities: list[dict[str, str]]) -> ProductionEntityResolverV2:
    resolver = object.__new__(ProductionEntityResolverV2)

    async def semantic_context(self):
        return {"assignee_identities": identities}

    resolver.semantic_context = types.MethodType(semantic_context, resolver)
    return resolver


def _empty_frame() -> SemanticFrame:
    return SemanticFrame(
        canonical_query="",
        intent_hint="",
        slots={},
        clarifications=[],
        confidence=0.0,
        llm_used=False,
    )


def test_unique_identity_recovery_does_not_require_llm_intent() -> None:
    resolver = _resolver_with_identities([
        {"display_name": "Родион Гаранин", "login": "Garanin.R.V", "external_id": "Garanin.R.V"},
        {"display_name": "Михаил Семавин", "login": "Semavin.M.M", "external_id": "Semavin.M.M"},
    ])
    slots: dict[str, str] = {}

    asyncio.run(resolver._infer_missing_person_from_query(_empty_frame(), slots, "Задачи Гаранина"))

    assert slots["person_raw"] == "Родион Гаранин"


def test_ambiguous_identity_recovery_remains_fail_closed() -> None:
    resolver = _resolver_with_identities([
        {"display_name": "Иван Иванов", "login": "Ivanov.I.A", "external_id": "Ivanov.I.A"},
        {"display_name": "Илья Иванов", "login": "Ivanov.I.B", "external_id": "Ivanov.I.B"},
    ])
    slots: dict[str, str] = {}

    asyncio.run(resolver._infer_missing_person_from_query(_empty_frame(), slots, "Задачи Иванова"))

    assert "person_raw" not in slots


def test_existing_llm_person_slot_is_never_overridden() -> None:
    resolver = _resolver_with_identities([
        {"display_name": "Родион Гаранин", "login": "Garanin.R.V", "external_id": "Garanin.R.V"},
    ])
    slots = {"person_raw": "Гаранина"}

    asyncio.run(resolver._infer_missing_person_from_query(_empty_frame(), slots, "Задачи Гаранина"))

    assert slots["person_raw"] == "Гаранина"


class _EmptyBulkTaskAdapter:
    async def search_tasks(self, query: str, **kwargs):
        del query, kwargs
        return []


def test_semantic_context_seeds_identity_from_team_directory_when_bulk_scan_is_empty() -> None:
    team = TeamDirectory((
        TeamDirectoryEntry(login="Garanin.R.V", full_name="Родион Гаранин", products=("DMS", "OLP")),
        TeamDirectoryEntry(login="Semavin.M.M", full_name="Михаил Семавин", products=("DMS",)),
    ))
    resolver = ProductionEntityResolverV2(_EmptyBulkTaskAdapter(), team=team)

    context = asyncio.run(resolver.semantic_context())

    assert {item["login"] for item in context["assignee_identities"]} == {"Garanin.R.V", "Semavin.M.M"}
    assert "Garanin.R.V" in context["known_assignees"]

    slots: dict[str, str] = {}
    asyncio.run(resolver._infer_missing_person_from_query(_empty_frame(), slots, "Задачи Гаранина"))
    assert slots["person_raw"] == "Родион Гаранин"


def test_generic_filter_clarification_is_removed_when_all_material_constraints_are_grounded() -> None:
    needs = [ClarificationNeed("filters", "Уточните значения фильтров")]
    slots = {
        "person_raw": "Андрей Моисеев",
        "member_login": "Moiseev.A.N",
        "product": "DMS",
        "status": "not_completed",
    }
    final_slots = {
        "person_raw": "Андрей Моисеев",
        "member_login": "Moiseev.A.N",
        "assignee": "Moiseev.A.N",
        "product": "DMS",
        "status": "not_completed",
    }

    result = ProductionEntityResolverV2._reconcile_grounded_clarifications(
        needs,
        slots=slots,
        final_slots=final_slots,
        original_query="Открытые задачи Андрея Моисеева в DMS",
    )

    assert result == []


def test_generic_filter_clarification_is_preserved_when_explicit_space_is_not_grounded() -> None:
    needs = [ClarificationNeed("filters", "Уточните значения фильтров")]
    slots = {
        "person_raw": "Андрей Моисеев",
        "member_login": "Moiseev.A.N",
        "status": "not_completed",
    }
    final_slots = {
        "person_raw": "Андрей Моисеев",
        "member_login": "Moiseev.A.N",
        "assignee": "Moiseev.A.N",
        "status": "not_completed",
    }

    result = ProductionEntityResolverV2._reconcile_grounded_clarifications(
        needs,
        slots=slots,
        final_slots=final_slots,
        original_query="Открытые задачи Андрея Моисеева в DMS",
    )

    assert result == needs


def test_specific_unresolved_clarification_is_never_suppressed_by_other_grounded_fields() -> None:
    needs = [ClarificationNeed("sprint_id", "Какой спринт?")]
    slots = {
        "person_raw": "Андрей Моисеев",
        "member_login": "Moiseev.A.N",
        "product": "DMS",
        "status": "not_completed",
    }
    final_slots = {
        "person_raw": "Андрей Моисеев",
        "member_login": "Moiseev.A.N",
        "assignee": "Moiseev.A.N",
        "product": "DMS",
        "status": "not_completed",
    }

    result = ProductionEntityResolverV2._reconcile_grounded_clarifications(
        needs,
        slots=slots,
        final_slots=final_slots,
        original_query="Открытые задачи Андрея Моисеева в DMS",
    )

    assert result == needs
