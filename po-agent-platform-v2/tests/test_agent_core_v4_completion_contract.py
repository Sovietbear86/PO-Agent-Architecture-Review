"""Assignment 187 — deterministic skill-completion contract tests.

These tests prove the generic post-observation completion mechanism required
by the A187 spec. All fixtures are synthetic (ALPHA-101, member.alpha, ...)
and deliberately contain no production person/space/sprint/task facts.

Properties under test (A187 Phase 1 list):
1. tasks.lookup_then_assignee completes after lookup + assignee-bound search;
2. it does NOT complete after lookup alone;
3. it does NOT complete after a search for the wrong/unbound assignee;
4. it does NOT complete when a resolved user constraint (space/sprint) is not
   represented in the downstream task.search observation;
5. single-step skills complete only after their required authoritative
   observation;
6. analytical skills are not auto-completed before their capability result
   exists;
7. invented/ambiguous/source-failure paths never auto-complete;
8. runtime-generated completion does not use a model READY and cannot
   fabricate an answer without observations;
9. existing action-only recovery safety remains intact;
10. no semantic-prepass or entity-specific routing appears in the mechanism.
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime
from typing import Any

import pytest

from po_agent.domain.models import StatusCategory, Task, TaskStatus
from po_agent.harness.agent_core_v4 import (
    AgentCoreV4Runtime,
    V4Observation,
)
from po_agent.harness.agent_core_v4_completion import (
    CompletionRequirement,
    SkillCompletionContract,
    is_skill_satisfied,
    resolved_constraint_values,
)
from po_agent.harness.agent_core_v4_robust import RobustReliableAgentCoreV4Runtime
from po_agent.harness.contracts import ResponseStatus
from po_agent.harness.entity_grounding import TeamDirectory, TeamDirectoryEntry
from po_agent.llm.client import LLMChoice, LLMMessage, LLMResponse

ALPHA_LOGIN = "member.alpha"
BETA_LOGIN = "member.beta"
FIXED_NOW = datetime(2026, 1, 1, 12, 0, 0)


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

def _obs(step: int, capability_id: str, arguments: dict[str, str] | None = None, data: dict[str, Any] | None = None) -> V4Observation:
    return V4Observation(
        step=step,
        capability_id=capability_id,
        arguments=dict(arguments or {}),
        answer=f"{capability_id} observation",
        data=dict(data or {}),
    )


def _lookup_found(task_key: str = "ALPHA-101", assignee_login: str = ALPHA_LOGIN) -> V4Observation:
    return _obs(
        1,
        "task.lookup",
        {"task_key": task_key},
        {
            "task_key": task_key,
            "task": {
                "key": task_key,
                "assignee_login": assignee_login,
                "assignee_id": assignee_login,
                "status": "In progress",
                "project_space": "DMS",
                "sprint_id": "DMS-SPRNT-9",
            },
            "assignee_login": assignee_login,
            "assignee_id": assignee_login,
            "source": "REAL_AS21",
            "capability": "task.lookup",
        },
    )


def _search(assignee: str | None = None, sprint_id: str | None = None, space: str | None = None, step: int = 2, count: int = 3) -> V4Observation:
    arguments: dict[str, str] = {}
    if assignee:
        arguments["assignee"] = assignee
    if sprint_id:
        arguments["sprint_id"] = sprint_id
    if space:
        arguments["space"] = space
    filters = {key: value for key, value in arguments.items()}
    return _obs(
        step,
        "task.search",
        arguments,
        {
            "count": count,
            "filters": filters,
            "task_keys_sample": [f"ALPHA-{100 + i}" for i in range(count)],
            "task_key_count": count,
            "source": "REAL_AS21",
            "capability": "task.search",
        },
    )


def _lookup_then_assignee_contract() -> SkillCompletionContract:
    return SkillCompletionContract(
        "tasks.lookup_then_assignee",
        (
            CompletionRequirement("task.lookup", data_keys=("task", "assignee_login")),
            CompletionRequirement(
                "task.search",
                data_keys=("count",),
                bound_argument=("assignee", "task.lookup", ("assignee_login", "task.assignee_login", "assignee_id", "task.assignee_id")),
                covers_resolved_constraints=True,
            ),
        ),
    )


def _tasks_search_contract() -> SkillCompletionContract:
    return SkillCompletionContract(
        "tasks.search",
        (
            CompletionRequirement("task.search", data_keys=("count",), covers_resolved_constraints=True),
        ),
    )


# --------------------------------------------------------------------------
# 1-4: lookup -> assignee -> search completion semantics
# --------------------------------------------------------------------------

def test_lookup_then_assignee_completes_after_lookup_and_bound_search() -> None:
    observations = [_lookup_found(), _search(assignee=ALPHA_LOGIN)]
    assert is_skill_satisfied(_lookup_then_assignee_contract(), observations)


def test_lookup_then_assignee_not_complete_after_lookup_alone() -> None:
    observations = [_lookup_found()]
    assert not is_skill_satisfied(_lookup_then_assignee_contract(), observations)


def test_lookup_then_assignee_not_complete_after_unbound_search() -> None:
    observations = [_lookup_found(assignee_login=ALPHA_LOGIN), _search(assignee=BETA_LOGIN)]
    assert not is_skill_satisfied(_lookup_then_assignee_contract(), observations)


def test_lookup_then_assignee_not_complete_when_resolved_constraint_missing() -> None:
    observations = [
        _lookup_found(),
        _obs(2, "space.resolve", {"reference": "DMS"}, {"space": "DMS", "product": "DMS", "source": "PO_AGENT_SCOPE", "capability": "space.resolve"}),
        # Downstream search drops the resolved space constraint.
        _search(assignee=ALPHA_LOGIN, step=3),
    ]
    assert not is_skill_satisfied(_lookup_then_assignee_contract(), observations)
    # Adding the constraint to the downstream search satisfies the contract.
    observations.append(_search(assignee=ALPHA_LOGIN, space="DMS", step=4))
    assert is_skill_satisfied(_lookup_then_assignee_contract(), observations)


def test_resolved_constraints_are_collected_from_typed_resolver_observations() -> None:
    observations = [
        _obs(1, "member.resolve", {"reference": "Альфа"}, {"member_login": ALPHA_LOGIN, "source": "REAL_AS21"}),
        _obs(2, "sprint.resolve", {"reference": "DMS-SPRNT-9"}, {"sprint_id": "DMS-SPRNT-9", "space": "DMS", "count": 7, "source": "REAL_AS21"}),
        _search(assignee=ALPHA_LOGIN, sprint_id="DMS-SPRNT-9", step=3),
    ]
    resolved = resolved_constraint_values(observations)
    assert ("assignee", ALPHA_LOGIN) in resolved
    assert ("sprint_id", "DMS-SPRNT-9") in resolved
    # The search covers both resolved constraints.
    assert is_skill_satisfied(_tasks_search_contract(), observations)
    # Dropping the sprint constraint from the search breaks satisfaction.
    incomplete = observations[:2] + [_search(assignee=ALPHA_LOGIN, step=3)]
    assert not is_skill_satisfied(_tasks_search_contract(), incomplete)


# --------------------------------------------------------------------------
# 5-6: single-step and analytical skills
# --------------------------------------------------------------------------

def test_single_step_skill_completes_only_after_its_authoritative_observation() -> None:
    contract = SkillCompletionContract("task.lookup", (CompletionRequirement("task.lookup", data_keys=("task",)),))
    assert not is_skill_satisfied(contract, [])
    assert not is_skill_satisfied(contract, [_search(assignee=ALPHA_LOGIN)])
    assert is_skill_satisfied(contract, [_lookup_found()])


def test_analytical_skill_not_completed_before_its_capability_result_exists() -> None:
    contract = SkillCompletionContract(
        "sprint.health",
        (CompletionRequirement("sprint.health", data_keys=("sprint_id", "total")),),
    )
    sprint_resolve = _obs(1, "sprint.resolve", {"reference": "DMS-SPRNT-9"}, {"sprint_id": "DMS-SPRNT-9", "space": "DMS", "count": 7, "source": "REAL_AS21"})
    assert not is_skill_satisfied(contract, [sprint_resolve])
    health = _obs(2, "sprint.health", {"sprint_id": "DMS-SPRNT-9"}, {"sprint_id": "DMS-SPRNT-9", "total": 7, "completed": 2, "active": 4, "blocked": 1, "completion_percent": 28.6})
    assert is_skill_satisfied(contract, [sprint_resolve, health])


def test_analytical_task_skill_requires_its_own_result_not_the_lookup() -> None:
    contract = SkillCompletionContract(
        "task.quality",
        (CompletionRequirement("task.quality", data_keys=("task_key",), data_absent_keys=("found",)),),
    )
    assert not is_skill_satisfied(contract, [_lookup_found()])
    quality_found = _obs(2, "task.quality", {"task_key": "ALPHA-101"}, {"task_key": "ALPHA-101", "score": 70, "quality_level": "good"})
    assert is_skill_satisfied(contract, [_lookup_found(), quality_found])
    quality_not_found = _obs(2, "task.quality", {"task_key": "ALPHA-101"}, {"task_key": "ALPHA-101", "found": False})
    assert not is_skill_satisfied(contract, [quality_not_found])


# --------------------------------------------------------------------------
# 7: failure paths never auto-complete
# --------------------------------------------------------------------------

def test_not_found_lookup_never_satisfies_completion() -> None:
    not_found = _obs(1, "task.lookup", {"task_key": "ALPHA-999"}, {"task_key": "ALPHA-999", "task": None, "source": "REAL_AS21"})
    assert not is_skill_satisfied(_lookup_then_assignee_contract(), [not_found])
    assert not is_skill_satisfied(_lookup_then_assignee_contract(), [not_found, _search(assignee=ALPHA_LOGIN, step=2)])


def test_missing_or_ambiguous_or_source_failure_paths_have_no_observations() -> None:
    # Source failures, clarifications and ambiguity raise before an observation
    # is appended, so the trajectory state simply has no such observation:
    # nothing can be auto-completed from an empty or partial typed state.
    assert not is_skill_satisfied(_lookup_then_assignee_contract(), [])
    assert not is_skill_satisfied(_tasks_search_contract(), [])
    # A current-sprint observation with an explicit not-found (null sprint_id)
    # must not be treated as a satisfied terminal observation.
    sprint_current_contract = SkillCompletionContract(
        "sprint.current",
        (CompletionRequirement("sprint.current", data_keys=("sprint_id",)),),
    )
    not_found_current = _obs(1, "sprint.current", {"product": "DMS"}, {"product": "DMS", "space": "DMS", "sprint_id": None, "source": "REAL_AS21"})
    assert not is_skill_satisfied(sprint_current_contract, [not_found_current])
    found_current = _obs(1, "sprint.current", {"product": "DMS"}, {"product": "DMS", "space": "DMS", "sprint_id": "DMS-SPRNT-9", "source": "REAL_AS21"})
    assert is_skill_satisfied(sprint_current_contract, [found_current])


# --------------------------------------------------------------------------
# 8: runtime-generated completion (process-level, scripted LLM)
# --------------------------------------------------------------------------

class ScriptedLLM:
    def __init__(self, outputs: list[str]) -> None:
        self.outputs = list(outputs)
        self.planner_calls = 0
        self.synthesis_calls = 0

    async def complete(self, messages, **kwargs):
        content = str(messages[0].content)
        if "concise Russian answer" in content:
            self.synthesis_calls += 1
            return LLMResponse(choices=[LLMChoice(message=LLMMessage(role="assistant", content="Детерминированный синтез по наблюдениям."))])
        self.planner_calls += 1
        if not self.outputs:
            raise AssertionError("planner was called again after the satisfaction boundary")
        raw = self.outputs.pop(0)
        return LLMResponse(choices=[LLMChoice(message=LLMMessage(role="assistant", content=raw))])


class FakeV4Adapter:
    def __init__(self, tasks_by_key: dict[str, Task] | None = None, search_results: dict[str, list[Task]] | None = None) -> None:
        self.tasks_by_key = {key.upper(): task for key, task in (tasks_by_key or {}).items()}
        self.search_results = dict(search_results or {})
        self.current_sprints: dict[str, str | None] = {}

    async def get_task(self, task_key: str) -> Task | None:
        return self.tasks_by_key.get(str(task_key or "").upper())

    async def search_tasks(self, query: str, **kwargs) -> list[Task]:
        return list(self.search_results.get(str(query or "").strip(), []))

    async def get_sprint_tasks(self, sprint_id: str, space: str | None = None) -> list[Task]:
        return []

    async def get_current_sprint_id(self, product: str) -> str | None:
        return self.current_sprints.get(str(product or "").upper())

    async def get_release_tasks(self, release_id: str, space: str | None = None) -> list[Task]:
        return []


def _task(key: str, assignee_login: str | None = ALPHA_LOGIN, space: str = "DMS", sprint_id: str | None = "DMS-SPRNT-9") -> Task:
    return Task(
        key=key,
        id=key,
        title=f"Synthetic task {key}",
        description="synthetic description",
        status=TaskStatus.IN_PROGRESS,
        status_category=StatusCategory.ACTIVE_WORK,
        status_type="progress",
        assignee=assignee_login,
        assignee_id=assignee_login,
        assignee_login=assignee_login,
        created_at=FIXED_NOW,
        updated_at=FIXED_NOW,
        project_space=space,
        sprint_id=sprint_id,
    )


def _team() -> TeamDirectory:
    return TeamDirectory(
        (
            TeamDirectoryEntry(login=ALPHA_LOGIN, full_name="Альфа А. Альфова", products=("DMS",)),
            TeamDirectoryEntry(login=BETA_LOGIN, full_name="Бета Б. Бетова", products=("DMS",)),
        )
    )


def _robust_runtime(adapter: FakeV4Adapter, llm: ScriptedLLM) -> RobustReliableAgentCoreV4Runtime:
    return RobustReliableAgentCoreV4Runtime(
        adapter,
        llm=llm,
        model="test-model",
        team=_team(),
        legacy_capabilities=None,
        max_steps=8,
    )


def _decision(kind: str, **payload: Any) -> str:
    import json

    body: dict[str, Any] = {"load_skill": None, "call": None, "ready": None, "rationale": "scripted"}
    body[kind] = payload
    return json.dumps(body, ensure_ascii=False)


def _run(runtime, query: str):
    from po_agent.harness.contracts import HarnessRequest

    return asyncio.run(runtime.process(HarnessRequest(query=query, session_id="completion-test")))


def test_runtime_completes_lookup_then_assignee_without_model_ready() -> None:
    lookup_task = _task("ALPHA-101", ALPHA_LOGIN)
    assignee_tasks = [_task(f"ALPHA-{101 + i}", ALPHA_LOGIN) for i in range(3)]
    adapter = FakeV4Adapter(
        tasks_by_key={"ALPHA-101": lookup_task},
        search_results={f'assignee = "{ALPHA_LOGIN}"': assignee_tasks},
    )
    llm = ScriptedLLM([
        _decision("load_skill", skill_id="tasks.lookup_then_assignee"),
        _decision("call", capability_id="task.lookup", arguments={"task_key": "ALPHA-101"}),
        _decision("call", capability_id="task.search", arguments={"assignee": ALPHA_LOGIN}),
        # No fourth planner output: if the runtime asks the model for a terminal
        # READY, the scripted client raises — proving the completion boundary.
    ])
    runtime = _robust_runtime(adapter, llm)
    response = _run(runtime, "Покажи ALPHA-101 и затем задачи его исполнителя")

    assert response.status is ResponseStatus.COMPLETED
    meta = response.data["_agent_core_v4"]
    assert meta["completion"] == "runtime_contract"
    assert meta["semantic_prepass_used"] is False
    assert llm.planner_calls == 3
    # The synthesizer saw only validated observations; the final answer exists.
    assert llm.synthesis_calls == 1
    assert response.answer
    keys = {row["key"] for row in response.data["results"][-1]["data"]["tasks"]}
    assert keys == {task.key for task in assignee_tasks}


def test_runtime_completion_cannot_fabricate_without_observations() -> None:
    adapter = FakeV4Adapter()
    llm = ScriptedLLM([
        _decision("load_skill", skill_id="tasks.lookup_then_assignee"),
        _decision("ready", answer="Задач нет, источник пуст."),
    ])
    runtime = _robust_runtime(adapter, llm)
    response = _run(runtime, "Покажи ALPHA-101 и затем задачи его исполнителя")

    # READY with zero observations stays the existing clarification behavior —
    # the runtime contract must never mint a completed answer from nothing.
    assert response.status is ResponseStatus.NEEDS_CLARIFICATION
    assert response.data["_agent_core_v4"].get("completion") != "runtime_contract"
    assert llm.planner_calls == 2


def test_unsatisfied_contract_fails_closed_when_planner_dies() -> None:
    # Only the lookup happens (task not found), then the model endpoint degrades
    # (A186 signature): the contract is NOT satisfied, so the runtime must fail
    # closed rather than synthesize a fabricated completion.
    adapter = FakeV4Adapter(tasks_by_key={})
    llm = ScriptedLLM([
        _decision("load_skill", skill_id="tasks.lookup_then_assignee"),
        _decision("call", capability_id="task.lookup", arguments={"task_key": "ALPHA-999"}),
        "the model derails into an undecodable essay",
        "still undecodable",
        "still undecodable",
        "still undecodable",
    ])
    runtime = _robust_runtime(adapter, llm)
    response = _run(runtime, "Покажи ALPHA-999 и затем задачи его исполнителя")

    assert response.status is ResponseStatus.FAILED
    assert "v4_runtime_failure" in response.warnings
    assert response.data["_agent_core_v4"].get("completion") != "runtime_contract"


def test_premature_model_ready_is_rejected_until_contract_is_satisfied() -> None:
    # A planner READY after lookup alone must not bypass the declared
    # lookup->assignee-search completion contract. The runtime rejects the
    # premature READY, gives the planner another bounded turn, and completes
    # only after the required source-backed search observation exists.
    lookup_task = _task("ALPHA-101", ALPHA_LOGIN)
    assignee_tasks = [_task("ALPHA-201", ALPHA_LOGIN)]
    adapter = FakeV4Adapter(
        tasks_by_key={"ALPHA-101": lookup_task},
        search_results={f'assignee = "{ALPHA_LOGIN}"': assignee_tasks},
    )
    llm = ScriptedLLM([
        _decision("load_skill", skill_id="tasks.lookup_then_assignee"),
        _decision("call", capability_id="task.lookup", arguments={"task_key": "ALPHA-101"}),
        _decision("ready", answer="ALPHA-101 показана; остальное не нужно."),
        _decision("call", capability_id="task.search", arguments={"assignee": ALPHA_LOGIN}),
    ])
    runtime = _robust_runtime(adapter, llm)
    response = _run(runtime, "Покажи ALPHA-101 и затем задачи его исполнителя")

    assert response.status is ResponseStatus.COMPLETED
    assert response.data["_agent_core_v4"]["completion"] == "runtime_contract"
    assert llm.planner_calls == 4
    rejected = [
        entry for entry in response.data["_agent_core_v4"]["trajectory"]
        if entry.get("ready_rejected") == "unsatisfied_completion_contract"
    ]
    assert rejected


def test_zero_row_search_is_a_legitimate_source_completion() -> None:
    # A person with zero tasks is a source-true answer, not a failure.
    adapter = FakeV4Adapter(search_results={f'assignee = "{BETA_LOGIN}"': []})
    llm = ScriptedLLM([
        _decision("load_skill", skill_id="tasks.search"),
        _decision("call", capability_id="member.resolve", arguments={"reference": "Бета"}),
        _decision("call", capability_id="task.search", arguments={"assignee": BETA_LOGIN}),
    ])
    runtime = _robust_runtime(adapter, llm)
    response = _run(runtime, "Задачи Беты")

    assert response.status is ResponseStatus.COMPLETED
    assert response.data["_agent_core_v4"]["completion"] == "runtime_contract"
    search_data = response.data["results"][-1]["data"]
    assert search_data["count"] == 0
    assert llm.planner_calls == 3


def test_person_collection_completes_at_search_with_exact_keys() -> None:
    person_tasks = [_task(f"ALPHA-{201 + i}", ALPHA_LOGIN) for i in range(4)]
    adapter = FakeV4Adapter(search_results={f'assignee = "{ALPHA_LOGIN}"': person_tasks})
    llm = ScriptedLLM([
        _decision("load_skill", skill_id="tasks.search"),
        _decision("call", capability_id="member.resolve", arguments={"reference": "Альфа"}),
        _decision("call", capability_id="task.search", arguments={"assignee": ALPHA_LOGIN}),
    ])
    runtime = _robust_runtime(adapter, llm)
    response = _run(runtime, "Задачи Альфы")

    assert response.status is ResponseStatus.COMPLETED
    assert response.data["_agent_core_v4"]["completion"] == "runtime_contract"
    keys = {row["key"] for row in response.data["results"][-1]["data"]["tasks"]}
    assert keys == {task.key for task in person_tasks}
    assert llm.planner_calls == 3


def test_missing_resolved_constraint_is_injected_before_terminal_call() -> None:
    # The planner omits the already-resolved space on task.search. The runtime
    # deterministically fills the unique typed constraint because task.search
    # explicitly accepts a space argument. No extra stochastic repair turn is
    # required.
    person_tasks = [_task(f"ALPHA-{301 + i}", ALPHA_LOGIN, space="DMS") for i in range(2)]
    adapter = FakeV4Adapter(
        search_results={
            f'assignee = "{ALPHA_LOGIN}" AND project = "DMS"': person_tasks,
        }
    )
    llm = ScriptedLLM([
        _decision("load_skill", skill_id="tasks.search"),
        _decision("call", capability_id="space.resolve", arguments={"reference": "DMS"}),
        _decision("call", capability_id="member.resolve", arguments={"reference": "Альфа"}),
        _decision("call", capability_id="task.search", arguments={"assignee": ALPHA_LOGIN}),
    ])
    runtime = _robust_runtime(adapter, llm)
    response = _run(runtime, "Открытые задачи Альфы в DMS")

    assert response.status is ResponseStatus.COMPLETED
    assert response.data["_agent_core_v4"]["completion"] == "runtime_contract"
    assert llm.planner_calls == 4
    last_result = response.data["results"][-1]
    assert last_result["arguments"]["space"] == "DMS"
    last_search = last_result["data"]
    assert last_search["count"] == 2
    assert last_search["filters"]["space"] == "DMS"


# --------------------------------------------------------------------------
# 9: action-only recovery safety remains intact
# --------------------------------------------------------------------------

def test_recovery_ready_still_forbidden_by_planner_protocol() -> None:
    # The completion mechanism must not weaken the A181 action-only invariant:
    # a repair turn can never mint a terminal READY.
    from po_agent.harness.agent_core_v4_robust import RobustSkillNativePlannerV4
    from po_agent.harness.agent_core_v4 import SkillCatalogV4, SkillSpecV4, CapabilitySpecV4, V4ContractError

    catalog = SkillCatalogV4(
        (SkillSpecV4("task-search", "Search tasks", ("Search tasks",), ("task.search",)),),
        {"task.search": CapabilitySpecV4("task.search", "Search tasks", {"assignee": "optional"})},
    )
    planner = RobustSkillNativePlannerV4(
        ScriptedLLM(["garbage", "READY fabricated answer", "READY fabricated again", "READY fabricated third"]),
        model="test",
    )
    with pytest.raises(V4ContractError):
        asyncio.run(
            planner.next_decision(
                user_query="Задачи Альфы",
                catalog=catalog,
                loaded_skills=("task-search",),
                observations=[_search(assignee=ALPHA_LOGIN)],
            )
        )


# --------------------------------------------------------------------------
# 10: no semantic prepass / no entity-specific routing in the mechanism
# --------------------------------------------------------------------------

def test_completion_mechanism_is_generic_and_entity_free() -> None:
    module_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "src", "po_agent", "harness", "agent_core_v4_completion.py",
    )
    source = open(module_path, encoding="utf-8").read()
    # No production entity facts, surnames, spaces, sprints or task keys.
    for literal in ("Гаранин", "Калачанов", "Семавин", "Моисеев", "Иванов", "Гончаров",
                    "DMS-380", "DMS-99", "semavin", "DMS-SPRNT", "OLP-SPRNT", "WMB-29909"):
        assert literal not in source, f"entity-specific literal leaked into completion module: {literal}"
    # The constraint-resolver map is capability/field-structural only.
    contract = _lookup_then_assignee_contract()
    for requirement in contract.requirements:
        assert requirement.capability_id.startswith(("task.", "member.", "sprint.", "space.", "release."))


def test_runtime_contract_completion_marker_and_prepass_flag() -> None:
    adapter = FakeV4Adapter(tasks_by_key={"ALPHA-101": _task("ALPHA-101", ALPHA_LOGIN)})
    llm = ScriptedLLM([
        _decision("load_skill", skill_id="task.lookup"),
        _decision("call", capability_id="task.lookup", arguments={"task_key": "ALPHA-101"}),
    ])
    runtime = _robust_runtime(adapter, llm)
    response = _run(runtime, "Покажи ALPHA-101")

    assert response.status is ResponseStatus.COMPLETED
    meta = response.data["_agent_core_v4"]
    assert meta["completion"] == "runtime_contract"
    assert meta["semantic_prepass_used"] is False
    assert meta["progressive_skill_loading"] is True
    # The trajectory records that the terminal decision was runtime-generated,
    # not model-emitted.
    terminal = [entry for entry in meta["trajectory"] if entry.get("decision") == "ready"]
    assert terminal and terminal[-1].get("completion") == "runtime_contract"