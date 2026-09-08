import pytest

from po_agent.harness.agent_core_v3 import AgentCoreV3ContractError, AgentCoreV3FailureCode
from po_agent.harness.agent_core_v3_registry import build_h1_task_registry
from po_agent.harness.agent_core_v3_typed_planner import TypedAgentLoopPlannerV3


def test_typed_call_shape_selects_capability_without_action_field() -> None:
    registry = build_h1_task_registry()
    decision = TypedAgentLoopPlannerV3._decode_candidate(
        {
            "call": {
                "capability_id": "task-lookup-v3",
                "constraints": {"task_key": "DMS-380"},
            },
            "final": None,
            "rationale": "lookup",
        },
        registry=registry,
    )
    assert decision is not None
    assert decision.action == "call_capability"
    assert decision.capability_id == "task-lookup-v3"
    assert decision.constraints == {"task_key": "DMS-380"}


def test_typed_final_shape_selects_final_without_action_field() -> None:
    registry = build_h1_task_registry()
    decision = TypedAgentLoopPlannerV3._decode_candidate(
        {
            "call": None,
            "final": {"answer": "Готово по данным источника."},
            "rationale": "complete",
        },
        registry=registry,
    )
    assert decision is not None
    assert decision.action == "final"
    assert decision.final_answer == "Готово по данным источника."


def test_both_null_is_not_an_executable_decision() -> None:
    registry = build_h1_task_registry()
    assert TypedAgentLoopPlannerV3._decode_candidate(
        {"call": None, "final": None, "rationale": None},
        registry=registry,
    ) is None


def test_both_selected_is_not_an_executable_decision() -> None:
    registry = build_h1_task_registry()
    assert TypedAgentLoopPlannerV3._decode_candidate(
        {
            "call": {"capability_id": "task-lookup-v3", "constraints": {"task_key": "DMS-380"}},
            "final": {"answer": "done"},
            "rationale": None,
        },
        registry=registry,
    ) is None


def test_typed_call_rejects_unsupported_constraint() -> None:
    registry = build_h1_task_registry()
    with pytest.raises(AgentCoreV3ContractError) as exc:
        TypedAgentLoopPlannerV3._decode_candidate(
            {
                "call": {
                    "capability_id": "task-lookup-v3",
                    "constraints": {"task_key": "DMS-380", "invented": "x"},
                },
                "final": None,
                "rationale": None,
            },
            registry=registry,
        )
    assert exc.value.code == AgentCoreV3FailureCode.UNSUPPORTED_CONSTRAINT
