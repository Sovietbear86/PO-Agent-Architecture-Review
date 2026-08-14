import pytest

from po_agent.harness import HarnessRequest, ResponseStatus, build_fake_runtime


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("query", "skill_id"),
    [
        ("Покажи очередь внимания", "po-attention-queue"),
        ("Сделай утреннюю сводку", "po-daily-brief"),
        ("Сделай статус-отчет", "po-status-report"),
        ("Подготовь напоминание по DMS-202", "po-reminder-draft"),
        ("Создай локальную задачу: проверить release notes", "po-local-task-draft"),
    ],
)
async def test_po_assistant_routes_are_executable(query, skill_id):
    response = await build_fake_runtime().process(HarnessRequest(query=query))
    assert response.status is ResponseStatus.COMPLETED
    assert response.skill_id == skill_id


@pytest.mark.asyncio
async def test_attention_queue_is_deterministically_ranked():
    response = await build_fake_runtime().process(HarnessRequest(query="Что требует моего внимания?"))
    assert response.data["scoring_version"] == "po_attention_v1"
    assert response.data["queue"]
    scores = [row["attention_score"] for row in response.data["queue"]]
    assert scores == sorted(scores, reverse=True)
    assert "DMS-202" in {row["task"]["key"] for row in response.data["queue"]}


@pytest.mark.asyncio
async def test_daily_brief_declares_deterministic_fallback():
    response = await build_fake_runtime().process(HarnessRequest(query="Сделай daily brief"))
    assert response.data["synthesis_mode"] == "deterministic_fallback"
    assert "llm_unavailable_deterministic_daily_brief" in response.warnings
    assert response.data["active"] >= response.data["blocked"]


@pytest.mark.asyncio
async def test_status_report_has_portfolio_completion_and_product_breakdown():
    response = await build_fake_runtime().process(HarnessRequest(query="Сделай status report"))
    assert response.data["total"] == 5
    assert response.data["completed"] == 2
    assert response.data["completion_percent"] == 40.0
    assert set(response.data["by_product"]) == {"WMB", "DMS"}
    assert "llm_unavailable_deterministic_status_report" in response.warnings


@pytest.mark.asyncio
async def test_reminder_is_draft_only_and_grounded_in_task():
    response = await build_fake_runtime().process(HarnessRequest(query="Составь напоминание по DMS-202"))
    assert response.skill_id == "po-reminder-draft"
    assert response.data["draft_created"] is True
    assert response.data["task"]["key"] == "DMS-202"
    assert response.data["write_performed"] is False
    assert response.data["requires_approval_for_send"] is True
    assert response.evidence
    assert "draft_only_no_external_write" in response.warnings


@pytest.mark.asyncio
async def test_local_task_draft_never_writes_external_system():
    response = await build_fake_runtime().process(HarnessRequest(query="Создай локальную задачу: проверить release notes"))
    assert response.skill_id == "po-local-task-draft"
    assert response.data["draft_created"] is True
    assert response.data["draft"]["title"] == "проверить release notes"
    assert response.data["draft"]["write_performed"] is False
    assert response.data["draft"]["requires_approval_for_external_write"] is True
    assert "draft_only_no_external_write" in response.warnings
