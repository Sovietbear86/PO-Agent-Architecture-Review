from __future__ import annotations

import inspect

from po_agent.harness.agent_core_v4 import SkillNativePlannerV4
from po_agent.harness.agent_core_v4_robust import RobustSkillNativePlannerV4


def test_robust_planner_next_decision_signature_matches_base_keyword_contract():
    base = inspect.signature(SkillNativePlannerV4.next_decision)
    robust = inspect.signature(RobustSkillNativePlannerV4.next_decision)

    base_params = {
        name: param.kind
        for name, param in base.parameters.items()
        if name != "self"
    }
    robust_params = {
        name: param.kind
        for name, param in robust.parameters.items()
        if name != "self"
    }

    assert robust_params == base_params
    assert "session_context" in robust_params
    assert "runtime_guidance" in robust_params
