from __future__ import annotations

import pytest

from po_agent.harness.agent_core_v3 import AgentCoreV3ContractError, CapabilityContractV3, SOURCE_AUTHORITY_REAL_AS21
from po_agent.harness.agent_core_v3_registry import CapabilityRegistrationV3, CapabilityRegistryV3, build_h1_task_registry


def _registration(capability_id: str, intent: str) -> CapabilityRegistrationV3:
    return CapabilityRegistrationV3(
        contract=CapabilityContractV3(
            id=capability_id,
            version="test",
            supported_constraints=frozenset({"task_key"}),
            source_authority=SOURCE_AUTHORITY_REAL_AS21,
            executor_id=f"{capability_id}-executor",
        ),
        family="tasks",
        intents=frozenset({intent}),
        summary="test capability",
    )


def test_h1_registry_contains_only_reusable_task_capabilities() -> None:
    registry = build_h1_task_registry()

    assert len(registry) == 2
    assert registry.resolve_intent("task_lookup").contract.id == "task-lookup-v3"
    assert registry.resolve_intent("task_search").contract.id == "task-search-v3"

    catalog = registry.compact_catalog(family="tasks")
    assert [item["id"] for item in catalog] == ["task-lookup-v3", "task-search-v3"]
    assert all(item["source_authority"] == "REAL_AS21" for item in catalog)
    serialized = repr(catalog)
    assert "Garanin" not in serialized
    assert "Kalachanov" not in serialized
    assert "WMB-" not in serialized


def test_registry_rejects_duplicate_capability_id() -> None:
    registry = CapabilityRegistryV3()
    registry.register(_registration("task-one", "intent_one"))

    with pytest.raises(ValueError, match="already registered"):
        registry.register(_registration("task-one", "intent_two"))


def test_registry_rejects_duplicate_intent_owner() -> None:
    registry = CapabilityRegistryV3()
    registry.register(_registration("task-one", "shared_intent"))

    with pytest.raises(ValueError, match="already owned"):
        registry.register(_registration("task-two", "shared_intent"))


def test_registry_fails_closed_for_unknown_intent() -> None:
    registry = build_h1_task_registry()

    with pytest.raises(AgentCoreV3ContractError) as exc_info:
        registry.resolve_intent("release_forecast")

    assert exc_info.value.details == {"intent": "release_forecast"}


def test_compact_catalog_is_stable_and_does_not_expose_executor_internals() -> None:
    registry = build_h1_task_registry()
    first = registry.compact_catalog()
    second = registry.compact_catalog()

    assert first == second
    assert all("executor_id" not in item for item in first)
    assert all("oracle_id" not in item for item in first)
