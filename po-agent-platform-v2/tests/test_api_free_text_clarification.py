"""A230R3.2 — continuation API seam, independent from frozen Core V4."""
import time
import uuid

import pytest

from po_agent.api.v1 import (
    QueryRequest, PendingClarification, _pending_clarifications,
    _free_text_clarification_kind, _prepare_query,
)


@pytest.fixture(autouse=True)
def clean_pending():
    _pending_clarifications.clear()
    yield
    _pending_clarifications.clear()


def pending(session, question="Уточните период списаний.", options=()):
    item = PendingClarification(
        clarification_id=str(uuid.uuid4()), original_query="Покажи списания Иванова",
        question=question, options=options, created_at=time.monotonic(),
        resume_loaded_skills=("member.worklogs_period",),
        required_completion_skills=("member.worklogs_period",),
    )
    _pending_clarifications[session] = item
    return item


@pytest.mark.parametrize("reply", [
    "с 21.09.2026 по сегодня", "с 2026-09-21 по сегодня",
    "за последние 2 недели", "за 14 дней", "сегодня",
])
def test_date_followup_preserves_original_intent_and_completion(reply):
    item = pending("s1")
    effective, early, continuation = _prepare_query(QueryRequest(query=reply), "s1")
    assert early is None
    assert item.original_query in effective
    assert reply in effective
    assert continuation.required_completion_skills == ("member.worklogs_period",)
    assert "s1" not in _pending_clarifications


def test_what_to_clarify_returns_pending_question_without_consuming():
    item = pending("s1")
    effective, early, _ = _prepare_query(QueryRequest(query="Что именно нужно уточнить?"), "s1")
    assert effective is None
    assert early["question"] == item.question
    assert early["clarification_id"] == item.clarification_id
    assert "s1" in _pending_clarifications


def test_unrelated_new_query_not_hijacked():
    pending("s1")
    original = "Покажи задачи Ивановой в DMS"
    effective, early, continuation = _prepare_query(QueryRequest(query=original), "s1")
    assert early is None
    assert effective == original
    assert not continuation.loaded_skills
    assert "s1" not in _pending_clarifications


def test_date_answer_not_hijacked_when_question_about_space():
    pending("s1", "Укажите пространство проекта.")
    effective, early, _ = _prepare_query(QueryRequest(query="за 2 недели"), "s1")
    assert early is None and effective == "за 2 недели"


def test_option_click_rejects_non_option():
    item = pending("s1", options=("DMS", "OLP"))
    effective, early, _ = _prepare_query(QueryRequest(
        query="OTHER", clarification_id=item.clarification_id,
        clarification_option="OTHER"), "s1")
    assert effective is None
    assert early["warnings"] == ["invalid_clarification_option"]


def test_session_isolation_and_expiration():
    item = pending("s1")
    pending("s2")
    effective, early, _ = _prepare_query(QueryRequest(query="сегодня"), "s1")
    assert early is None and item.original_query in effective
    assert "s2" in _pending_clarifications
    _pending_clarifications["s2"].created_at -= 100000
    effective, early, _ = _prepare_query(QueryRequest(query="сегодня"), "s2")
    assert effective is None
    assert early["intent"] == "clarification_context_lost"
