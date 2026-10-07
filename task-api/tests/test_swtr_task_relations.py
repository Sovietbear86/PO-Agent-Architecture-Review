from app.routers.swtr_read import _task_link_facts


def test_link_facts_extract_structural_parent_epic_and_related_links():
    rows = [
        {"source": "DMS-100", "destination": "DMS-333", "type": "decomposition", "deleted": False},
        {"source": "DMS-333", "destination": "DMS-1", "type": "realized_in", "deleted": False},
        {"source": "DMS-333", "destination": "DMS-200", "type": "dependend", "deleted": False},
        {"source": "DMS-333", "destination": "DMS-334", "type": "decomposition", "deleted": False},
    ]

    facts = _task_link_facts("DMS-333", rows)

    assert facts["schema_proven"] is True
    assert facts["parent_key"] == "DMS-100"
    assert facts["epic_key"] == "DMS-1"
    assert set(facts["related_keys"]) == {"DMS-200", "DMS-334"}
    assert "mcp:get_unit_links" in facts["source_fields_seen"]
    assert "link_type:decomposition" in facts["source_fields_seen"]
    assert "link_type:realized_in" in facts["source_fields_seen"]


def test_link_facts_empty_complete_source_is_proven_empty_not_unknown():
    facts = _task_link_facts("DMS-333", [])

    assert facts["schema_proven"] is True
    assert facts["parent_key"] is None
    assert facts["epic_key"] is None
    assert facts["related_keys"] == []
    assert facts["source_fields_seen"] == ["mcp:get_unit_links"]


def test_link_facts_surface_ambiguous_structural_parent():
    rows = [
        {"source": "DMS-10", "destination": "DMS-333", "type": "decomposition", "deleted": False},
        {"source": "DMS-11", "destination": "DMS-333", "type": "decomposition", "deleted": False},
    ]

    facts = _task_link_facts("DMS-333", rows)

    assert facts["parent_key"] is None
    assert facts["parent_ambiguous"] is True
    assert facts["parent_candidates"] == ["DMS-10", "DMS-11"]


def test_realized_in_is_epic_relation_not_structural_parent():
    rows = [
        {"source": "CRPV-90180", "destination": "DMS-253", "type": "realized_in", "deleted": False},
        {"source": "CRPV-90180", "destination": "DMS-253", "type": "decomposition", "deleted": False},
    ]

    source_facts = _task_link_facts("CRPV-90180", rows)
    destination_facts = _task_link_facts("DMS-253", rows)

    assert source_facts["parent_key"] is None
    assert source_facts["epic_key"] == "DMS-253"
    assert destination_facts["parent_key"] == "CRPV-90180"
    assert destination_facts["epic_key"] is None
