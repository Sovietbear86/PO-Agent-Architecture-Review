"""Meaning-based correction/recheck runtime for production Harness.

Corrections are interpreted in the same conversation session against the previous
canonical semantic state. The runtime never creates a synthetic natural-language
mega-query, which previously allowed the model to lose or duplicate filters.
"""
from __future__ import annotations

import copy
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
        """Treat an exact natural-language repeat as an idempotent rerun."""
        normalize = lambda value: " ".join((value or "").split()).casefold()
        return bool(normalize(current)) and normalize(current) == normalize(previous)

    def _clear_semantic_previous_turn(self, session: str) -> None:
        """Remove only the interpreter's cached previous semantic turn."""
        reset = getattr(self.semantic_interpreter, "reset_session", None)
        if callable(reset):
            reset(session)
            return
        state = getattr(self.semantic_interpreter, "_last", None)
        if isinstance(state, dict):
            state.pop(session, None)

    async def _classify(self, current: str, previous_query: str) -> DialogueAct:
        classifier = getattr(self.semantic_interpreter, "classify_dialogue_act", None)
        if not callable(classifier):
            return DialogueAct("new")
        try:
            return await classifier(current, previous_query)
        except Exception:
            return DialogueAct("new")

    @staticmethod
    def _replay_clarification(previous: _PreviousTurn, session: str) -> HarnessResponse:
        """Replay an already-open clarification without consuming or recomputing it.

        Exact repetition of the request that opened a clarification is not an
        answer to that clarification. Re-running semantic interpretation here would
        also reintroduce LLM stochasticity and could mutate otherwise grounded slots.
        Return a defensive copy of the accepted clarification state instead.
        """
        response = copy.deepcopy(previous.response)
        response.trace_id = str(uuid.uuid4())
        response.session_id = session
        if "clarification_replay" not in response.warnings:
            response.warnings.append("clarification_replay")
        return response

    async def process(self, request: HarnessRequest) -> HarnessResponse:
        session = request.session_id or str(uuid.uuid4())
        current = (request.query or "").strip()
        previous = self._last.get(session)

        pending = getattr(self.inner, "_pending", None)

        # Exact replay of the request that opened the active clarification is a
        # deterministic replay of that clarification. Never consume it as the user's
        # answer and never call the semantic model/grounder again.
        if (
            previous is not None
            and previous.response.status == ResponseStatus.NEEDS_CLARIFICATION
            and isinstance(pending, dict)
            and session in pending
            and self._same_query(current, previous.query)
        ):
            return self._replay_clarification(previous, session)

        # Any other message while a clarification is pending is the user's answer to
        # that clarification and must be delegated to DialogueHarnessRuntime.
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

        # A literal repeat after a completed/failed standalone request is not negative
        # feedback and not a correction. Execute it again from clean semantic context.
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
        # Reopen the previous evidence chain first. This refreshes semantic previous
        # turn for an actual correction/recheck only.
        rechecked = await self.inner.process(HarnessRequest(query=previous.query, session_id=session))

        if act.act == "correction" and act.specific_correction:
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
