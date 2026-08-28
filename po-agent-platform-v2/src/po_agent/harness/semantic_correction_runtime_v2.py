"""Meaning-based correction/recheck runtime for production Harness.

Corrections are interpreted in the same conversation session against the previous
canonical semantic state. The runtime never creates a synthetic natural-language
mega-query, which previously allowed the model to lose or duplicate filters.

Source-grounded corrections can promote one bounded behavioural learning policy:
``authoritative_recheck_on_negative``.  The policy is persisted outside the
skill/catalog code, applies to later requests for the same skill, survives a
process restart and can be rolled back through ``LearnedPolicyStore``.  Entity
facts and user-provided answers are never persisted as learned truths.
"""
from __future__ import annotations

import copy
import time
import uuid
from dataclasses import dataclass
from typing import Any

from .contracts import HarnessRequest, HarnessResponse, ResponseStatus
from .learned_policy import LearnedPolicy, LearnedPolicyStore
from .semantic_core_v2 import DialogueAct


@dataclass
class _PreviousTurn:
    query: str
    response: HarnessResponse


class SemanticCorrectionRuntimeV2:
    def __init__(
        self,
        inner,
        semantic_interpreter,
        *,
        learned_policy_store: LearnedPolicyStore | None = None,
    ) -> None:
        self.inner = inner
        self.semantic_interpreter = semantic_interpreter
        self.learned_policy_store = learned_policy_store or LearnedPolicyStore()
        self._last: dict[str, _PreviousTurn] = {}
        for name in ("adapter", "router", "capabilities", "skills"):
            if hasattr(inner, name):
                setattr(self, name, getattr(inner, name))

    @staticmethod
    def _skill_key(response: HarnessResponse) -> str | None:
        return response.skill_id or response.intent

    @staticmethod
    def _is_grounded(response: HarnessResponse) -> bool:
        return response.status == ResponseStatus.COMPLETED and len(response.evidence) > 0

    @staticmethod
    def _looks_negative(response: HarnessResponse) -> bool:
        if response.status in {ResponseStatus.FAILED, ResponseStatus.PARTIAL}:
            return True
        warning_text = " ".join(response.warnings or []).casefold()
        if any(
            marker in warning_text
            for marker in (
                "not_found",
                "entity_not_found",
                "source_capability_unavailable",
                "missing_source_fact",
                "no_data",
                "unavailable",
                "empty",
            )
        ):
            return True
        answer = (response.answer or "").casefold()
        return any(marker in answer for marker in ("не найден", "нет данных", "недоступ", "не удалось найти"))

    @staticmethod
    def _ensure_harness_meta(response: HarnessResponse) -> dict[str, Any]:
        if response.data is None or not isinstance(response.data, dict):
            response.data = {} if response.data is None else {"result": response.data}
        meta = response.data.setdefault("_harness", {})
        if not isinstance(meta, dict):
            meta = {}
            response.data["_harness"] = meta
        return meta

    @classmethod
    def _attach_meta(
        cls,
        response: HarnessResponse,
        *,
        previous_trace: str,
        recheck_trace: str,
        correction: str,
        act: str,
        learned_policy: LearnedPolicy | None = None,
    ) -> None:
        meta = cls._ensure_harness_meta(response)
        correction_meta: dict[str, Any] = {
            "dialogue_act": act,
            "correction_text": correction,
            "previous_trace_id": previous_trace,
            "recheck_trace_id": recheck_trace,
            "source_recheck_performed": True,
            "persistent_skill_mutation": False,
            "persistent_behavior_learning": learned_policy is not None,
            "semantic_state_reused": True,
        }
        if learned_policy is not None:
            correction_meta["learned_policy"] = {
                "policy_id": learned_policy.policy_id,
                "skill_id": learned_policy.skill_id,
                "behaviour": learned_policy.behaviour,
                "version": learned_policy.version,
                "state": learned_policy.state,
                "entity_fact_persisted": False,
                "evidence_count": learned_policy.evidence_count,
            }
        meta["correction"] = correction_meta

    @classmethod
    def _attach_learning_application(
        cls,
        response: HarnessResponse,
        policy: LearnedPolicy,
        *,
        first_trace_id: str,
    ) -> None:
        meta = cls._ensure_harness_meta(response)
        meta["learning"] = {
            "policy_id": policy.policy_id,
            "skill_id": policy.skill_id,
            "behaviour": policy.behaviour,
            "version": policy.version,
            "state": policy.state,
            "first_attempt_trace_id": first_trace_id,
            "recheck_trace_id": response.trace_id,
            "policy_applied": True,
            "entity_fact_persisted": False,
        }
        if "learned_policy_applied" not in response.warnings:
            response.warnings.append("learned_policy_applied")

    def _learn_from_grounded_correction(
        self,
        *,
        previous: HarnessResponse,
        validated: HarnessResponse,
    ) -> LearnedPolicy | None:
        """Promote a generalized behaviour only after authoritative evidence.

        A positive correction does not cause entity memorisation.  Promotion is
        allowed only when the corrected execution is source-grounded and the prior
        execution was negative/ungrounded or materially different.
        """
        skill_id = self._skill_key(validated) or self._skill_key(previous)
        if not skill_id or not self._is_grounded(validated):
            return None
        if not self._looks_negative(previous) and previous.answer == validated.answer:
            return None
        return self.learned_policy_store.promote_grounded_recheck(
            skill_id=skill_id,
            correction_trace_id=previous.trace_id,
            validation_trace_id=validated.trace_id,
            evidence_count=len(validated.evidence),
        )

    async def _apply_learned_policy(
        self,
        *,
        request: HarnessRequest,
        session: str,
        response: HarnessResponse,
    ) -> HarnessResponse:
        """Re-open authoritative execution before returning a learned negative."""
        skill_id = self._skill_key(response)
        policy = self.learned_policy_store.active_for(skill_id)
        if policy is None or policy.behaviour != "authoritative_recheck_on_negative":
            return response
        if not self._looks_negative(response):
            return response

        first_trace = response.trace_id
        # Clear semantic conversation cache so this is a fresh authoritative
        # execution of the current request, not a correction of the prior frame.
        self._clear_semantic_previous_turn(session)
        rechecked = await self.inner.process(HarnessRequest(query=request.query, session_id=session))
        chosen = rechecked if self._is_grounded(rechecked) or not self._is_grounded(response) else response
        self._attach_learning_application(chosen, policy, first_trace_id=first_trace)
        return chosen

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
            act = await classifier(current, previous_query)
        except Exception:
            return DialogueAct("new")
        # Contract hardening: the classifier contract defines `correction` as a
        # semantic replacement/change and `recheck` as a generic challenge.  Some
        # LLM backends have nevertheless emitted `specific_correction: null`, which
        # is parsed as False and silently bypasses the correction/learning path.
        # Once the act itself is `correction`, treat it as specific; a non-specific
        # challenge must be classified as `recheck` and therefore remains safe.
        if act.act == "correction" and not act.specific_correction:
            return DialogueAct("correction", True, act.clarification_question)
        return act

    @staticmethod
    def _replay_clarification(previous: _PreviousTurn, session: str) -> HarnessResponse:
        """Replay an already-open clarification without consuming or recomputing it."""
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

        if (
            previous is not None
            and previous.response.status == ResponseStatus.NEEDS_CLARIFICATION
            and isinstance(pending, dict)
            and session in pending
            and self._same_query(current, previous.query)
        ):
            return self._replay_clarification(previous, session)

        if isinstance(pending, dict) and session in pending:
            response = await self.inner.process(HarnessRequest(query=current, session_id=session))
            if response.status != ResponseStatus.NEEDS_CLARIFICATION:
                previous = self._last.get(session)
                self._last[session] = _PreviousTurn(previous.query if previous else current, response)
            return response

        if previous is None:
            response = await self.inner.process(HarnessRequest(query=current, session_id=session))
            response = await self._apply_learned_policy(request=request, session=session, response=response)
            self._last[session] = _PreviousTurn(current, response)
            return response

        if self._same_query(current, previous.query):
            self._clear_semantic_previous_turn(session)
            response = await self.inner.process(HarnessRequest(query=current, session_id=session))
            response = await self._apply_learned_policy(request=request, session=session, response=response)
            self._last[session] = _PreviousTurn(current, response)
            return response

        act = await self._classify(current, previous.query)
        if act.act == "new":
            self._clear_semantic_previous_turn(session)
            response = await self.inner.process(HarnessRequest(query=current, session_id=session))
            response = await self._apply_learned_policy(request=request, session=session, response=response)
            self._last[session] = _PreviousTurn(current, response)
            return response

        started = time.perf_counter()
        rechecked = await self.inner.process(HarnessRequest(query=previous.query, session_id=session))

        if act.act == "correction" and act.specific_correction:
            corrected = await self.inner.process(HarnessRequest(query=current, session_id=session))
            learned = self._learn_from_grounded_correction(previous=previous.response, validated=corrected)
            self._attach_meta(
                corrected,
                previous_trace=previous.response.trace_id,
                recheck_trace=rechecked.trace_id,
                correction=current,
                act=act.act,
                learned_policy=learned,
            )
            if "correction_recheck" not in corrected.warnings:
                corrected.warnings.append("correction_recheck")
            if learned is not None and "learned_policy_promoted" not in corrected.warnings:
                corrected.warnings.append("learned_policy_promoted")
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
                        "persistent_behavior_learning": False,
                        "semantic_state_reused": True,
                    },
                }
            },
            warnings=["negative_feedback", "source_rechecked", "clarification_required"],
            latency_ms=(time.perf_counter() - started) * 1000,
        )
