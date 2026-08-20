"""Dialogue correction/recheck wrapper for Harness.

An explicit user challenge is negative feedback about the previous execution,
not an unrelated query.  The wrapper forces a fresh execution first, then asks
only for unresolved semantic clarification.  It never changes global learned
semantics or promotes a skill from a single correction.
"""
from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass
from typing import Any

from .contracts import HarnessRequest, HarnessResponse, ResponseStatus

_CHALLENGE_RE = re.compile(
    r"(?:ты\s+не\s+прав|неверн|неправильн|проверь\s+(?:еще|ещё)\s+раз|перепроверь|"
    r"ты\s+потерял|ты\s+пропустил|я\s+имел(?:а)?\s+в\s+виду)",
    re.I,
)
_EXPLICIT_CORRECTION_RE = re.compile(
    r"(?:я\s+имел(?:а)?\s+в\s+виду|под\s+.+?\s+я\s+имел|точно\s+есть|"
    r"DMS-SPRNT-\d+|OLP-SPRNT-\d+|WMB-SPRNT-\d+|последн(?:ий|его)\s+заверш)",
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
    """Force evidence revalidation on negative feedback and retain session context."""

    def __init__(self, inner) -> None:
        self.inner = inner
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
    def _attach_correction_meta(response: HarnessResponse, *, previous_trace: str, recheck_trace: str, correction: str) -> None:
        if response.data is None or not isinstance(response.data, dict):
            response.data = {} if response.data is None else {"result": response.data}
        harness = response.data.setdefault("_harness", {})
        if not isinstance(harness, dict):
            harness = {}
            response.data["_harness"] = harness
        harness["correction"] = {
            "negative_feedback": True,
            "correction_text": correction,
            "previous_trace_id": previous_trace,
            "recheck_trace_id": recheck_trace,
            "source_recheck_performed": True,
            "persistent_skill_mutation": False,
        }

    async def _fresh_recheck(self, session: str, previous: _PreviousTurn) -> HarnessResponse:
        # Calling the inner runtime again is deliberate: DialogueHarnessRuntime
        # has no result cache, so grounding/source reads are reopened.
        return await self.inner.process(HarnessRequest(query=previous.query, session_id=session))

    async def process(self, request: HarnessRequest) -> HarnessResponse:
        session = request.session_id or str(uuid.uuid4())
        text = (request.query or "").strip()

        if session in self._pending and not self._is_challenge(text):
            pending = self._pending.pop(session)
            combined = f"{pending.original_query}\nУточнение пользователя: {text}"
            response = await self.inner.process(HarnessRequest(query=combined, session_id=session))
            self._attach_correction_meta(
                response,
                previous_trace=pending.previous_trace_id,
                recheck_trace=pending.recheck_trace_id,
                correction=text,
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
                self._attach_correction_meta(
                    corrected,
                    previous_trace=previous.response.trace_id,
                    recheck_trace=rechecked.trace_id,
                    correction=text,
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
                        },
                    }
                },
                warnings=["negative_feedback", "source_rechecked", "clarification_required"],
                latency_ms=(time.perf_counter() - started) * 1000,
            )
            return response

        response = await self.inner.process(HarnessRequest(query=request.query, session_id=session))
        # A clarification answer belongs to the current dialogue; do not replace
        # the remembered original request with a one-word answer.
        if response.status != ResponseStatus.NEEDS_CLARIFICATION or session not in self._last:
            self._last[session] = _PreviousTurn(text, response)
        return response
