from po_agent.harness.skill_catalog import SKILL_CATALOG, catalog_by_id, catalog_summary


def test_catalog_contains_at_least_48_distinct_skills():
    ids = [entry.id for entry in SKILL_CATALOG]
    capability_ids = [entry.capability_id for entry in SKILL_CATALOG]
    assert len(SKILL_CATALOG) >= 48
    assert len(ids) == len(set(ids))
    assert len(capability_ids) == len(set(capability_ids))


def test_catalog_preserves_core_po_domains():
    domains = {entry.domain for entry in SKILL_CATALOG}
    assert {"tasks", "sprints", "team", "releases", "portfolio", "po"} <= domains


def test_master_spec_search_and_release_forecast_are_not_lost():
    skills = catalog_by_id()
    assert "task-search-product" in skills
    assert "release-forecast" in skills


def test_current_recovery_vertical_slices_are_marked_implemented():
    skills = catalog_by_id()
    for skill_id in (
        "task-lookup",
        "task-search",
        "task-search-attachments",
        "task-search-excel",
        "task-search-pdf",
        "task-search-msg",
        "task-search-assignee",
        "task-search-status",
        "task-search-sprint",
        "task-search-release",
        "task-search-product",
        "task-summary",
        "task-quality",
        "task-missing-requirements",
        "task-history",
        "task-time-in-status",
        "task-aging",
        "sprint-health",
        "release-health",
        "portfolio-overview",
    ):
        assert skills[skill_id].status == "implemented"


def test_draft_skills_do_not_claim_external_write_permission():
    assert not [entry for entry in SKILL_CATALOG if entry.requires_write]


def test_catalog_summary_is_machine_readable():
    summary = catalog_summary()
    assert summary["total"] == 54
    assert summary["statuses"]["implemented"] == 20
    assert summary["statuses"]["planned"] == 34
    assert summary["by_domain"]["tasks"] == 21
    assert summary["by_domain"]["sprints"] == 12
    assert summary["by_domain"]["releases"] == 7
