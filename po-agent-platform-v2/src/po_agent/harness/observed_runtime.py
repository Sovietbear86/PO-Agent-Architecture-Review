"""Observed Harness runtime: execution, bounded session context and history."""
from __future__ import annotations

from .contracts import HarnessRequest, HarnessResponse, ResponseStatus
from .operational_history import ActiveVersions, HistoryStore, SQLiteHistoryStore, record_from_response
from .runtime import HarnessRuntime
from .session_context import SessionContextStore


class ObservedHarnessRuntime:
    """Decorator adding short-lived context and append-only execution history."""

    def __init__(
        self,
        runtime: HarnessRuntime,
        history: HistoryStore | None = None,
        versions: ActiveVersions | None = None,
        sessions: SessionContextStore | None = None,
    ) -> None:
        self.inner = runtime
        self.history = history or SQLiteHistoryStore()
        self.versions = versions or ActiveVersions()
        self.sessions = sessions or SessionContextStore()

        # Preserve introspection used by acceptance tests and future diagnostics.
        self.adapter = runtime.adapter
        self.router = runtime.router
        self.capabilities = runtime.capabilities
        self.skills = runtime.skills

    async def process(self, request: HarnessRequest) -> HarnessResponse:
        effective_request = self.sessions.resolve(request)
        response = await self.inner.process(effective_request)
        self.sessions.observe(request, effective_request, response)

        capability_id: str | None = None
        if response.intent:
            try:
                capability_id = self.skills.resolve(response.intent).capability_id
            except ValueError:
                capability_id = None

        error_category = None
        if response.status is ResponseStatus.FAILED:
            error_category = response.warnings[0] if response.warnings else "runtime_failure"

        # Audit the user's original request. Session state is intentionally not
        # serialized into operational history as hidden prompt context.
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
