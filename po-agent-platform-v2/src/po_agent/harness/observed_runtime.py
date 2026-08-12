"""Observed Harness runtime: execution plus append-only operational history."""
from __future__ import annotations

from .contracts import HarnessRequest, HarnessResponse, ResponseStatus
from .operational_history import ActiveVersions, HistoryStore, SQLiteHistoryStore, record_from_response
from .runtime import HarnessRuntime


class ObservedHarnessRuntime:
    """Decorator that records every Harness execution without changing business logic."""

    def __init__(
        self,
        runtime: HarnessRuntime,
        history: HistoryStore | None = None,
        versions: ActiveVersions | None = None,
    ) -> None:
        self.inner = runtime
        self.history = history or SQLiteHistoryStore()
        self.versions = versions or ActiveVersions()

        # Preserve introspection used by acceptance tests and future diagnostics.
        self.adapter = runtime.adapter
        self.router = runtime.router
        self.capabilities = runtime.capabilities
        self.skills = runtime.skills

    async def process(self, request: HarnessRequest) -> HarnessResponse:
        response = await self.inner.process(request)
        capability_id: str | None = None
        if response.intent:
            try:
                capability_id = self.skills.resolve(response.intent).capability_id
            except ValueError:
                capability_id = None

        error_category = None
        if response.status is ResponseStatus.FAILED:
            error_category = response.warnings[0] if response.warnings else "runtime_failure"

        self.history.append(
            record_from_response(
                request,
                response,
                capability_id=capability_id,
                versions=self.versions,
                llm_used=False,
                error_category=error_category,
            )
        )
        return response
