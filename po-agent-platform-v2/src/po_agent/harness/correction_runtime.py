"""Dialogue correction/recheck wrapper with bounded persistent learning.

Explicit user challenges remain negative feedback about the previous execution,
not unrelated queries.  A correction is first revalidated against the real
source.  When the corrected execution is source-grounded, the runtime may
persist one allow-listed *behavioural* policy for that skill: authoritative
recheck before returning a future negative result.  It never memorises entity
facts and never edits Python, prompts or Skill Catalog at runtime.
"""
from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass
from typing import Any

from .contracts import HarnessRequest, HarnessResponse, ResponseStatus
from .learned_policy import LearnedPolicy, LearnedPolicyStore

_CHALLENGE_RE = re.compile(
    r"(?:ты\s+не\s+прав|неверн|неправильн|проверь\s+(?:еще|ещё)\s+раз|перепроверь|"
    r"ты\s+потерял|ты\s+пропустил|я\s+имел(?:а)?\s+в\s+виду)",
    re.I,
)
_EXPLICIT_CORRECTION_RE = re.compile(
    r"(?:я\s+имел(?:а)?\s+в\s+виду|под\s+.+?\s+я\s+имел|точно\s+есть|"
    r"существует|есть\s+такая|DMS-SPRNT-\d+|OLP-SPRNT-\d+|WMB-SPRNT-\d+|последн(?:ий|его)\s+заверш)",
    re.I,
)
_NEGATIVE_WARNING_RE = re.compile(
    r"(?:not_found|entity_not_found|source_capability_unavailable|missing_source_fact|empty|no_data|unavailable)",
    re.I,
)


@dataclass
class _PreviousTurn:
    query: str
    response: HarnessResponse


@dataclass
class _CorrectionPending:
    original_query: str
    previous_trace_id: str
    recheck_trace_id: str
    recheck_status: str


