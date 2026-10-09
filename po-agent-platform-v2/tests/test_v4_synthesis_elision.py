from __future__ import annotations

import pytest

from po_agent.harness.agent_core_v4 import V4Observation
from po_agent.harness.v4_synthesis_elision import TerminalSynthesisElider


class _UnderlyingSynthesizer:
    def __init__(self) -> None:
        self.calls = 0

    async def synthesize(self, user_query, observations):
        self.calls += 1
        return "LLM synthesis"


def _obs(step: int, capability_id: str, *, answer: str, data: dict) -> V4Observation:
    return V4Observation(
        step=step,
        capability_id=capability_id,
        arguments={},
        answer=answer,
        data=data,
    )


@pytest.mark.asyncio
async def test_elides_simple_task_collection_after_resolver():
    underlying = _UnderlyingSynthesizer()
    elider = TerminalSynthesisElider(underlying)
    observations = [
        _obs(
            1,
            "space.resolve",
            answer="Пространство подтверждено: WMB.",
            data={"space": "WMB"},
        ),
        _obs(
            2,
            "task.search_assignee",
            answer="Найдено задач: 2.",
            data={"count": 2, "task_keys": ["WMB-1", "WMB-2"], "source": "REAL_AS21"},
        ),
    ]

    answer = await elider.synthesize("Задачи Калачанова в WMB", observations)

    assert answer == "Найдено задач: 2.\nКлючи: WMB-1, WMB-2"
    assert underlying.calls == 0


@pytest.mark.asyncio
async def test_elides_task_type_analysis_using_grounded_capability_answer():
    underlying = _UnderlyingSynthesizer()
    elider = TerminalSynthesisElider(underlying)
    observations = [
        _obs(
            1,
            "task.type_analysis",
            answer="Найдено задач типа «Дефект»: 1.",
            data={
                "count": 1,
                "task_keys": ["DMS-431"],
                "type_breakdown": [{"code": "bug", "name": "Дефект", "count": 1}],
                "source": "REAL_AS21",
            },
        )
    ]

    answer = await elider.synthesize("Открытые дефекты", observations)

    assert answer == "Найдено задач типа «Дефект»: 1."
    assert underlying.calls == 0


@pytest.mark.asyncio
async def test_elides_lookup_and_hierarchy_answers():
    underlying = _UnderlyingSynthesizer()
    elider = TerminalSynthesisElider(underlying)

    lookup = await elider.synthesize(
        "DMS-267",
        [_obs(1, "task.lookup", answer="DMS-267: Тестовая задача — В работе.", data={"task_key": "DMS-267"})],
    )
    hierarchy = await elider.synthesize(
        "Покажи иерархию DMS-267",
        [_obs(
            1,
            "task.hierarchy",
            answer="Для DMS-267: уровней родителей — 2. Эпик: DMS-349.",
            data={"task_key": "DMS-267", "depth": 2, "epic_key": "DMS-349"},
        )],
    )

    assert lookup == "DMS-267: Тестовая задача — В работе."
    assert hierarchy == "Для DMS-267: уровней родителей — 2. Эпик: DMS-349."
    assert underlying.calls == 0


@pytest.mark.asyncio
async def test_delegates_multi_terminal_trajectory():
    underlying = _UnderlyingSynthesizer()
    elider = TerminalSynthesisElider(underlying)
    observations = [
        _obs(1, "task.search", answer="Найдено задач: 2.", data={"count": 2}),
        _obs(2, "task.hierarchy", answer="Иерархия построена.", data={"depth": 2}),
    ]

    answer = await elider.synthesize("Сделай два разных анализа", observations)

    assert answer == "LLM synthesis"
    assert underlying.calls == 1


@pytest.mark.asyncio
async def test_delegates_unknown_non_resolver_observation():
    underlying = _UnderlyingSynthesizer()
    elider = TerminalSynthesisElider(underlying)
    observations = [
        _obs(1, "sprint.health", answer="Спринт стабилен.", data={"health": "green"}),
        _obs(2, "task.search", answer="Найдено задач: 1.", data={"count": 1}),
    ]

    answer = await elider.synthesize("Спринт и задачи", observations)

    assert answer == "LLM synthesis"
    assert underlying.calls == 1


@pytest.mark.asyncio
async def test_delegates_when_terminal_answer_is_empty():
    underlying = _UnderlyingSynthesizer()
    elider = TerminalSynthesisElider(underlying)
    observations = [
        _obs(1, "task.search", answer="", data={"count": 1, "task_keys": ["DMS-1"]}),
    ]

    answer = await elider.synthesize("задачи", observations)

    assert answer == "LLM synthesis"
    assert underlying.calls == 1
