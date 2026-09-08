from types import MappingProxyType

import pytest

from po_agent.harness.agent_core_v3 import AgentCoreV3ContractError, AgentCoreV3FailureCode
from po_agent.harness.agent_core_v3_loop import AgentLoopObservationV3, AgentLoopPlannerV3, resolve_observation_reference
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


def test_planner_parser_accepts_typed_json_after_think_wrapper() -> None:
    raw = '<think>internal reasoning</think>\n{"call":null,"final":{"answer":"ok"},"rationale":null}'
    parsed = AgentLoopPlannerV3._parse(raw)
    assert parsed is not None
    action = AgentLoopPlannerV3._typed_candidate(parsed)
    assert action is not None
    assert action.action == "final"
    assert action.final_answer == "ok"


def test_planner_parser_extracts_embedded_typed_call() -> None:
    raw = 'Result follows: {"call":{"capability_id":"task-lookup-v3","constraints":{"task_key":"DMS-380"}},"final":null,"rationale":"lookup"}'
    parsed = AgentLoopPlannerV3._parse(raw)
    assert parsed is not None
    action = AgentLoopPlannerV3._typed_candidate(parsed)
    assert action is not None
    assert action.action == "call_capability"
    assert action.capability_id == "task-lookup-v3"
    assert action.constraints == {"task_key": "DMS-380"}


def test_typed_call_requires_capability_id() -> None:
    action = AgentLoopPlannerV3._typed_candidate(
        {"call": {"capability_id": "", "constraints": {}}, "final": None, "rationale": None}
    )
    assert action is None


def test_typed_final_requires_nonempty_answer() -> None:
    action = AgentLoopPlannerV3._typed_candidate(
        {"call": None, "final": {"answer": ""}, "rationale": None}
    )
    assert action is None


def test_both_typed_branches_null_is_not_executable() -> None:
    assert AgentLoopPlannerV3._typed_candidate(
        {"call": None, "final": None, "rationale": None}
    ) is None


def test_both_typed_branches_present_is_not_executable() -> None:
    assert AgentLoopPlannerV3._typed_candidate(
        {
            "call": {"capability_id": "task-lookup-v3", "constraints": {"task_key": "DMS-380"}},
            "final": {"answer": "done"},
            "rationale": None,
        }
    ) is None


def test_legacy_action_only_object_is_not_executable() -> None:
    assert AgentLoopPlannerV3._typed_candidate(
        {
            "action": "call_capability",
            "capability_id": "task-lookup-v3",
            "constraints": {"task_key": "DMS-380"},
        }
    ) is None
