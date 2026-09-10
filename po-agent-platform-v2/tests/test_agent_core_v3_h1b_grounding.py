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


def test_assignee_literal_equal_to_grounded_member_login_is_source_safe() -> None:
    grounded = {
        "person_raw": "Гаранин Родион Владимирович",
        "member_login": "Garanin.R.V",
        "assignee": "Garanin.R.V",
    }
    assert AgentCoreV3H1BProcessor._literal_matches_grounded(
        "assignee", "Garanin.R.V", grounded
    ) == "Garanin.R.V"


def test_grounded_literal_match_is_not_fuzzy() -> None:
    grounded = {"member_login": "Garanin.R.V", "assignee": "Garanin.R.V"}
    assert AgentCoreV3H1BProcessor._literal_matches_grounded(
        "assignee", "Garanin", grounded
    ) is None


def test_non_assignee_literal_must_match_same_grounded_field() -> None:
    grounded = {"space": "DMS", "member_login": "Garanin.R.V"}
    assert AgentCoreV3H1BProcessor._literal_matches_grounded("space", "DMS", grounded) == "DMS"
    assert AgentCoreV3H1BProcessor._literal_matches_grounded("space", "Garanin.R.V", grounded) is None
