import pytest

from po_agent.harness import HarnessRequest, ResponseStatus, build_fake_runtime


@pytest.mark.asyncio
async def test_task_summary_returns_master_spec_structure_without_hallucinating():
    response = await build_fake_runtime().process(
        HarnessRequest(query="Суммаризируй WMB-102: что нужно сделать?")
    )
    assert response.status is ResponseStatus.COMPLETED
    assert response.skill_id == "task-summary"
    assert set(response.data) >= {
        "goal",
        "what_to_do",
        "acceptance_expectations",
        "dependencies",
        "open_questions",
    }
    assert "mobile devices" in response.data["what_to_do"]
    assert response.data["acceptance_expectations"] == []
    assert "llm_unavailable_deterministic_summary" in response.warnings
    assert response.evidence


@pytest.mark.asyncio
async def test_task_quality_score_is_deterministic_and_rule_evidenced():
    runtime = build_fake_runtime()
    first = await runtime.process(HarnessRequest(query="Оцени постановку задачи WMB-102"))
    second = await runtime.process(HarnessRequest(query="Оцени постановку задачи WMB-102"))

    assert first.skill_id == "task-quality"
    assert first.data["score"] == second.data["score"]
    assert 0 <= first.data["score"] <= 100
    assert first.data["rules"]
    assert any(item.type == "quality_rule" for item in first.evidence)


@pytest.mark.asyncio
async def test_missing_requirements_reuses_same_quality_rules():
    response = await build_fake_runtime().process(
        HarnessRequest(query="Чего не хватает в задаче WMB-103?")
    )
    assert response.skill_id == "task-missing-requirements"
    assert response.data["missing_elements"]
    assert response.data["quality_score"] < 100
    assert response.data["recommendations"]


@pytest.mark.asyncio
async def test_task_history_returns_source_transitions():
    response = await build_fake_runtime().process(
        HarnessRequest(query="Покажи историю переходов WMB-101")
    )
    assert response.skill_id == "task-history"
    assert len(response.data["timeline"]) == 2
    assert response.data["timeline"][0]["to"] == "In progress"
    assert all(item.type == "status_transition" for item in response.evidence)


@pytest.mark.asyncio
async def test_time_in_status_is_calculated_from_history():
    response = await build_fake_runtime().process(
        HarnessRequest(query="Сколько времени в статусах у WMB-101?")
    )
    assert response.skill_id == "task-time-in-status"
    assert response.data["durations"]
    assert all(item["hours"] >= 0 for item in response.data["durations"])


@pytest.mark.asyncio
async def test_aging_returns_only_open_non_cancelled_tasks_above_threshold():
    response = await build_fake_runtime().process(
        HarnessRequest(query="Покажи старые задачи старше 7 дней")
    )
    assert response.skill_id == "task-aging"
    assert response.data["threshold_days"] == 7
    assert response.data["tasks"]
    assert all(item["age_days"] >= 7 for item in response.data["tasks"])
    assert "WMB-101" not in {item["key"] for item in response.data["tasks"]}  # completed
    assert "DMS-201" not in {item["key"] for item in response.data["tasks"]}  # completed
