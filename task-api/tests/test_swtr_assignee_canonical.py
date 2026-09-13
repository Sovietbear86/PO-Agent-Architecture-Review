"""Assignment 185 — B2 regression: assignee route preserves decoded workflow semantics.

B2: the live assignee route rows carried opaque encoded workflow status keys
(``CNCLLD_…``, ``PN_…``, ``PRBLMN_…``) at the row level, and passed the raw
*nested* TQL attribute list (``{"attribute": {"code":...}, "value": {...}}``)
through into ``swtr_attributes``. The agent's flat-only attribute parser then
silently dropped the decoded ``workflow_status`` (name + statusType), so every
encoded row fell back to UNKNOWN and was treated as "open" — inflating an
"open tasks" collection (2609) instead of the true non-terminal set (404).

The fix normalizes ``swtr_attributes`` to the flat ``{"code","value"}``
contract (both encodings, row-level and under ``unit``) and exposes the
human-readable status name at the row level, so terminal/open classification
is driven by the source's authoritative ``statusType``/``name``.
"""

from app.routers.swtr_assignee import (
    _canonical_row,
    _raw_attribute_entries,
    _status_identifier,
)


def _nested_row() -> dict:
    """Live TQL shape: unit nested, attributes at row level in nested encoding."""
    return {
        "unit": {
            "code": "STS-547220",
            "summary": "Уязвимость в Platform V",
            "space": {"code": "STS", "name": "Sbt to Sbt"},
        },
        "attributes": [
            {
                "attribute": {"code": "workflow_status", "name": "Статус", "type": "workflow_status"},
                "value": {"name": "PROBLEM ANALYSIS", "code": "PRBLMN_ZghEqKJlAzmUx", "statusType": "progress"},
                "valueAsString": None,
            },
            {
                "attribute": {"code": "assigned_to", "name": "Исполнитель", "type": "user"},
                "value": {"externalId": "Kalachanov.V.V", "login": "kalachanov.v.v",
                          "firstName": "Виктор", "lastName": "Калачанов"},
                "valueAsString": None,
            },
        ],
        "calculatedAttributes": [],
    }


def _flat_row() -> dict:
    """Flat encoding at the row level (also accepted)."""
    return {
        "unit": {"code": "STS-1", "summary": "task", "space": {"code": "STS"}},
        "attributes": [
            {"code": "workflow_status", "value": {"name": "Closed", "code": "CLSD_x", "statusType": "done"}},
            {"code": "assigned_to", "value": {"externalId": "Ivanov.P.Se", "login": "ivanov.p.se"}},
        ],
    }


class TestRawAttributeEntries:
    def test_nested_encoding(self):
        entries = dict(_raw_attribute_entries(_nested_row()))
        assert entries["workflow_status"]["statusType"] == "progress"
        assert entries["assigned_to"]["externalId"] == "Kalachanov.V.V"

    def test_flat_encoding(self):
        entries = dict(_raw_attribute_entries(_flat_row()))
        assert entries["workflow_status"]["statusType"] == "done"

    def test_unit_level_attributes(self):
        row = {"unit": {"code": "DMS-1",
                        "attributes": [{"code": "workflow_status", "value": {"statusType": "pause"}}]}}
        entries = dict(_raw_attribute_entries(row))
        assert entries["workflow_status"]["statusType"] == "pause"

    def test_no_attributes(self):
        assert _raw_attribute_entries({"attributes": []}) == []
        assert _raw_attribute_entries({}) == []


class TestStatusIdentifier:
    def test_prefers_name_over_opaque_code(self):
        assert _status_identifier(
            {"code": "PRBLMN_x", "name": "PROBLEM ANALYSIS", "statusType": "progress"}) == "PROBLEM ANALYSIS"

    def test_plain_string(self):
        assert _status_identifier("In progress") == "In progress"

    def test_missing(self):
        assert _status_identifier(None) == ""


class TestCanonicalRow:
    def test_nested_row_preserves_status_type_in_flat_swtr_attributes(self):
        canonical = _canonical_row(_nested_row())
        assert canonical is not None
        assert canonical["source_id"] == "STS-547220"
        assert canonical["status"] == "PROBLEM ANALYSIS"
        flat = {e["code"]: e["value"] for e in canonical["source_data"]["swtr_attributes"]}
        assert flat["workflow_status"]["statusType"] == "progress"
        assert flat["workflow_status"]["name"] == "PROBLEM ANALYSIS"
        assert flat["assigned_to"]["externalId"] == "Kalachanov.V.V"
        assert canonical["source_data"]["swtr_space"] == "STS"

    def test_flat_row_contract(self):
        canonical = _canonical_row(_flat_row())
        assert canonical is not None
        assert canonical["source_id"] == "STS-1"
        flat = {e["code"]: e["value"] for e in canonical["source_data"]["swtr_attributes"]}
        assert flat["workflow_status"]["statusType"] == "done"
        assert canonical["status"] == "Closed"

    def test_no_task_code_returns_none(self):
        assert _canonical_row({"attributes": []}) is None