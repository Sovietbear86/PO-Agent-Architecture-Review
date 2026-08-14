import pytest

from po_agent.harness import HarnessRequest, ResponseStatus, build_fake_runtime


@pytest.mark.asyncio
async def test_acceptance_analysis_is_deterministic_and_grounded():
    response = await build_fake_runtime().process(
        HarnessRequest(query="Проверь критерии приемки WMB-102")
    )
    assert response.status is ResponseStatus.COMPLETED
    assert response.skill_id == "task-acceptance-analysis"
    assert 0 <= response.data["score"] <= 100
    assert response.data["task_key"] == "WMB-102"
    assert response.data["gaps"]
    assert response.evidence


@pytest.mark.asyncio
async def test_dependency_analysis_returns_explicit_empty_graph_when_none_exist():
    response = await build_fake_runtime().process(
        HarnessRequest(query="Покажи зависимости WMB-102")
    )
    assert response.status is ResponseStatus.COMPLETED
    assert response.skill_id == "task-dependency-analysis"
    assert response.data["dependencies"] == []
    assert response.data["unresolved_count"] == 0
    assert response.evidence


@pytest.mark.asyncio
async def test_blocker_analysis_uses_status_evidence_not_llm_guessing():
    response = await build_fake_runtime().process(
        HarnessRequest(query="Какие блокеры у DMS-202?")
    )
    assert response.status is ResponseStatus.COMPLETED
    assert response.skill_id == "task-blocker-analysis"
    assert response.data["blocked"] is True
    assert "ожидание информации" in " ".join(response.data["reasons"]).casefold()
    assert any(item.type == "blocker" for item in response.evidence)


@pytest.mark.asyncio
async def test_similar_task_search_exposes_method_and_bounded_results():
    response = await build_fake_runtime().process(
        HarnessRequest(query="Найди похожие задачи для WMB-101")
    )
    assert response.status is ResponseStatus.COMPLETED
    assert response.skill_id == "task-similar"
    assert response.data["method"] == "token_jaccard_v1"
    assert len(response.data["matches"]) <= 5
    assert all(0 < item["similarity"] <= 1 for item in response.data["matches"])
