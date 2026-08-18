"""Session-scoped correction memory for the dialogue Harness.

Explicit user corrections may change subsequent interpretation inside the same
session, but they never mutate Skills, learned global semantics, AS21, or the
production promotion path.  The store is intentionally in-memory and bounded to
one runtime process/session.
"""
from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from .contracts import HarnessRequest, HarnessResponse, ResponseStatus
from .dialogue_runtime import SemanticFrame, SemanticInterpreter
from .semantic_authorization import IntentPreservingDialogueHarnessRuntime


_LOGIN_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9_-]*(?:\.[A-Za-z0-9_-]+)+\b")
_NOT_A_RE = re.compile(r"\bне\s+([^,.;]+?)\s*,?\s+а\s+([^,.;]+)", re.I)
_NUZHEN_A_NE_RE = re.compile(r"\b(?:нужен|нужна|нужно|нужны)\s+([^,.;]+?)\s*,?\s+а\s+не\s+([^,.;]+)", re.I)
_EN_NOT_BUT_RE = re.compile(r"\bnot\s+([^,.;]+?)\s*,?\s+but\s+([^,.;]+)", re.I)


@dataclass(frozen=True)
class SessionCorrection:
    correction_id: str
    session_id: str
    kind: str
    expected_value: str
    incorrect_value: str | None
    source_trace_id: str
    source_query: str
    corrected_query: str
    slot_overrides: dict[str, str] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


class SessionCorrectionStore:
    """Small fail-closed session memory; no persistence and no cross-session reads."""

    def __init__(self, *, max_per_session: int = 16) -> None:
        if max_per_session <= 0:
            raise ValueError("max_per_session must be positive")
        self.max_per_session = max_per_session
        self._items: dict[str, list[SessionCorrection]] = {}

    def append(self, correction: SessionCorrection) -> SessionCorrection:
        bucket = self._items.setdefault(correction.session_id, [])
        bucket.append(correction)
        if len(bucket) > self.max_per_session:
            del bucket[: len(bucket) - self.max_per_session]
        return correction

    def for_session(self, session_id: str) -> tuple[SessionCorrection, ...]:
        return tuple(self._items.get(session_id, ()))

    def effective_overrides(self, session_id: str) -> dict[str, str]:
        merged: dict[str, str] = {}
        for item in self._items.get(session_id, ()):
            merged.update(item.slot_overrides)
        return merged

    def clear(self, session_id: str) -> None:
        self._items.pop(session_id, None)


class SessionCorrectionSemanticInterpreter:
    """Apply trusted, structured session overrides after semantic interpretation.

    Corrections are not concatenated into the LLM prompt.  This avoids turning
    arbitrary feedback text into hidden instructions and keeps the overlay
    deterministic and auditable.
    """

    def __init__(self, delegate: SemanticInterpreter, store: SessionCorrectionStore) -> None:
        self.delegate = delegate
        self.store = store

    async def interpret(self, query: str, *, context: dict[str, Any] | None = None) -> SemanticFrame:
        frame = await self.delegate.interpret(query, context=context)
        session_id = str((context or {}).get("session_id") or "")
        overrides = self.store.effective_overrides(session_id) if session_id else {}
        if not overrides:
            return frame

        slots = dict(frame.slots)
        slots.update(overrides)
        # A corrected assignee is authoritative for this session.  Remove raw
        # person ambiguity so grounding cannot silently replace it again.
        if "member_login" in overrides or "assignee" in overrides:
            slots.pop("person_raw", None)
        return SemanticFrame(
            canonical_query=frame.canonical_query,
            intent_hint=frame.intent_hint,
            slots=slots,
            clarifications=[need for need in frame.clarifications if need.field not in overrides],
            confidence=max(frame.confidence, 0.85),
            llm_used=frame.llm_used,
        )