class CorrectionAwareHarnessRuntime:
    """Revalidate negative feedback and learn bounded cross-session policies."""

    def __init__(self, inner, *, learned_policy_store: LearnedPolicyStore | None = None) -> None:
        self.inner = inner
        self.learned_policy_store = learned_policy_store or LearnedPolicyStore()
        self._last: dict[str, _PreviousTurn] = {}
        self._pending: dict[str, _CorrectionPending] = {}
        for name in ("adapter", "router", "capabilities", "skills"):
            if hasattr(inner, name):
                setattr(self, name, getattr(inner, name))

    @staticmethod
    def _is_challenge(text: str) -> bool:
        return bool(_CHALLENGE_RE.search(text or ""))

    @staticmethod
    def _targeted_question(original: str) -> str:
        questions: list[str] = []
        low = original.casefold()
        if "открыт" in low or "незакрыт" in low:
            questions.append("что считать «открытыми»: только статус Open или все незавершённые статусы")
        if "последн" in low and "спринт" in low:
            questions.append("что считать «последним спринтом»: текущий активный или последний завершённый")
        if questions:
            return "Я заново перепроверил источник. Уточните, пожалуйста, " + "; и ".join(questions) + "."
        return "Я заново перепроверил источник. Что именно в результате нужно уточнить: сущность, период/спринт, статус или состав найденных задач?"

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
        warning_text = " ".join(response.warnings or [])
        if _NEGATIVE_WARNING_RE.search(warning_text):
            return True
        answer = (response.answer or "").casefold()
        return any(marker in answer for marker in ("не найден", "нет данных", "недоступ", "не удалось найти"))

    @staticmethod
    def _attach_correction_meta(
        response: HarnessResponse,
        *,
        previous_trace: str,
        recheck_trace: str,
        correction: str,
        learned_policy: LearnedPolicy | None = None,
    ) -> None:
        if response.data is None or not isinstance(response.data, dict):
            response.data = {} if response.data is None else {"result": response.data}
        harness = response.data.setdefault("_harness", {})
        if not isinstance(harness, dict):
            harness = {}
            response.data["_harness"] = harness
        correction_meta: dict[str, Any] = {
            "negative_feedback": True,
            "correction_text": correction,
            "previous_trace_id": previous_trace,
            "recheck_trace_id": recheck_trace,
            "source_recheck_performed": True,
            "persistent_skill_mutation": False,
            "persistent_behavior_learning": learned_policy is not None,
        }
        if learned_policy is not None:
            correction_meta["learned_policy"] = {
                "policy_id": learned_policy.policy_id,
                "skill_id": learned_policy.skill_id,
                "behaviour": learned_policy.behaviour,
                "version": learned_policy.version,
                "state": learned_policy.state,
                "entity_fact_persisted": False,
            }
        harness["correction"] = correction_meta

    @staticmethod
    def _attach_learning_application(response: HarnessResponse, policy: LearnedPolicy, first_trace_id: str) -> None:
        if response.data is None or not isinstance(response.data, dict):
            response.data = {} if response.data is None else {"result": response.data}
        harness = response.data.setdefault("_harness", {})
        if not isinstance(harness, dict):
            harness = {}
            response.data["_harness"] = harness
        harness["learning"] = {
            "policy_id": policy.policy_id,
            "skill_id": policy.skill_id,
            "behaviour": policy.behaviour,
            "version": policy.version,
            "state": policy.state,
            "first_attempt_trace_id": first_trace_id,
            "recheck_trace_id": response.trace_id,
            "policy_applied": True,
        }
        if "learned_policy_applied" not in response.warnings:
            response.warnings.append("learned_policy_applied")

    def _learn_from_grounded_correction(
        self,
        *,
        previous: HarnessResponse,
        validated: HarnessResponse,
    ) -> LearnedPolicy | None:
        """Persist a general policy, never the corrected entity/answer itself."""
        skill_id = self._skill_key(validated) or self._skill_key(previous)
        if not skill_id or not self._is_grounded(validated):
            return None
        # A correction is a valid promotion signal only when it disproves or
        # materially improves a negative/ungrounded prior execution.
        if not self._looks_negative(previous) and previous.answer == validated.answer:
            return None
        return self.learned_policy_store.promote_grounded_recheck(
            skill_id=skill_id,
            correction_trace_id=previous.trace_id,
            validation_trace_id=validated.trace_id,
            evidence_count=len(validated.evidence),
        )

    async def _fresh_recheck(self, session: str, previous: _PreviousTurn) -> HarnessResponse:
        # Calling the inner runtime again is deliberate: DialogueHarnessRuntime
        # has no result cache, so grounding/source reads are reopened.
        return await self.inner.process(HarnessRequest(query=previous.query, session_id=session))

    async def _apply_learned_policy(
        self,
        *,
        request: HarnessRequest,
        session: str,
        response: HarnessResponse,
    ) -> HarnessResponse:
        """Apply promoted policy only to future negative results for same skill."""
        skill_id = self._skill_key(response)
        policy = self.learned_policy_store.active_for(skill_id)
        if policy is None or not self._looks_negative(response):
            return response
        if policy.behaviour != "authoritative_recheck_on_negative":
            return response
        first_trace = response.trace_id
        rechecked = await self.inner.process(HarnessRequest(query=request.query, session_id=session))
        # Never replace a source-grounded result by a weaker retry.  Otherwise
        # return the retry so a recovered authoritative read reaches the user.
        chosen = rechecked if self._is_grounded(rechecked) or not self._is_grounded(response) else response
        self._attach_learning_application(chosen, policy, first_trace)
        return chosen

    async def process(self, request: HarnessRequest) -> HarnessResponse:
        session = request.session_id or str(uuid.uuid4())
        text = (request.query or "").strip()

        if session in self._pending and not self._is_challenge(text):
            pending = self._pending.pop(session)
            previous = self._last.get(session)
            combined = f"{pending.original_query}\nУточнение пользователя: {text}"
            response = await self.inner.process(HarnessRequest(query=combined, session_id=session))
            learned = self._learn_from_grounded_correction(
                previous=previous.response if previous else response,
                validated=response,
            )
            self._attach_correction_meta(
                response,
                previous_trace=pending.previous_trace_id,
                recheck_trace=pending.recheck_trace_id,
                correction=text,
                learned_policy=learned,
            )
            self._last[session] = _PreviousTurn(pending.original_query, response)
            return response

        if self._is_challenge(text) and session in self._last:
            previous = self._last[session]
            started = time.perf_counter()
            rechecked = await self._fresh_recheck(session, previous)

            if _EXPLICIT_CORRECTION_RE.search(text):
                combined = f"{previous.query}\nУточнение/исправление пользователя: {text}"
                corrected = await self.inner.process(HarnessRequest(query=combined, session_id=session))
                learned = self._learn_from_grounded_correction(previous=previous.response, validated=corrected)
                self._attach_correction_meta(
                    corrected,
                    previous_trace=previous.response.trace_id,
                    recheck_trace=rechecked.trace_id,
                    correction=text,
                    learned_policy=learned,
                )
                if "correction_recheck" not in corrected.warnings:
                    corrected.warnings.append("correction_recheck")
                self._last[session] = _PreviousTurn(previous.query, corrected)
                return corrected

            pending = _CorrectionPending(
                original_query=previous.query,
                previous_trace_id=previous.response.trace_id,
                recheck_trace_id=rechecked.trace_id,
                recheck_status=rechecked.status.value,
            )
            self._pending[session] = pending
            response = HarnessResponse(
                status=ResponseStatus.NEEDS_CLARIFICATION,
                trace_id=str(uuid.uuid4()),
                session_id=session,
                question=self._targeted_question(previous.query),
                clarification_id=f"{session}:correction",
                data={
                    "_harness": {
                        "dialogue_state": "correction_clarification",
                        "correction": {
                            "negative_feedback": True,
                            "correction_text": text,
                            "previous_trace_id": previous.response.trace_id,
                            "recheck_trace_id": rechecked.trace_id,
                            "recheck_status": rechecked.status.value,
                            "source_recheck_performed": True,
                            "persistent_skill_mutation": False,
                            "persistent_behavior_learning": False,
                        },
                    }
                },
                warnings=["negative_feedback", "source_rechecked", "clarification_required"],
                latency_ms=(time.perf_counter() - started) * 1000,
            )
            return response

        response = await self.inner.process(HarnessRequest(query=request.query, session_id=session))
        response = await self._apply_learned_policy(request=request, session=session, response=response)
        # A clarification answer belongs to the current dialogue; do not replace
        # the remembered original request with a one-word answer.
        if response.status != ResponseStatus.NEEDS_CLARIFICATION or session not in self._last:
            self._last[session] = _PreviousTurn(text, response)
        return response
