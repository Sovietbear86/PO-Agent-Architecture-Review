from __future__ import annotations

from po_agent.adapters.hardened_production_task_api import HardenedProductionTaskApiAS21Adapter
from po_agent.adapters.task_api import TaskApiAS21Adapter


def _attrs():
    return [
        {"code": "label", "value": ["AQA", "DataMarts server"]},
        {"code": "sber_component", "value": [{"name": "OLAP"}, {"name": "dmts"}]},
        {"code": "workflow_status", "value": {"name": "Open", "statusType": "open"}},
    ]


def test_hardened_raw_unit_preserves_labels_and_components():
    task = HardenedProductionTaskApiAS21Adapter._map_raw_unit(
        {
            "code": "DMS-408",
            "summary": "DataMarts task",
            "description": "description",
            "attributes": _attrs(),
            "space": {"code": "DMS"},
            "createdAt": "2026-09-01T10:00:00Z",
            "updatedAt": "2026-09-02T10:00:00Z",
        }
    )

    assert task is not None
    assert task.labels == ["AQA", "DataMarts server"]
    assert task.components == ["OLAP", "dmts"]


def test_generic_mapper_decodes_raw_attributes_for_labels_and_components():
    task = TaskApiAS21Adapter._map(
        {
            "source_id": "OLP-3339",
            "title": "OLAP task",
            "description": "description",
            "status": "Open",
            "created_at": "2026-09-01T10:00:00Z",
            "updated_at": "2026-09-02T10:00:00Z",
            "source": "swtr",
            "source_data": {
                "attributes": _attrs(),
                "swtr_space": "OLP",
            },
        }
    )

    assert task is not None
    assert task.labels == ["AQA", "DataMarts server"]
    assert task.components == ["OLAP", "dmts"]