class SessionCorrectionDialogueHarnessRuntime(IntentPreservingDialogueHarnessRuntime):
    """Dialogue runtime that learns explicit corrections only inside a session."""

    def __init__(self, *args, correction_store: SessionCorrectionStore | None = None, **kwargs) -> None:
        self.correction_store = correction_store or SessionCorrectionStore()
        interpreter = kwargs.get("interpreter")
        if interpreter is not None and not isinstance(interpreter, SessionCorrectionSemanticInterpreter):
            kwargs["interpreter"] = SessionCorrectionSemanticInterpreter(interpreter, self.correction_store)
        super().__init__(*args, **kwargs)
        # ConservativeSemanticInterpreter is created by the parent when no
        # interpreter is supplied; wrap it after construction in that case.
        if not isinstance(self.interpreter, SessionCorrectionSemanticInterpreter):
            self.interpreter = SessionCorrectionSemanticInterpreter(self.interpreter, self.correction_store)
        self._last_user_query: dict[str, str] = {}
        self._last_trace_id: dict[str, str] = {}

    @staticmethod
    def _looks_like_correction(text: str) -> bool:
        low = text.casefold()
        markers = (
            "ты вывел", "ты показал", "неправильно", "ошиб", "исправ", "а не",
            "you returned", "you showed", "wrong", "incorrect", "not ",
        )
        return any(marker in low for marker in markers)

    @staticmethod
    def _contrast_values(text: str) -> tuple[str | None, str | None]:
        """Return (expected, incorrect) where explicit contrast is available."""
        match = _NUZHEN_A_NE_RE.search(text)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        match = _NOT_A_RE.search(text)
        if match:
            # Russian feedback such as "ты вывел задачи не Каланчанова, а Иванова"
            # means the first entity was requested and the second was observed.
            return match.group(1).strip(), match.group(2).strip()
        match = _EN_NOT_BUT_RE.search(text)
        if match:
            # English "not X but Y" conventionally means Y is expected.
            return match.group(2).strip(), match.group(1).strip()
        return None, None

    def _capture_correction(self, session_id: str, text: str) -> SessionCorrection | None:
        previous = self._last_user_query.get(session_id)
        if not previous or not self._looks_like_correction(text):
            return None

        expected, incorrect = self._contrast_values(text)
        previous_logins = _LOGIN_RE.findall(previous)
        overrides: dict[str, str] = {}
        expected_value = (expected or "").strip()

        # If the immediately preceding request contained one explicit corporate
        # login, preserve that exact identifier.  It is safer than inventing a
        # login from an inflected human name in the correction utterance.
        if len(previous_logins) == 1:
            expected_value = previous_logins[0]
            overrides["member_login"] = expected_value
            overrides["assignee"] = expected_value
        elif expected_value:
            # Preserve raw person wording for grounding; do not pretend a display
            # name is already a source login.
            overrides["person_raw"] = expected_value

        if not overrides:
            return None

        return self.correction_store.append(
            SessionCorrection(
                correction_id=str(uuid.uuid4()),
                session_id=session_id,
                kind="entity_resolution",
                expected_value=expected_value,
                incorrect_value=incorrect,
                source_trace_id=self._last_trace_id.get(session_id, ""),
                source_query=previous,
                corrected_query=text.strip(),
                slot_overrides=overrides,
            )
        )

    async def process(self, request: HarnessRequest) -> HarnessResponse:
        session = request.session_id or str(uuid.uuid4())
        text = (request.query or "").strip()
        correction = self._capture_correction(session, text) if text else None
        if correction is not None:
            trace = str(uuid.uuid4())
            self._last_trace_id[session] = trace
            return HarnessResponse(
                status=ResponseStatus.COMPLETED,
                trace_id=trace,
                session_id=session,
                answer="Исправление учтено в текущей сессии. Повторите запрос — я применю его без изменения глобальных навыков.",
                data={
                    "session_correction": {
                        "id": correction.correction_id,
                        "kind": correction.kind,
                        "expected_value": correction.expected_value,
                        "incorrect_value": correction.incorrect_value,
                        "scope": "session",
                        "slot_overrides": dict(correction.slot_overrides),
                    },
                    "_harness": {
                        "session_correction_captured": True,
                        "production_skill_changed": False,
                        "global_semantics_changed": False,
                    },
                },
                warnings=[],
            )

        response = await super().process(
            HarnessRequest(query=request.query, session_id=session)
        )
        self._last_user_query[session] = text
        self._last_trace_id[session] = response.trace_id
        if isinstance(response.data, dict):
            meta = response.data.setdefault("_harness", {})
            if isinstance(meta, dict):
                applied = self.correction_store.effective_overrides(session)
                meta["session_correction_applied"] = bool(applied)
                if applied:
                    meta["session_correction_overrides"] = dict(applied)
        return response
