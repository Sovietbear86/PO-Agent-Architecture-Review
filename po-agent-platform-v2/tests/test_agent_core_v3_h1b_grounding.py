from po_agent.harness.agent_core_v3_h1b import AgentCoreV3H1BProcessor


def test_ground_reference_resolves_canonical_member_login() -> None:
    grounded = {"person_raw": "Гаранина", "member_login": "Garanin.R.V"}
    assert AgentCoreV3H1BProcessor._resolve_ground_reference(
        "$ground.member_login", grounded
    ) == "Garanin.R.V"


def test_ground_reference_does_not_accept_missing_value() -> None:
    from po_agent.harness.agent_core_v3 import AgentCoreV3ContractError

    try:
        AgentCoreV3H1BProcessor._resolve_ground_reference("$ground.member_login", {})
    except AgentCoreV3ContractError:
        return
    raise AssertionError("missing grounded value must fail closed")
