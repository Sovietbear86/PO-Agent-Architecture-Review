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


def test_current_recovery_vertical_slices_are_marked_implemented():
    skills = catalog_by_id()
    for skill_id in (
        "task-lookup",
        "task-search",
        "sprint-health",
        "release-health",
        "portfolio-overview",
    ):
        assert skills[skill_id].status == "implemented"


def test_write_capabilities_are_explicitly_marked():
    write_skills = [entry for entry in SKILL_CATALOG if entry.requires_write]
    assert write_skills
    assert {entry.id for entry in write_skills} == {"po-local-task-draft"}


def test_catalog_summary_is_machine_readable():
    summary = catalog_summary()
    assert summary["total"] == 52
    assert summary["statuses"]["implemented"] == 5
    assert summary["statuses"]["planned"] == 47
    assert summary["by_domain"]["tasks"] == 20
    assert summary["by_domain"]["sprints"] == 12
