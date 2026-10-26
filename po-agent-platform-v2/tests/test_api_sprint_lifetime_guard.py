"""A230R3.3-R3: guard explicit sprint lifetime intent after bounded LLM failure."""
from po_agent.api.v1 import _guard_lifetime_sprint_scope


def _v4(status="NEEDS_CLARIFICATION"):
    return {
        "status": status, "answer": "147.5h за всё время",
        "question": "Уточните статус, исполнителя, тип задачи",
        "data": {"results": [{"capability_id": "sprint.time_spent",
                             "data": {"source": "REAL_AS21", "complete": True,
                                      "scope": "sprint_period_worklogs",
                                      "total_hours": 147.5}}],
                 "total_hours": 147.5, "worklog_count": 20},
        "evidence": [{"source": "as21"}], "warnings": [],
    }


def test_concrete_sprint_code_alltime_generic_planner_error_is_typed():
    res = _guard_lifetime_sprint_scope(
        _v4(), "Сколько всего часов было списано по задачам DMS-SPRNT-5 за всё время?"
    )
    assert res["status"] == "NEEDS_CLARIFICATION"
    assert "задачам спринта за всё время" in res["question"]
    assert "статус" not in res["question"]
    assert res["answer"] is None
    assert res["evidence"] == []
    assert "results" not in res["data"]
    assert "total_hours" not in res["data"]


def test_completed_calendar_total_cannot_be_promoted_to_lifetime():
    res = _guard_lifetime_sprint_scope(
        _v4("COMPLETED"), "Сколько часов за всю историю по задачам спринта?"
    )
    assert res["status"] == "NEEDS_CLARIFICATION"
    assert res["warnings"] == ["sprint_lifetime_scope_unsupported"]


def test_non_lifetime_sprint_request_unchanged():
    source = _v4("COMPLETED")
    assert _guard_lifetime_sprint_scope(
        source, "Сколько списал Гаранин в период спринта DMS-SPRNT-5?"
    ) is source


def test_non_sprint_lifetime_query_unchanged():
    source = _v4()
    assert _guard_lifetime_sprint_scope(source, "Покажи все списания Иванова за всё время") is source


def test_only_proven_all_date_source_may_complete():
    response = _v4("COMPLETED")
    response["data"]["results"] = [{
        "capability_id": "sprint.worklogs_all_dates",
        "data": {"all_time_total": True, "complete": True, "source": "REAL_AS21"},
    }]
    assert _guard_lifetime_sprint_scope(
        response, "Покажи часы по задачам спринта за всё время"
    ) is response
