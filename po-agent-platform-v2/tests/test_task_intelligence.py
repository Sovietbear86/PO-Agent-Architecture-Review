from datetime import datetime, timedelta

from po_agent.analysis.task_intelligence import TaskIntelligenceAnalysis
from po_agent.domain.models import StatusCategory, StatusTransition, Task, TaskStatus


def task(key="WMB-1", title="Implement deterministic task intelligence", description="Цель: улучшить анализ.\n- критерий один\n- критерий два", **kwargs):
    now = datetime.now()
    data = dict(
        key=key, id=key, title=title, description=description,
        status=TaskStatus.IN_PROGRESS, status_category=StatusCategory.ACTIVE_WORK,
        created_at=now-timedelta(days=20), updated_at=now,
    )
    data.update(kwargs)
    return Task(**data)


def test_missing_requirements_and_acceptance_are_deterministic():
    analyzer = TaskIntelligenceAnalysis()
    weak = task(description="коротко")
    assert analyzer.missing_requirements(weak)["complete"] is False
    assert analyzer.acceptance_analysis(weak)["testable"] is False
    strong = task()
    assert analyzer.acceptance_analysis(strong)["testable"] is True


def test_dependency_analysis_never_invents_dependencies():
    result = TaskIntelligenceAnalysis().dependency_analysis(task(depends_on=[]))
    assert result["depends_on"] == []
    assert result["evidence_limited"] is True


def test_history_and_time_in_status_fail_closed_without_history():
    analyzer = TaskIntelligenceAnalysis()
    item = task(status_transitions=[])
    assert analyzer.history(item)["history_available"] is False
    assert analyzer.time_in_status(item)["hours"] is None


def test_time_in_status_uses_canonical_last_transition():
    now = datetime.now()
    transition = StatusTransition(from_status=TaskStatus.OPEN, to_status=TaskStatus.IN_PROGRESS, timestamp=now-timedelta(hours=6))
    result = TaskIntelligenceAnalysis().time_in_status(task(status_transitions=[transition]), now=now)
    assert 5.99 <= result["hours"] <= 6.01


def test_aging_only_flags_active_tasks():
    analyzer = TaskIntelligenceAnalysis()
    now = datetime.now()
    assert analyzer.aging(task(created_at=now-timedelta(days=20)), now=now)["is_aging"] is True
    closed = task(created_at=now-timedelta(days=20), status=TaskStatus.CLOSED, status_category=StatusCategory.COMPLETED)
    assert analyzer.aging(closed, now=now)["is_aging"] is False


def test_blocker_analysis_uses_only_canonical_evidence():
    analyzer = TaskIntelligenceAnalysis()
    assert analyzer.blocker_analysis(task(status=TaskStatus.NEED_INFO, status_category=StatusCategory.WAITING))["blocked"] is True
    assert analyzer.blocker_analysis(task(depends_on=[]))["blocked"] is False


def test_similar_tasks_is_bounded_and_excludes_self():
    analyzer = TaskIntelligenceAnalysis()
    base = task("WMB-1", title="Добавить фильтр задач по спринту", description="Фильтрация задач AS21 по спринту")
    close = task("WMB-2", title="Добавить фильтр задач по спринту", description="Фильтрация задач AS21 по спринту")
    other = task("WMB-3", title="Обновить документацию релиза", description="Документация")
    result = analyzer.similar_tasks(base, [base, close, other], threshold=0.7)
    assert [item["task_key"] for item in result["matches"]] == ["WMB-2"]
