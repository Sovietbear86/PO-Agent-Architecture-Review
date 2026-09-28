from task_api.app.routers.swtr_assignee import _canonical_row


def test_canonical_row_surfaces_source_timestamps():
    row = {
        "attributes": [
            {"code": "code", "value": "WMB-1"},
            {"code": "summary", "value": "Example"},
            {"code": "space", "value": {"code": "WMB"}},
            {"code": "workflow_status", "value": {"name": "In progress"}},
            {"code": "created_at", "value": "2026-09-01T10:00:00+03:00"},
            {"code": "updatedAt", "value": "2026-09-20T12:00:00+03:00"},
            {"code": "dueDate", "value": "2026-09-30T00:00:00+03:00"},
        ]
    }

    mapped = _canonical_row(row)

    assert mapped is not None
    assert mapped["source_id"] == "WMB-1"
    assert mapped["created_at"] == "2026-09-01T10:00:00+03:00"
    assert mapped["updated_at"] == "2026-09-20T12:00:00+03:00"
    assert mapped["deadline"] == "2026-09-30T00:00:00+03:00"
