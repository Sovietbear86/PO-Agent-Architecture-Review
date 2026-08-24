"""Meaning-based correction/recheck runtime for production Harness.

Corrections are interpreted in the same conversation session against the previous
canonical semantic state. The runtime never creates a synthetic natural-language
mega-query, which previously allowed the model to lose or duplicate filters.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

from .contracts import HarnessRequest, HarnessResponse, ResponseStatus
from .semantic_core_v2 import DialogueAct


@dataclass
class _PreviousTurn:
    query: str
    response: HarnessResponse


class SemanticCorrectionRuntimeV2:
    def __init__(self, inner, semantic_interpreter) -> None:
        self.inner = inner
        self.semantic_interpreter = semantic_interpreter
        self._last: dict[str, _PreviousTurn] = {}
        for name in ("adapter", "router", "capabilities", "skills"):
            if hasattr(inner, name):
                setattr(self, name, getattr(inner, name))

    @staticmethod
    def _attach_meta(response: HarnessResponse, *, previous_trace: str, recheck_trace: str, correction: str, act: str) -> None:
        if response.data is None or not isinstance(response.data, dict):
            response.data = {} if response.data is None else {"result": response.data}
        meta = response.data.setdefault("_harness", {})
        if not isinstance(meta, dict):
            meta = {}
            response.data["_harness"] = meta
        meta["correction"] = {
            "dialogue_act": act,
            "correction_text": correction,
            "previous_trace_id": previous_trace,
            "recheck_trace_id": recheck_trace,
            "source_recheck_performed": True,
            "persistent_skill_mutation": False,
            "semantic_state_reused": True,
        }

    @staticmethod
    def _same_query(current: str, previous: str) -> bool:
        """Treat an exact natural-language repeat as an idempotent rerun.

        Repeating the same standalone request must never become a correction/recheck
        solely because the session already contains a previous turn. Whitespace and
        letter case are not semantically meaningful for this guard.
        """
        normalize = lambda value: " ".join((value or "").split()).casefold()
        return bool(normalize(current)) and normalize(current) == normalize(previous)

    def _clear_semantic_previous_turn(self, session: str) -> None:
        """Remove only the interpreter's cached previous semantic turn.

        The outer Harness session remains unchanged. This prevents a standalone
        request from being interpreted as a continuation/correction while preserving
        user-visible session identity for genuine dialogue flows.
        """
        reset = getattr(self.semantic_interpreter, "reset_session", None)
        if callable(reset):
            reset(session)
            return
        state = getattr(self.semantic_interpreter, "_last", None)
        if isinstance(state, dict):
            state.pop(session, None)

    def _clear_pending(self, session: str) -> None:
        """Discard only the current inner clarification state for an explicit rerun."""
        pending = getattr(self.inner, "_pending", None)
        if isinstance(pending, dict):
            pending.pop(session, None)

    async def _classify(self, current: str, previous_query: str) -> DialogueAct:
        classifier = getattr(self.semantic_interpreter, "classify_dialogue_act", None)
        if not callable(classifier):
            return DialogueAct("new")
        try:
            return await classifier(current, previous_query)
        except Exception:
            return DialogueAct("new")

    async def process(self, request: HarnessRequest) -> HarnessResponse:
        session = request.session_id or str(uuid.uuid4())
        current = (request.query or "").strip()
        previous = self._last.get(session)

        # If the user repeats the exact request that opened a clarification, treat it
        # as an explicit rerun of the original request, not as the answer to that
        # clarification. The pending clarification and stale semantic turn are both
        # cleared before the request is interpreted again.
        pending = getattr(self.inner, "_pending", None)
        if (
            previous is not None
            and isinstance(pending, dict)
            and session in pending
            and self._same_query(current, previous.query)
        ):
            self._clear_pending(session)
            self._clear_semantic_previous_turn(session)
            response = await self.inner.process(HarnessRequest(query=current, session_id=session))
            self._last[session] = _PreviousTurn(current, response)
            return response

        if isinstance(pending, dict) and session in pending:
            response = await self.inner.process(HarnessRequest(query=current, session_id=session))
            if response.status != ResponseStatus.NEEDS_CLARIFICATION:
                previous = self._last.get(session)
                self._last[session] = _PreviousTurn(previous.query if previous else current, response)
            return response

        if previous is None:
            response = await self.inner.process(HarnessRequest(query=current, session_id=session))
            self._last[session] = _PreviousTurn(current, response)
            return response

        # A literal repeat is not negative feedback and not a correction. Execute it
        # again from clean semantic context so the result does not depend on turn order.
        if self._same_query(current, previous.query):
            self._clear_semantic_previous_turn(session)
            response = await self.inner.process(HarnessRequest(query=current, session_id=session))
            self._last[session] = _PreviousTurn(current, response)
            return response

        act = await self._classify(current, previous.query)
        if act.act == "new":
            # NEW means the current turn is semantically independent. Do not leak the
            # previous semantic frame into the interpreter simply because the same
            # user-visible session is being reused.
            self._clear_semantic_previous_turn(session)
            response = await self.inner.process(HarnessRequest(query=current, session_id=session))
            self._last[session] = _PreviousTurn(current, response)
            return response

        started = time.perf_counter()
        # Reopen the previous evidence chain first. This also refreshes the
        # ConversationAwareSemanticInterpreter's previous_turn with the canonical
        # previous request before a correction is applied.
        rechecked = await self.inner.process(HarnessRequest(query=previous.query, session_id=session))

        if act.act == "correction" and act.specific_correction:
            # Pass only the user's correction in the SAME session. The semantic
            # interpreter receives previous_turn structurally from session state and
            # therefore merges slots without parsing an artificial combined sentence.
            corrected = await self.inner.process(HarnessRequest(query=current, session_id=session))
            self._attach_meta(
                corrected,
                previous_trace=previous.response.trace_id,
                recheck_trace=rechecked.trace_id,
                correction=current,
                act=act.act,
            )
            if "correction_recheck" not in corrected.warnings:
                corrected.warnings.append("correction_recheck")
            self._last[session] = _PreviousTurn(previous.query, corrected)
            return corrected

        question = act.clarification_question or (
            "Я заново перепроверил данные источника. Что именно нужно исправить в предыдущем запросе или результате?"
        )
        return HarnessResponse(
            status=ResponseStatus.NEEDS_CLARIFICATION,
            trace_id=str(uuid.uuid4()),
            session_id=session,
            question=question,
            clarification_id=f"{session}:semantic-correction",
            data={
                "_harness": {
                    "dialogue_state": "correction_clarification",
                    "correction": {
                        "dialogue_act": act.act,
                        "correction_text": current,
                        "previous_trace_id": previous.response.trace_id,
                        "recheck_trace_id": rechecked.trace_id,
                        "recheck_status": rechecked.status.value,
                        "source_recheck_performed": True,
                        "persistent_skill_mutation": False,
                        "semantic_state_reused": True,
                    },
                }
            },
            warnings=["negative_feedback", "source_rechecked", "clarification_required"],
            latency_ms=(time.perf_counter() - started) * 1000,
        )
