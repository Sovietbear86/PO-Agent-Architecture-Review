from __future__ import annotations

import pytest

from po_agent.harness.agent_core_v3 import (
    AcceptedTurnContract,
    AgentCoreV3ContractError,
    AgentCoreV3FailureCode,
    CapabilityContractV3,
    ResultPostconditionValidator,
    SOURCE_AUTHORITY_REAL_AS21,
    guard_constraint_preservation,
)


def test_accepted_turn_contract_is_immutable_and_rejects_constraint_loss():
    source = {"assignee": "Kalachanov.V.V", "space": "WMB"}
    contract = AcceptedTurnContract(
        turn_id="turn-1",
        intent="task_search",
        constraints=source,
        requested_constraints=frozenset({"assignee", "space"}),
    )
    source["space"] = "DMS"
    assert contract.constraints["space"] == "WMB"
    with pytest.raises(TypeError):
        contract.constraints["space"] = "DMS"  # type: ignore[index]

    with pytest.raises(AgentCoreV3ContractError) as exc:
        AcceptedTurnContract(
            turn_id="turn-2",
            intent="task_search",
            constraints={"assignee": "Kalachanov.V.V"},
            requested_constraints=frozenset({"assignee", "space"}),
        )
    assert exc.value.code is AgentCoreV3FailureCode.CONSTRAINT_LOSS


def test_capability_contract_rejects_unsupported_requested_constraint():
    turn = AcceptedTurnContract(
        turn_id="turn-3",
        intent="task_search",
        constraints={"assignee": "Kalachanov.V.V", "space": "WMB"},
        requested_constraints=frozenset({"assignee", "space"}),
    )
    capability = CapabilityContractV3(
        id="task-search-assignee",
        version="1",
        supported_constraints=frozenset({"assignee"}),
        source_authority=SOURCE_AUTHORITY_REAL_AS21,
        executor_id="task_search_executor",
    )
    with pytest.raises(AgentCoreV3ContractError) as exc:
        capability.validate_turn(turn)
    assert exc.value.code is AgentCoreV3FailureCode.UNSUPPORTED_CONSTRAINT


def test_constraint_guard_detects_executor_slot_loss():
    with pytest.raises(AgentCoreV3ContractError) as exc:
        guard_constraint_preservation(
            {"assignee", "space"},
            {"assignee": "Kalachanov.V.V", "space": "WMB"},
            {"assignee", "space"},
            {"assignee": "Kalachanov.V.V"},
        )
    assert exc.value.code is AgentCoreV3FailureCode.CONSTRAINT_LOSS


def test_result_validator_blocks_wrong_space_before_rendering():
    contract = AcceptedTurnContract(
        turn_id="turn-4",
        intent="task_search",
        constraints={"assignee": "Kalachanov.V.V", "space": "WMB"},
        requested_constraints=frozenset({"assignee", "space"}),
    )
    data = {
        "tasks": [
            {
                "key": "DMS-243",
                "assignee_login": "Kalachanov.V.V",
                "source_data": {"swtr_space": "DMS"},
            }
        ]
    }
    with pytest.raises(AgentCoreV3ContractError) as exc:
        ResultPostconditionValidator().validate(contract, data)
    assert exc.value.code is AgentCoreV3FailureCode.RESULT_CONTRACT_VIOLATION
    assert exc.value.details["failures"][0]["field"] == "space"


def test_result_validator_accepts_matching_pilot_rows():
    contract = AcceptedTurnContract(
        turn_id="turn-5",
        intent="task_search",
        constraints={"assignee": "Kalachanov.V.V", "space": "WMB"},
        requested_constraints=frozenset({"assignee", "space"}),
    )
    data = {
        "tasks": [
            {
                "key": "WMB-1",
                "assignee_login": "Kalachanov.V.V",
                "source_data": {"swtr_space": "WMB"},
            }
        ]
    }
    result = ResultPostconditionValidator().validate(contract, data)
    assert result.passed is True
    assert len(result.checks) == 2
