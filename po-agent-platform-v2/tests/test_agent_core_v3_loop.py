from types import MappingProxyType

import pytest

from po_agent.harness.agent_core_v3 import AgentCoreV3ContractError, AgentCoreV3FailureCode
from po_agent.harness.agent_core_v3_loop import AgentLoopObservationV3, resolve_observation_reference
from po_agent.harness.agent_core_v3_pilot import AgentCoreV3PilotProcessor


def _observation() -> AgentLoopObservationV3:
    return AgentLoopObservationV3(
        step=1,
        capability_id="task-lookup-v3",
        constraints=MappingProxyType({"task_key": "DMS-380"}),
        data={
            "task": {
                "key": "DMS-380",
                "assignee_login": "Example.User",
                "project_space": "DMS",
            },
            "found": True,
        },
    )


def test_observation_reference_resolves_authoritative_fact() -> None:
    value = resolve_observation_reference(
        "$obs.1.task.assignee_login",
        observations=[_observation()],
    )
    assert value == "Example.User"


def test_observation_reference_fails_closed_for_missing_fact() -> None:
    with pytest.raises(AgentCoreV3ContractError) as exc:
        resolve_observation_reference(
            "$obs.1.task.nonexistent",
            observations=[_observation()],
        )
    assert exc.value.code == AgentCoreV3FailureCode.UNRESOLVED_CONSTRAINT


def test_literal_task_key_must_exist_in_original_query() -> None:
    query = "Проверь DMS-380 и затем покажи задачи его исполнителя"
    assert AgentCoreV3PilotProcessor._literal_is_source_safe("task_key", "DMS-380", query)
    assert not AgentCoreV3PilotProcessor._literal_is_source_safe("task_key", "DMS-999", query)


def test_observation_binding_is_source_safe_before_resolution() -> None:
    query = "Проверь DMS-380 и затем покажи задачи его исполнителя"
    assert AgentCoreV3PilotProcessor._literal_is_source_safe(
        "assignee", "$obs.1.task.assignee_login", query
    )


def test_space_literal_must_be_explicit_in_original_query() -> None:
    query = "Проверь DMS-380 и покажи задачи исполнителя в WMB"
    assert AgentCoreV3PilotProcessor._literal_is_source_safe("space", "WMB", query)
    assert not AgentCoreV3PilotProcessor._literal_is_source_safe("space", "STS", query)
