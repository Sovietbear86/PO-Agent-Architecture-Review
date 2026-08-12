from po_agent.harness.skill_catalog import SKILL_CATALOG, catalog_by_id, catalog_summary

def test_catalog_contains_at_least_48_distinct_skills():
    ids=[e.id for e in SKILL_CATALOG]; caps=[e.capability_id for e in SKILL_CATALOG]
    assert len(SKILL_CATALOG)>=48 and len(ids)==len(set(ids)) and len(caps)==len(set(caps))

def test_catalog_preserves_core_po_domains():
    assert {"tasks","sprints","team","releases","portfolio","po"} <= {e.domain for e in SKILL_CATALOG}

def test_master_spec_search_and_release_forecast_are_not_lost():
    skills=catalog_by_id(); assert "task-search-product" in skills; assert "release-forecast" in skills

def test_current_recovery_vertical_slices_are_marked_implemented():
    skills=catalog_by_id()
    implemented=("task-lookup","task-search","task-search-attachments","task-search-excel","task-search-pdf","task-search-msg","task-search-assignee","task-search-status","task-search-sprint","task-search-release","task-search-product","task-summary","task-quality","task-missing-requirements","task-acceptance-analysis","task-dependency-analysis","task-history","task-time-in-status","task-aging","task-blocker-analysis","task-similar","sprint-health","sprint-current","sprint-scope","sprint-velocity","sprint-throughput","sprint-wip","sprint-cycle-time","sprint-lead-time","sprint-predictability","sprint-risk-queue","team-workload","team-wip","team-blocked","team-capacity","team-bottlenecks","team-distribution","release-health","portfolio-overview")
    for skill_id in implemented: assert skills[skill_id].status=="implemented"

def test_history_snapshot_dependent_sprint_metrics_remain_planned():
    skills=catalog_by_id(); assert skills["sprint-carryover"].status=="planned"; assert skills["sprint-scope-change"].status=="planned"

def test_llm_team_recommendations_remain_planned_until_competency_source_is_wired():
    skills=catalog_by_id(); assert skills["team-competency-match"].status=="planned"; assert skills["team-assignee-recommendation"].status=="planned"

def test_draft_skills_do_not_claim_external_write_permission(): assert not [e for e in SKILL_CATALOG if e.requires_write]

def test_catalog_summary_is_machine_readable():
    summary=catalog_summary(); assert summary["total"]==54; assert summary["statuses"]["implemented"]==39; assert summary["statuses"]["planned"]==15; assert summary["by_domain"]["tasks"]==21; assert summary["by_domain"]["sprints"]==12; assert summary["by_domain"]["team"]==8; assert summary["by_domain"]["releases"]==7
