from app.routers.swtr_read import _task_relation_facts


def test_relation_facts_extract_parent_epic_and_links_from_realistic_unit_shape():
    unit = {
        "code": "DMS-333",
        "suit": {"code": "story", "name": "Story"},
        "links": [
            {"code": "DMS-334"},
            {"target": {"code": "DMS-335"}},
        ],
        "attributes": [
            {"code": "parent", "value": {"code": "DMS-100"}},
            {"code": "epic_link", "value": {"code": "DMS-1"}},
            {"code": "depends_on", "value": [{"code": "DMS-200"}]},
        ],
    }

    facts = _task_relation_facts(unit)

    assert facts["schema_proven"] is True
    assert facts["parent_key"] == "DMS-100"
    assert facts["epic_key"] == "DMS-1"
    assert set(facts["related_keys"]) == {"DMS-334", "DMS-335", "DMS-200"}
    assert "attribute:parent" in facts["source_fields_seen"]
    assert "attribute:epic_link" in facts["source_fields_seen"]
    assert "unit:links" in facts["source_fields_seen"]


def test_relation_facts_do_not_invent_empty_contract_when_no_relation_field_is_visible():
    unit = {
        "code": "DMS-333",
        "suit": {"code": "task", "name": "Задача"},
        "attributes": [
            {"code": "assigned_to", "value": {"externalId": "Ivanov.I.I"}},
            {"code": "workflow_status", "value": {"name": "Open"}},
        ],
    }

    facts = _task_relation_facts(unit)

    assert facts["schema_proven"] is False
    assert facts["parent_key"] is None
    assert facts["epic_key"] is None
    assert facts["related_keys"] == []


def test_relation_facts_surface_ambiguous_parent_instead_of_choosing_one():
    unit = {
        "code": "DMS-333",
        "attributes": [
            {"code": "parent", "value": [{"code": "DMS-10"}, {"code": "DMS-11"}]},
        ],
    }

    facts = _task_relation_facts(unit)

    assert facts["parent_key"] is None
    assert facts["parent_ambiguous"] is True
    assert facts["parent_candidates"] == ["DMS-10", "DMS-11"]
