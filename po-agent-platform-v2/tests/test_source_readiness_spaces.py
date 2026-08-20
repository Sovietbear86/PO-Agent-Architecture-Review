from po_agent.harness.source_readiness import SourceFact, build_source_readiness
from po_agent.adapters.hardened_production_task_api import HardenedProductionTaskApiAS21Adapter


class _AdapterStub:
    source_name = "stub"
    source_facts = frozenset({"tasks", "spaces"})


def test_spaces_is_a_valid_source_fact():
    assert SourceFact("spaces") is SourceFact.SPACES


def test_product_search_requires_spaces_fact():
    report = build_source_readiness(_AdapterStub())
    item = report.by_skill()["task-search-product"]
    assert item.status == "ready"
    assert item.required_facts == ("tasks", "spaces")


def test_product_search_unavailable_without_spaces_fact():
    class TasksOnly:
        source_name = "tasks-only"
        source_facts = frozenset({"tasks"})

    report = build_source_readiness(TasksOnly())
    item = report.by_skill()["task-search-product"]
    assert item.status == "unavailable"
    assert item.missing_facts == ("spaces",)
