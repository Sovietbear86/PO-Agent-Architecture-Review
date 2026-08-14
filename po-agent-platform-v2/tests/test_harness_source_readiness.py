from po_agent.adapters.fake import FakeAS21Adapter
from po_agent.adapters.task_api import TaskApiAS21Adapter
from po_agent.harness.source_readiness import build_source_readiness


def test_fake_source_advertises_history_and_attachments_but_not_snapshots():
    report = build_source_readiness(FakeAS21Adapter())
    skills = report.by_skill()

    assert skills["task-history"].status == "ready"
    assert skills["task-search-pdf"].status == "ready"
    assert skills["sprint-cycle-time"].status == "ready"
    assert skills["sprint-carryover"].status == "unavailable"
    assert "sprint_snapshots" in skills["sprint-carryover"].missing_facts


def test_task_api_marks_missing_source_skills_unavailable():
    adapter = TaskApiAS21Adapter(base_url="http://example.invalid")
    report = build_source_readiness(adapter)
    skills = report.by_skill()

    assert skills["task-lookup"].status == "ready"
    assert skills["sprint-health"].status == "ready"
    assert skills["release-progress"].status == "ready"
    assert skills["task-history"].status == "unavailable"
    assert skills["task-search-attachments"].status == "unavailable"
    assert skills["sprint-cycle-time"].status == "unavailable"
    assert skills["team-competency-match"].status == "unavailable"
    assert skills["team-assignee-recommendation"].status == "unavailable"
    assert skills["sprint-carryover"].status == "unavailable"
    assert skills["sprint-scope-change"].status == "unavailable"
    assert skills["release-forecast"].status == "unavailable"
    assert skills["task-history"].missing_facts == ("history",)
    assert "attachments" in skills["task-search-attachments"].missing_facts
    assert "team_competencies" in skills["team-competency-match"].missing_facts
    assert "sprint_snapshots" in skills["sprint-carryover"].missing_facts
    assert "release_timeline" in skills["release-forecast"].missing_facts


def test_injected_sources_make_source_gated_skills_ready():
    report = build_source_readiness(
        TaskApiAS21Adapter(base_url="http://example.invalid"),
        extra_facts={"team_competencies", "sprint_snapshots", "release_timeline"},
    )
    skills = report.by_skill()
    assert skills["team-competency-match"].status == "ready"
    assert skills["team-assignee-recommendation"].status == "ready"
    assert skills["sprint-carryover"].status == "ready"
    assert skills["sprint-scope-change"].status == "ready"
    assert skills["release-forecast"].status == "ready"


def test_readiness_summary_covers_entire_catalog():
    report = build_source_readiness(FakeAS21Adapter())
    summary = report.summary()
    assert sum(summary.values()) == 54
