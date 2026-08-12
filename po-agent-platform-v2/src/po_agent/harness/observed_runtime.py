"""Observed Harness runtime: execution, bounded session context and history."""
from __future__ import annotations

from .contracts import HarnessRequest, HarnessResponse, ResponseStatus
from .eval_store import EvalSeed, EvalSeedStore, SQLiteEvalSeedStore, seed_from_feedback
from .feedback_store import FeedbackRecord, FeedbackStore, SQLiteFeedbackStore, make_feedback
from .operational_history import ActiveVersions, HistoryStore, SQLiteHistoryStore, record_from_response
from .runtime import HarnessRuntime
from .session_context import SessionContextStore


class ObservedHarnessRuntime:
    """Decorator adding short-lived context, history, feedback and eval seeds."""

    def __init__(
        self,
        runtime: HarnessRuntime,
        history: HistoryStore | None = None,
        versions: ActiveVersions | None = None,
        sessions: SessionContextStore | None = None,
        feedback: FeedbackStore | None = None,
        evals: EvalSeedStore | None = None,
    ) -> None:
        self.inner = runtime
        self.history = history or SQLiteHistoryStore()
        self.versions = versions or ActiveVersions()
        self.sessions = sessions or SessionContextStore()
        self.feedback = feedback or SQLiteFeedbackStore()
        self.evals = evals or SQLiteEvalSeedStore()

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

    def submit_feedback(
        self,
        trace_id: str,
        rating: str,
        *,
        correction: str | None = None,
        expected_intent: str | None = None,
        expected_entity: str | None = None,
        comment: str | None = None,
    ) -> FeedbackRecord:
        """Attach explicit feedback to a completed/failed execution trace."""
        trace = self.history.get(trace_id)
        if trace is None:
            raise ValueError(f"unknown trace_id: {trace_id}")
        record = make_feedback(
            trace_id=trace_id,
            session_id=trace.session_id,
            rating=rating,
            correction=correction,
            expected_intent=expected_intent,
            expected_entity=expected_entity,
            comment=comment,
            metadata={
                "skill_id": trace.skill_id,
                "skill_version": trace.skill_version,
                "agent_version": trace.versions.agent,
                "router_version": trace.versions.router,
            },
        )
        self.feedback.append(record)
        return record

    def create_eval_seed(self, trace_id: str, feedback_id: str) -> EvalSeed:
        """Explicitly curate one trace+feedback pair into an offline eval candidate."""
        trace = self.history.get(trace_id)
        if trace is None:
            raise ValueError(f"unknown trace_id: {trace_id}")
        matches = [item for item in self.feedback.by_trace(trace_id) if item.feedback_id == feedback_id]
        if not matches:
            raise ValueError(f"unknown feedback_id for trace: {feedback_id}")
        seed = seed_from_feedback(trace, matches[0])
        self.evals.append(seed)
        return seed
