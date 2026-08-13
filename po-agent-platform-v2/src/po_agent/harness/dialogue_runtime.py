"""Dialogue-first Harness orchestration.

Natural language understanding is intentionally separated from deterministic
capabilities. An LLM may interpret language and propose a semantic frame, but it
may not invent source entities or calculate business metrics. Ambiguities are
resolved through explicit user clarification before execution.
"""
from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Protocol, Any

from po_agent.llm.client import LLMClient, LLMMessage

from .contracts import HarnessRequest, HarnessResponse, ResponseStatus


@dataclass(frozen=True)
class ClarificationNeed:
    field: str
    question: str
    options: tuple[str, ...] = ()


@dataclass
class SemanticFrame:
    canonical_query: str
    intent_hint: str | None = None
    slots: dict[str, str] = field(default_factory=dict)
    clarifications: list[ClarificationNeed] = field(default_factory=list)
    confidence: float = 1.0
    llm_used: bool = False


class SemanticInterpreter(Protocol):
    async def interpret(self, query: str, *, context: dict[str, Any] | None = None) -> SemanticFrame: ...


class LLMJsonSemanticInterpreter:
    """Strict JSON semantic interpreter suitable for Qwen/Qwen-Coder class models.

    The model is allowed to interpret wording only. It must surface uncertainty
    as clarifications and must not fabricate task/sprint/member identifiers.
    """

    SYSTEM = """You are the semantic interpreter of a PO Harness agent.
Return JSON only with keys canonical_query, intent_hint, slots, clarifications, confidence.
clarifications is an array of {field, question, options}.
Rules:
1. Understand free-form Russian/English wording, names, grammatical cases and shorthand.
2. NEVER invent task IDs, sprint IDs, release IDs, logins, statuses or source facts.
3. If an entity or business term is ambiguous, add a clarification instead of guessing.
4. canonical_query must preserve the user's requested operation and only use values explicitly supplied or resolved in context.
5. Do not calculate metrics; deterministic capabilities do that after interpretation.
6. For phrases such as 'open tasks', if context does not define the term, clarify its status semantics.
"""

    def __init__(self, client: LLMClient, *, model: str | None = None) -> None:
        self.client = client
        self.model = model

    async def interpret(self, query: str, *, context: dict[str, Any] | None = None) -> SemanticFrame:
        payload = json.dumps({"query": query, "context": context or {}}, ensure_ascii=False)
        response = await self.client.complete(
            [LLMMessage(role="system", content=self.SYSTEM), LLMMessage(role="user", content=payload)],
            model=self.model,
            temperature=0.0,
            max_tokens=900,
        )
        if not response.choices:
            raise ValueError("semantic interpreter returned no choices")
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.I | re.S)
        data = json.loads(raw)
        if not isinstance(data, dict) or not isinstance(data.get("canonical_query"), str):
            raise ValueError("semantic interpreter contract violation")
        needs = []
        for item in data.get("clarifications", []) or []:
            if not isinstance(item, dict) or not item.get("field") or not item.get("question"):
                continue
            needs.append(ClarificationNeed(str(item["field"]), str(item["question"]), tuple(str(x) for x in item.get("options", []) if x)))
        return SemanticFrame(
            canonical_query=data["canonical_query"].strip() or query,
            intent_hint=str(data.get("intent_hint")) if data.get("intent_hint") else None,
            slots={str(k): str(v) for k, v in (data.get("slots") or {}).items() if v is not None},
            clarifications=needs,
            confidence=float(data.get("confidence", 1.0)),
            llm_used=True,
        )


class ConservativeSemanticInterpreter:
    """Hermetic fallback, not the primary production NLP layer.

    It performs only high-confidence normalization and otherwise lets the
    deterministic runtime handle the query. No FIO declension tables are kept.
    """

    async def interpret(self, query: str, *, context: dict[str, Any] | None = None) -> SemanticFrame:
        text = query.strip()
        low = text.casefold()
        # One safe normalization fixes grammatical variants without enumerating
        # complete phrase dictionaries; production should use LLMJsonSemanticInterpreter.
        if "истор" in low and re.search(r"\b[A-ZА-Я][A-ZА-Я0-9_]{1,15}-\d+\b", text, re.I):
            key = re.search(r"\b[A-ZА-Я][A-ZА-Я0-9_]{1,15}-\d+\b", text, re.I).group(0)
            text = f"история {key}"
        return SemanticFrame(canonical_query=text, confidence=0.7, llm_used=False)


@dataclass
class _PendingDialogue:
    frame: SemanticFrame
    remaining: list[ClarificationNeed]
    answers: dict[str, str] = field(default_factory=dict)


class DialogueHarnessRuntime:
    """Stateful semantic/clarification layer over an executable Harness runtime."""

    def __init__(self, inner, interpreter: SemanticInterpreter | None = None) -> None:
        self.inner = inner
        self.interpreter = interpreter or ConservativeSemanticInterpreter()
        self._pending: dict[str, _PendingDialogue] = {}
        for name in ("adapter", "router", "capabilities", "skills"):
            setattr(self, name, getattr(inner, name))

    @staticmethod
    def _clarification_response(session: str, pending: _PendingDialogue) -> HarnessResponse:
        need = pending.remaining[0]
        return HarnessResponse(
            status=ResponseStatus.NEEDS_CLARIFICATION,
            trace_id=str(uuid.uuid4()),
            session_id=session,
            question=need.question,
            options=list(need.options),
            clarification_id=f"{session}:{need.field}",
            data={"missing_field": need.field, "semantic_frame": pending.frame.slots},
            warnings=["clarification_required"],
        )

    @staticmethod
    def _apply_answers(frame: SemanticFrame, answers: dict[str, str]) -> str:
        query = frame.canonical_query
        for field, value in answers.items():
            token = "{" + field + "}"
            if token in query:
                query = query.replace(token, value)
            elif value and value.casefold() not in query.casefold():
                query = f"{query} {value}"
        return query

    async def process(self, request: HarnessRequest) -> HarnessResponse:
        session = request.session_id or str(uuid.uuid4())
        started = time.perf_counter()

        if session in self._pending:
            pending = self._pending[session]
            need = pending.remaining.pop(0)
            answer = request.query.strip()
            if not answer:
                pending.remaining.insert(0, need)
                return self._clarification_response(session, pending)
            pending.answers[need.field] = answer
            pending.frame.slots[need.field] = answer
            if pending.remaining:
                return self._clarification_response(session, pending)
            self._pending.pop(session, None)
            effective = HarnessRequest(query=self._apply_answers(pending.frame, pending.answers), session_id=session)
            response = await self.inner.process(effective)
            self._decorate(response, pending.frame.llm_used)
            return response

        frame = await self.interpreter.interpret(request.query, context={"session_id": session})
        if frame.clarifications:
            pending = _PendingDialogue(frame=frame, remaining=list(frame.clarifications))
            self._pending[session] = pending
            return self._clarification_response(session, pending)

        response = await self.inner.process(HarnessRequest(query=frame.canonical_query, session_id=session))
        self._decorate(response, frame.llm_used)
        response.latency_ms = max(response.latency_ms, (time.perf_counter() - started) * 1000)
        return response

    @staticmethod
    def _decorate(response: HarnessResponse, llm_used: bool) -> None:
        if response.data is None:
            response.data = {}
        if isinstance(response.data, dict):
            meta = response.data.setdefault("_harness", {})
            if isinstance(meta, dict):
                meta["llm_used"] = llm_used
                meta["feedback_prompt"] = "Ответ помог? Что бы вы хотели улучшить?"
