from po_agent.adapters.fake import FakeAS21Adapter
from po_agent.adapters.production_task_api import ProductionTaskApiAS21Adapter
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


def test_base_task_api_advertises_only_proven_task_and_attachment_facts():
    adapter = TaskApiAS21Adapter(base_url="http://example.invalid")
    report = build_source_readiness(adapter)
    skills = report.by_skill()

    assert skills["task-lookup"].status == "ready"
    assert skills["task-search-attachments"].status == "ready"
    assert skills["task-history"].status == "unavailable"
    assert skills["sprint-health"].status == "unavailable"
    assert skills["release-progress"].status == "unavailable"
    assert skills["sprint-cycle-time"].status == "unavailable"
    assert skills["team-competency-match"].status == "unavailable"
    assert skills["team-assignee-recommendation"].status == "unavailable"
    assert skills["sprint-carryover"].status == "unavailable"
    assert skills["release-forecast"].status == "unavailable"
    assert skills["task-history"].missing_facts == ("history",)
    assert "sprints" in skills["sprint-health"].missing_facts
    assert "releases" in skills["release-progress"].missing_facts
    assert "team_competencies" in skills["team-competency-match"].missing_facts


def test_production_task_api_advertises_proven_sprint_and_release_facts():
    adapter = ProductionTaskApiAS21Adapter(base_url="http://example.invalid")
    report = build_source_readiness(adapter)
    skills = report.by_skill()

    assert skills["task-search-attachments"].status == "ready"
    assert skills["sprint-health"].status == "ready"
    assert skills["sprint-velocity"].status == "ready"
    assert skills["release-health"].status == "ready"
    assert skills["release-progress"].status == "ready"
    assert skills["task-history"].status == "unavailable"


def test_injected_non_as21_sources_do_not_invent_missing_sprint_or_release_facts():
    report = build_source_readiness(
        TaskApiAS21Adapter(base_url="http://example.invalid"),
        extra_facts={"team_competencies", "sprint_snapshots", "release_timeline"},
    )
    skills = report.by_skill()
    assert skills["team-competency-match"].status == "ready"
    assert skills["team-assignee-recommendation"].status == "ready"
    assert skills["sprint-carryover"].status == "unavailable"  # still needs sprints
    assert skills["sprint-scope-change"].status == "unavailable"  # still needs sprints
    assert skills["release-forecast"].status == "unavailable"  # still needs releases


def test_readiness_summary_covers_entire_catalog():
    report = build_source_readiness(FakeAS21Adapter())
    summary = report.summary()
    assert sum(summary.values()) == 54
