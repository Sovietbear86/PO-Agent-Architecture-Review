"""Regression coverage for bounded source-correctness defect B2.

B2: the live assignee route rows carry opaque encoded workflow status keys
(``CNCLLD_…``, ``PN_…``, ``PRBLMN_…``). The previous mapper normalized those
keys to UNKNOWN, so ``is_completed`` was always False and every row looked
"open" — an "open tasks" query reported 2609 instead of the true 404
non-terminal tasks (2205 terminal rows were counted as open).

The fix classifies completion from the source's authoritative workflow
semantics (``workflow_status.statusType`` category + decoded ``name``), never
by matching one exact opaque id. Undecodable statuses are neither open nor
completed, so they can never inflate a factual open-task collection.
"""

from datetime import datetime

import httpx
import pytest

from po_agent.adapters.production_task_api import ProductionTaskApiAS21Adapter
from po_agent.adapters.task_api import TaskApiAS21Adapter
from po_agent.domain.models import StatusCategory, Task, TaskStatus


def _task(status: TaskStatus, *, status_type: str | None = None, status_raw: str | None = None) -> Task:
    now = datetime.now()
    return Task(
        key="WMB-1",
        id="WMB-1",
        title="t",
        status=status,
        status_category=get_category(status),
        status_type=status_type,
        status_raw=status_raw,
        created_at=now,
        updated_at=now,
    )


def get_category(status: TaskStatus):
    from po_agent.domain.models import get_status_category

    return get_status_category(status)


# =============================================================================
# Domain model: status_type-driven open/completed classification
# =============================================================================


class TestStatusTypeClassification:
    def test_terminal_types_are_completed_and_not_open(self):
        for st in ("done", "closed", "cancelled", "finished", "resolved", "completed", "complete"):
            task = _task(TaskStatus.UNKNOWN, status_type=st)
            assert task.is_completed is True, st
            assert task.is_open is False, st

    def test_active_types_are_open_and_not_completed(self):
        for st in ("open", "todo", "backlog", "progress", "pause", "waiting", "blocked",
                   "review", "in_review", "qa", "testing", "reopened", "need_info"):
            task = _task(TaskStatus.UNKNOWN, status_type=st)
            assert task.is_open is True, st
            assert task.is_completed is False, st

    def test_live_lower_case_status_types(self):
        # REAL AS21 exposes lowercase categories; they must be recognized.
        assert _task(TaskStatus.UNKNOWN, status_type="done").is_completed is True
        assert _task(TaskStatus.UNKNOWN, status_type="progress").is_open is True
        assert _task(TaskStatus.UNKNOWN, status_type="pause").is_open is True

    def test_unknown_status_type_defers_to_name(self):
        # A category outside both known sets is not force-classified; the
        # canonical status enum (from the decoded name) decides.
        assert _task(TaskStatus.IN_PROGRESS, status_type="mystery").is_open is True
        assert _task(TaskStatus.CLOSED, status_type="mystery").is_completed is True
        assert _task(TaskStatus.CLOSED, status_type="mystery").is_open is False

    def test_undecodable_is_neither_open_nor_completed(self):
        task = _task(TaskStatus.UNKNOWN, status_type=None, status_raw="Mystery state")
        assert task.is_open is False
        assert task.is_completed is False

    def test_name_based_fallback_preserved_without_status_type(self):
        assert _task(TaskStatus.OPEN).is_open is True
        assert _task(TaskStatus.OPEN).is_completed is False
        assert _task(TaskStatus.NEED_INFO).is_open is True
        assert _task(TaskStatus.CLOSED).is_completed is True
        assert _task(TaskStatus.CLOSED).is_open is False
        assert _task(TaskStatus.REOPENED).is_open is True


# =============================================================================
# Adapter mapping: encoded row status + decoded workflow_status semantics
# =============================================================================


