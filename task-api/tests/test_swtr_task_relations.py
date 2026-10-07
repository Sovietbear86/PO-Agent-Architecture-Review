import asyncio
import json

from app.routers.swtr_read import _get_unit_links_complete, _task_link_facts


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



def test_get_unit_links_complete_uses_live_flat_request_contract():
    class Client:
        def __init__(self):
            self.calls = []

        async def call_tool(self, name, arguments):
            self.calls.append((name, arguments))
            return [{
                "type": "text",
                "text": json.dumps({
                    "content": [
                        {
                            "source": "DMS-253",
                            "destination": "DMS-267",
                            "type": "decomposition",
                            "deleted": False,
                        }
                    ],
                    "hasNext": False,
                    "pageNumber": 0,
                    "pageSize": 100,
                    "totalElements": 1,
                }),
            }]

    client = Client()
    rows = asyncio.run(_get_unit_links_complete(client, "DMS-253"))

    assert len(rows) == 1
    assert client.calls == [(
        "get_unit_links",
        {
            "request": {
                "unit_code": "DMS-253",
                "link_types": [],
                "page": 0,
                "size": 100,
            }
        },
    )]


def test_get_unit_links_complete_paginates_with_flat_page_number():
    class Client:
        def __init__(self):
            self.calls = []

        async def call_tool(self, name, arguments):
            self.calls.append((name, arguments))
            page = arguments["request"]["page"]
            payload = {
                "content": [{
                    "source": "DMS-253",
                    "destination": f"DMS-{267 + page}",
                    "type": "decomposition",
                    "deleted": False,
                }],
                "hasNext": page == 0,
                "pageNumber": page,
                "pageSize": 1,
                "totalElements": 2,
            }
            return [{"type": "text", "text": json.dumps(payload)}]

    client = Client()
    rows = asyncio.run(_get_unit_links_complete(client, "DMS-253", page_size=1))

    assert len(rows) == 2
    assert [call[1]["request"]["page"] for call in client.calls] == [0, 1]
    assert all(call[1]["request"]["size"] == 1 for call in client.calls)
