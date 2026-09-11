from __future__ import annotations

import asyncio
from types import SimpleNamespace

from po_agent.harness.agent_core_v4 import CapabilitySpecV4, SkillCatalogV4, SkillSpecV4
from po_agent.harness.agent_core_v4_robust import RobustSkillNativePlannerV4


class StubClient:
    def __init__(self, *responses: str) -> None:
        self._responses = iter(responses)

    async def complete(self, *_args, **_kwargs):
        content = next(self._responses)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
        )


def _catalog() -> SkillCatalogV4:
    capabilities = {
        "task.search": CapabilitySpecV4(
            "task.search",
            "Search tasks",
            {"assignee": "optional", "status": "optional"},
        )
    }
    return SkillCatalogV4(
        (
            SkillSpecV4(
                "task-search",
                "Search tasks",
                ("Resolve source-backed constraints", "Search tasks"),
                ("task.search",),
            ),
        ),
        capabilities,
    )


def test_dsl_load_decodes() -> None:
    decision = RobustSkillNativePlannerV4._decode_dsl("LOAD task-search")
    assert decision is not None
    assert decision.kind == "load_skill"
    assert decision.skill_id == "task-search"


def test_dsl_call_decodes_observation_reference() -> None:
    decision = RobustSkillNativePlannerV4._decode_dsl(
        "CALL task.search assignee=$obs.1.assignee_login status=not_completed"
    )
    assert decision is not None
    assert decision.kind == "call"
    assert decision.capability_id == "task.search"
    assert decision.arguments == {
        "assignee": "$obs.1.assignee_login",
        "status": "not_completed",
    }


def test_dsl_call_supports_quoted_multiword_value() -> None:
    decision = RobustSkillNativePlannerV4._decode_dsl(
        'CALL task.search assignee="Semavin.M.M" status="not completed"'
    )
    assert decision is not None
    assert decision.arguments == {
        "assignee": "Semavin.M.M",
        "status": "not completed",
    }


def test_dsl_rejects_multiple_decisions() -> None:
    assert RobustSkillNativePlannerV4._decode_dsl(
        "LOAD task-search\nCALL task.search status=not_completed"
    ) is None


def test_dsl_ready_decodes() -> None:
    decision = RobustSkillNativePlannerV4._decode_dsl("READY Данных достаточно для ответа")
    assert decision is not None
    assert decision.kind == "ready"
    assert decision.answer == "Данных достаточно для ответа"


def test_planner_recovers_from_malformed_json_to_dsl() -> None:
    planner = RobustSkillNativePlannerV4(
        StubClient(
            '{"load_skill":{"skill_id":"task-search"',
            "LOAD task-search",
        ),
        model="test",
    )
    decision = asyncio.run(
        planner.next_decision(
            user_query="Задачи исполнителя",
            catalog=_catalog(),
            loaded_skills=(),
            observations=[],
        )
    )
    assert decision.kind == "load_skill"
    assert decision.skill_id == "task-search"


def test_planner_recovers_second_step_call_without_trajectory_hardcode() -> None:
    planner = RobustSkillNativePlannerV4(
        StubClient(
            '{"call":{"capability_id":"task.search","arguments":{"assignee":',
            "CALL task.search assignee=$obs.1.assignee_login status=not_completed",
        ),
        model="test",
    )
    decision = asyncio.run(
        planner.next_decision(
            user_query="Покажи задачу и затем задачи её исполнителя",
            catalog=_catalog(),
            loaded_skills=("task-search",),
            observations=[],
        )
    )
    assert decision.kind == "call"
    assert decision.capability_id == "task.search"
    assert decision.arguments == {
        "assignee": "$obs.1.assignee_login",
        "status": "not_completed",
    }
