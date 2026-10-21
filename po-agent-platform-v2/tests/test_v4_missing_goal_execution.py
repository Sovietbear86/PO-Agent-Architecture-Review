"""A229M2.2B1 owner tests. Real AS21 parity is required independently in QA."""
import pytest

from po_agent.api.v1.missing_goal_execution import (
    _goal_query, run_bounded_missing_goals,
)
from po_agent.api.v1.goal_coverage import detect_goals


class _Result:
    def __init__(self, payload):
        self.payload = payload

    def to_dict(self):
        return self.payload


class _GovernedRuntime:
    def __init__(self, outcomes):
        self.outcomes = outcomes
        self.calls = []

    async def process(self, request):
        self.calls.append(request)
        return _Result(self.outcomes.pop(0))


def _obs(cap, args, *, key=None, answer="Подтверждено", source="REAL_AS21"):
    data = {"source": source}
    if key:
        data["task_key"] = key
    return {"capability_id": cap, "arguments": args, "answer": answer, "data": data}


def _response(*rows):
    return {
        "status": "COMPLETED", "answer": "Исходный непроверенный текст",
        "data": {"results": list(rows), "_agent_core_v4": {}},
        "warnings": [], "evidence": [],
    }


@pytest.mark.asyncio
async def test_missing_hierarchy_runs_once_and_renders_only_grounded_answers():
    query = "Покажи задачу DMS-267 и её иерархию"
    original = _response(_obs(
        "task.lookup", {"task_key": "DMS-267"},
        key="DMS-267", answer="Карточка DMS-267 подтверждена.",
    ))
    extra = _response(_obs(
        "task.hierarchy", {"task_key": "DMS-267"},
        key="DMS-267", answer="Родитель DMS-253.",
    ))
    runtime = _GovernedRuntime([extra])
    result = await run_bounded_missing_goals(runtime, original, query, "session")

    assert result.response["status"] == "COMPLETED"
    assert result.attempted == 1
    assert len(runtime.calls) == 1
    assert "иерархию" in runtime.calls[0].query
    assert "DMS-253" in result.response["answer"]
    assert "Карточка DMS-267" in result.response["answer"]
    assert "непроверенный текст" not in result.response["answer"]
    assert len(result.response["data"]["results"]) == 2


@pytest.mark.asyncio
async def test_three_goals_only_run_missing_and_never_exceed_two_extra_calls():
    query = "Покажи задачу DMS-267, её иерархию и задачи Калачанова в WMB"
    original = _response(_obs(
        "task.lookup", {"task_key": "DMS-267"}, key="DMS-267",
    ))
    runtime = _GovernedRuntime([
        _response(_obs("task.hierarchy", {"task_key": "DMS-267"},
                       key="DMS-267", answer="Родитель DMS-253")),
        _response(_obs("task.search_assignee",
                       {"reference": "Калачанов", "space": "WMB"},
                       answer="Найдено задач: 6")),
    ])
    result = await run_bounded_missing_goals(runtime, original, query, "session")
    assert result.response["status"] == "COMPLETED"
    assert result.attempted == 2
    assert len(runtime.calls) == 2
    assert all("Покажи задачу DMS-267" != call.query for call in runtime.calls)
    assert len(result.proven) == 3


@pytest.mark.asyncio
async def test_429_and_missing_source_do_not_ever_become_false_completed():
    query = "Покажи задачу DMS-267 и её иерархию"
    original = _response(_obs(
        "task.lookup", {"task_key": "DMS-267"}, key="DMS-267",
    ))
    runtime = _GovernedRuntime([{
        "status": "FAILED", "answer": None, "data": {},
        "warnings": ["v4_provider_rate_limit"],
    }])
    result = await run_bounded_missing_goals(runtime, original, query, "session")
    assert result.response["status"] == "PARTIAL"
    assert result.unresolved
    assert result.attempted == 1

    runtime = _GovernedRuntime([_response(_obs(
        "task.hierarchy", {"task_key": "DMS-267"},
        key="DMS-267", source="LOCAL",
    ))])
    result = await run_bounded_missing_goals(runtime, original, query, "session")
    assert result.response["status"] == "PARTIAL"


@pytest.mark.asyncio
async def test_composed_filters_and_comparison_are_not_split():
    original = _response()
    for query in (
        "Открытые задачи Семавина типа дефект в DMS за последние 2 дня",
        "Задачи в работе и с вложениями у Калачанова в WMB",
        "Сравни незавершённые задачи в DMS и OLP",
    ):
        runtime = _GovernedRuntime([])
        result = await run_bounded_missing_goals(runtime, original, query, "s")
        assert result.attempted == 0
        assert result.response == original
        assert runtime.calls == []


@pytest.mark.asyncio
async def test_prior_evidence_credit_only_and_never_injected_into_public_results():
    query = "Покажи задачу DMS-267 и её иерархию"
    prior = ({
        "step": 1, "capability_id": "task.lookup",
        "arguments": {"task_key": "DMS-267"},
        "answer": "Карточка DMS-267 подтверждена.",
        "data": {"source": "REAL_AS21", "task_key": "DMS-267"},
    },)
    current = _response()
    runtime = _GovernedRuntime([_response(_obs(
        "task.hierarchy", {"task_key": "DMS-267"},
        key="DMS-267", answer="Родитель DMS-253",
    ))])
    result = await run_bounded_missing_goals(
        runtime, current, query, "session", prior=prior,
    )
    assert result.response["status"] == "COMPLETED"
    assert len(runtime.calls) == 1
    assert len(result.response["data"]["results"]) == 1
    assert result.response["data"]["results"][0]["capability_id"] == "task.hierarchy"
    assert "Карточка DMS-267" in result.response["answer"]


@pytest.mark.asyncio
async def test_untrusted_prior_cannot_be_credited():
    query = "Покажи задачу DMS-267 и её иерархию"
    prior = ({
        "step": 1, "capability_id": "task.lookup",
        "arguments": {"task_key": "DMS-267"},
        "answer": "Invented",
        "data": {"source": "LOCAL", "task_key": "DMS-267"},
    },)
    runtime = _GovernedRuntime([_response(_obs(
        "task.hierarchy", {"task_key": "DMS-267"}, key="DMS-267",
    ))])
    result = await run_bounded_missing_goals(runtime, _response(), query, "s", prior=prior)
    assert result.response["status"] == "PARTIAL"
    assert "Invented" not in result.response["answer"]


def test_goal_query_is_typed_and_does_not_route_by_user_or_task_id():
    goals = detect_goals("Покажи задачу DMS-267 и её иерархию")
    assert all(_goal_query(goal) for goal in goals)
    assert set(_goal_query(goal) for goal in goals) == {
        "Покажи задачу DMS-267", "Покажи иерархию задачи DMS-267"
    }