def _encoded_payload(key: str, row_status: str, ws_value: dict | None, space: str = "STS") -> dict:
    attributes = []
    if ws_value is not None:
        attributes.append({"code": "workflow_status", "value": ws_value})
    attributes.append({"code": "assigned_to", "value": {
        "externalId": "Ivanov.P.Se", "login": "ivanov.p.se",
        "firstName": "Пётр", "lastName": "Иванов",
    }})
    return {
        "id": key,
        "source_id": key,
        "title": "task",
        "status": row_status,
        "assignee": "Иванов Пётр",
        "source": "swtr",
        "source_data": {
            "swtr_space": space,
            "workflow_status": row_status,
            "swtr_attributes": attributes,
        },
    }


def _map(payload: dict) -> Task | None:
    return TaskApiAS21Adapter._map(payload)


class TestEncodedStatusMapping:
    def test_encoded_terminal_is_completed_via_semantics(self):
        task = _map(_encoded_payload("STS-1", "CNCLLD_kx9Z",
                                     {"code": "CNCLLD_kx9Z", "name": "CANCELLED", "statusType": "done"}))
        assert task is not None
        assert task.status_type == "done"
        assert task.status == TaskStatus.CANCELLED
        assert task.is_completed is True
        assert task.is_open is False

    def test_encoded_active_is_open_via_status_type(self):
        # "PROBLEM ANALYSIS" is not in the name map, so the authoritative
        # statusType ("progress") decides: non-terminal open work.
        task = _map(_encoded_payload("STS-2", "PN_kx9Z",
                                     {"code": "PN_kx9Z", "name": "PROBLEM ANALYSIS", "statusType": "progress"}))
        assert task is not None
        assert task.status_type == "progress"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.is_open is True
        assert task.is_completed is False

    def test_encoded_pause_is_open_not_completed(self):
        task = _map(_encoded_payload("STS-3", "OPEN_kx",
                                     {"code": "OPEN_kx", "name": "Open", "statusType": "pause"}))
        assert task is not None
        assert task.status_type == "pause"
        assert task.is_open is True
        assert task.is_completed is False

    def test_human_readable_status_preserved(self):
        task = _map(_encoded_payload("STS-4", "In progress",
                                     {"code": "PR_kx", "name": "In progress", "statusType": "progress"}))
        assert task is not None
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.is_open is True
        assert task.status_raw == "In progress"

    def test_encoded_status_without_semantics_stays_unknown_not_open(self):
        task = _map(_encoded_payload("STS-5", "CNCLLD_unknownId", None))
        assert task is not None
        assert task.status == TaskStatus.UNKNOWN
        assert task.status_type is None
        assert task.is_open is False
        assert task.is_completed is False

    @pytest.mark.asyncio
    async def test_live_shaped_assignee_round_trip_open_vs_completed(self):
        # End-to-end through the real assignee search path: encoded statuses
        # must not inflate the open collection and must not hide completed.
        rows = [
            _encoded_payload("STS-100", "CNCLLD_a", {"code": "CNCLLD_a", "name": "CANCELLED", "statusType": "done"}),
            _encoded_payload("STS-101", "PN_b", {"code": "PN_b", "name": "PROBLEM ANALYSIS", "statusType": "progress"}),
            _encoded_payload("STS-102", "OPEN_c", {"code": "OPEN_c", "name": "Open", "statusType": "pause"}),
            _encoded_payload("STS-103", "CLSD_d", {"code": "CLSD_d", "name": "Closed", "statusType": "done"}),
        ]

        async def handler(request):
            assert request.url.path == "/api/v1/swtr-read/assignee-tasks"
            return httpx.Response(200, json={"external_id": "Ivanov.P.Se", "tasks": rows})

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
        adapter = ProductionTaskApiAS21Adapter(client=client)
        tasks = await adapter.search_tasks("assignee = Ivanov.P.Se")
        await client.aclose()

        by_key = {t.key: t for t in tasks}
        assert set(by_key) == {"STS-100", "STS-101", "STS-102", "STS-103"}
        open_keys = sorted(t.key for t in tasks if t.is_open)
        completed_keys = sorted(t.key for t in tasks if t.is_completed)
        # Only the two non-terminal rows (progress + pause) are open.
        assert open_keys == ["STS-101", "STS-102"]
        # Both terminal rows (cancelled/done + closed/done) are completed.
        assert completed_keys == ["STS-100", "STS-103"]