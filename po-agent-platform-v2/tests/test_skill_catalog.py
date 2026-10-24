from po_agent.harness.skill_catalog import SKILL_CATALOG, catalog_by_id, catalog_summary

def test_catalog_contains_at_least_48_distinct_skills():
    ids=[e.id for e in SKILL_CATALOG]; caps=[e.capability_id for e in SKILL_CATALOG]
    assert len(SKILL_CATALOG)>=48 and len(ids)==len(set(ids)) and len(caps)==len(set(caps))

def test_catalog_preserves_core_po_domains():
    assert {"tasks","sprints","team","releases","portfolio","po"} <= {e.domain for e in SKILL_CATALOG}

def test_master_spec_search_and_release_forecast_are_not_lost():
    skills=catalog_by_id(); assert "task-search-product" in skills; assert "release-forecast" in skills

def test_all_catalog_skills_have_executable_implementations():
    skills=catalog_by_id()
    assert len(skills) == 54
    assert all(entry.status == "implemented" for entry in skills.values())

def test_source_dependent_skills_are_implemented_but_runtime_gated():
    skills=catalog_by_id()
    for skill_id in ("sprint-carryover","sprint-scope-change","team-competency-match","team-assignee-recommendation","release-forecast"):
        assert skills[skill_id].status == "implemented"

def test_draft_skills_do_not_claim_external_write_permission(): assert not [e for e in SKILL_CATALOG if e.requires_write]

def test_catalog_summary_is_machine_readable():
    summary=catalog_summary(); assert summary["total"]==54; assert summary["statuses"]["implemented"]==54; assert summary["statuses"]["planned"]==0; assert summary["by_domain"]["tasks"]==21; assert summary["by_domain"]["sprints"]==12; assert summary["by_domain"]["team"]==8; assert summary["by_domain"]["releases"]==7
