from po_agent.adapters.hardened_production_task_api import HardenedProductionTaskApiAS21Adapter


def _rich_unit(description):
    return {
        "code": "DMS-333",
        "summary": "[doc] ABAC c Apache Ranger описание",
        "description": description,
        "space": {"code": "DMS"},
        "createdAt": "2026-10-01T10:00:00+03:00",
        "updatedAt": "2026-10-02T11:00:00+03:00",
        "workflow_status": {"name": "Closed", "statusType": "done"},
        "attributes": [],
    }


def test_hardened_point_read_normalizes_serialized_rich_text_and_preserves_raw_source():
    raw = (
        '{"type":"doc","content":[{"type":"paragraph","attrs":{"indent":0,'
        '"textAlign":"justify"},"content":[{"type":"text","marks":[{"type":"link",'
        '"attrs":{"href":"https://example.invalid/wiki/123","target":"_blank"}}],'
        '"text":"wiki-страница"}]}]}'
    )

    task = HardenedProductionTaskApiAS21Adapter._map_raw_unit(_rich_unit(raw))

    assert task is not None
    assert task.description == "wiki-страница (https://example.invalid/wiki/123)"
    assert task.source_data["description"] == raw
    assert '"type":"doc"' not in task.description
    assert "textAlign" not in task.description


def test_hardened_point_read_keeps_plain_description_human_readable_and_raw():
    raw = "Обычное текстовое описание задачи"

    task = HardenedProductionTaskApiAS21Adapter._map_raw_unit(_rich_unit(raw))

    assert task is not None
    assert task.description == raw
    assert task.source_data["description"] == raw
