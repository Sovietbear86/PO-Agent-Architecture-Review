"""Focused tests for the bounded-resilient task-api transport (Assignment 183, Phase 1).

Covers: operation-aware budget for /api/v1/swtr-read/ read-throughs, bounded retry
with backoff, client refresh on retry, immediate re-raise of non-transient HTTP
errors, single-shot behavior for standard paths, and typed fail-closed exhaustion.
"""
from __future__ import annotations

import httpx
import pytest

from po_agent.adapters import task_api as task_api_module
from po_agent.adapters.task_api import (
    AS21SourceUnavailable,
    TaskApiAS21Adapter,
)


class FakeResponse:
    def __init__(self, status_code: int = 200, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.content = str(self._payload).encode()

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", "http://stub")
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}", request=request, response=self
            )

    def json(self):
        return self._payload


class StubClient:
    """httpx.AsyncClient stand-in: replays a scripted sequence per get() call."""

    def __init__(self, script: list) -> None:
        self.script = list(script)
        self.calls = 0
        self.closed = False

    async def get(self, path, params=None, timeout=None):
        index = min(self.calls, len(self.script) - 1)
        self.calls += 1
        item = self.script[index]
        if isinstance(item, Exception):
            raise item
        return item

    async def aclose(self) -> None:
        self.closed = True


def _http_status(status_code: int) -> httpx.HTTPStatusError:
    return httpx.HTTPStatusError(
        f"HTTP {status_code}",
        request=httpx.Request("GET", "http://stub"),
        response=FakeResponse(status_code),
    )


def _adapter(script: list, **kwargs) -> tuple[TaskApiAS21Adapter, StubClient]:
    stub = StubClient(script)
    adapter = TaskApiAS21Adapter(base_url="http://stub", client=stub, **kwargs)
    return adapter, stub


def _patch_sleep(monkeypatch) -> list[float]:
    """Replace asyncio.sleep with an awaitable recorder; returns the list."""
    sleeps: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    monkeypatch.setattr(task_api_module.asyncio, "sleep", fake_sleep)
    return sleeps


@pytest.mark.asyncio
async def test_read_through_retries_timeout_then_succeeds(monkeypatch):
    sleeps = _patch_sleep(monkeypatch)
    adapter, stub = _adapter([httpx.ReadTimeout("slow"), FakeResponse(200, {"ok": True})])

    response = await adapter._get_resilient("/api/v1/swtr-read/assignee-tasks", params={"assignee": "x"})

    assert response.json() == {"ok": True}
    assert stub.calls == 2
    assert len(sleeps) == 1 and sleeps[0] > 0


@pytest.mark.asyncio
async def test_read_through_retries_502_then_succeeds(monkeypatch):
    sleeps = _patch_sleep(monkeypatch)
    adapter, stub = _adapter([_http_status(502), FakeResponse(200, {"ok": True})])

    response = await adapter._get_resilient("/api/v1/swtr-read/tasks/DMS-1")

    assert response.json() == {"ok": True}
    assert stub.calls == 2
    assert len(sleeps) == 1


@pytest.mark.asyncio
async def test_read_through_exhaustion_is_typed_and_bounded(monkeypatch):
    sleeps = _patch_sleep(monkeypatch)
    adapter, stub = _adapter([httpx.ReadTimeout("slow")] * 5, read_through_attempts=3)

    with pytest.raises(AS21SourceUnavailable):
        await adapter._get_resilient("/api/v1/swtr-read/sprints/DMS-SPRNT-1/tasks")

    # bounded: exactly 3 attempts, 2 backoffs — no infinite retry, no retry storm
    assert stub.calls == 3
    assert len(sleeps) == 2
    assert sleeps == [task_api_module._RETRY_BACKOFF_SECONDS[0], task_api_module._RETRY_BACKOFF_SECONDS[1]]


@pytest.mark.asyncio
async def test_non_transient_404_is_raised_immediately_without_retry():
    adapter, stub = _adapter([_http_status(404)])

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await adapter._get_resilient("/api/v1/swtr-read/tasks/DMS-999")

    assert exc_info.value.response.status_code == 404
    assert stub.calls == 1


@pytest.mark.asyncio
async def test_standard_path_is_single_shot_and_typed():
    adapter, stub = _adapter([httpx.ConnectError("down")])

    with pytest.raises(AS21SourceUnavailable):
        await adapter._get_resilient("/api/v1/tasks", params={"limit": 1})

    assert stub.calls == 1


@pytest.mark.asyncio
async def test_read_through_uses_operation_aware_timeout():
    seen_timeouts: list = []

    class TimeoutProbeClient(StubClient):
        async def get(self, path, params=None, timeout=None):
            seen_timeouts.append(timeout)
            return FakeResponse(200, {"ok": True})

    adapter = TaskApiAS21Adapter(base_url="http://stub", client=TimeoutProbeClient([FakeResponse()]))
    await adapter._get_resilient("/api/v1/swtr-read/assignee-tasks")
    await adapter._get_resilient("/api/v1/tasks")

    assert seen_timeouts[0] is not None
    assert seen_timeouts[0].read == adapter._read_through_timeout_seconds
    assert seen_timeouts[1] is None  # standard path keeps client default ceiling


@pytest.mark.asyncio
async def test_client_refreshed_on_retry_when_owned(monkeypatch):
    sleeps = _patch_sleep(monkeypatch)

    class FailingOnceClient(StubClient):
        async def get(self, path, params=None, timeout=None):
            if self.calls == 0:
                self.calls += 1
                raise httpx.ReadTimeout("slow")
            return await super().get(path, params=params, timeout=timeout)

    adapter = TaskApiAS21Adapter(base_url="http://stub")
    assert adapter._owns_client
    first = adapter._client
    fresh = StubClient([FakeResponse(200, {"ok": True})])
    adapter._new_client = lambda: fresh  # the refresh path builds "fresh"
    adapter._client = FailingOnceClient([FakeResponse(200)])

    response = await adapter._get_resilient("/api/v1/swtr-read/tasks/DMS-1")

    assert response.json() == {"ok": True}
    assert adapter._client is fresh
    assert first is not adapter._client
    assert sleeps == [task_api_module._RETRY_BACKOFF_SECONDS[0]]


@pytest.mark.asyncio
async def test_injected_client_is_never_replaced_by_refresh():
    stub = StubClient([FakeResponse(200)])
    adapter = TaskApiAS21Adapter(base_url="http://stub", client=stub)
    assert not adapter._owns_client
    await adapter._refresh_client()
    assert adapter._client is stub


@pytest.mark.asyncio
async def test_refresh_closes_old_client():
    adapter = TaskApiAS21Adapter(base_url="http://stub")
    old = adapter._client
    await adapter._refresh_client()
    assert old is not adapter._client
    assert old.is_closed is True