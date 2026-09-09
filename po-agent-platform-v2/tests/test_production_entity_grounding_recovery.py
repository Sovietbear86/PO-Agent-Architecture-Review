import asyncio
import types

from po_agent.harness.dialogue_runtime import SemanticFrame
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
