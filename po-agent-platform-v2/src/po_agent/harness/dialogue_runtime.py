"""Dialogue-first Harness orchestration.

Natural-language understanding is separated from deterministic capabilities.
The LLM may interpret wording and propose a semantic frame, but source entity
identifiers and business semantics are grounded before execution. Uncertainty
becomes an explicit clarification turn instead of a silent guess.
"""
from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Protocol, Any

from po_agent.adapters.task_api import AS21CapabilityUnavailable, AS21SourceError, AS21SourceUnavailable
from po_agent.llm.client import LLMClient, LLMMessage

from .contracts import HarnessRequest, HarnessResponse, ResponseStatus
from .learned_semantics import LearnedSemanticsStore, LearnedSemanticRule


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


class SemanticGrounder(Protocol):
    async def semantic_context(self) -> dict[str, Any]: ...
    async def ground(self, frame: SemanticFrame, original_query: str) -> SemanticFrame: ...


class LLMJsonSemanticInterpreter:
    """Strict JSON semantic interpreter suitable for Qwen/Qwen-Coder models."""

    SYSTEM = """You are the semantic interpreter of a PO Harness agent.
Return JSON only with keys canonical_query, intent_hint, slots, clarifications, confidence.
clarifications is an array of {field, question, options}.
Use placeholders {member_login}, {sprint_id}, {release_id}, {status} when a grounded value is not yet known.
Useful slots: person_raw, member_login, sprint_raw, sprint_id, release_raw, release_id, status_raw, status_semantic, product, phrase.
Rules:
1. Understand free-form Russian/English wording, names, grammatical cases and shorthand.
2. NEVER invent task IDs, sprint IDs, release IDs, logins, statuses or source facts.
3. If an entity or business term is ambiguous, add a clarification instead of guessing.
4. canonical_query must preserve the requested operation and only use values explicitly supplied or resolved in context.
5. Do not calculate metrics; deterministic capabilities do that after interpretation.
6. For business concepts such as 'open tasks', use a learned semantic rule only if it exists; otherwise set status_semantic and leave {status} unresolved.
7. team_members, known_sprints, known_releases and known_statuses are source-backed candidates. Use them only when the match is unambiguous.
8. Learned semantics are configuration facts supplied by the Harness; do not extend them by analogy.
9. For multi-filter task searches set intent_hint to task_search and put each filter in slots. The Harness executes all filters deterministically.
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
        try:
            confidence = float(data.get("confidence", 1.0))
        except (TypeError, ValueError):
            confidence = 0.0
        return SemanticFrame(
            canonical_query=data["canonical_query"].strip() or query,
            intent_hint=str(data.get("intent_hint")) if data.get("intent_hint") else None,
            slots={str(k): str(v) for k, v in (data.get("slots") or {}).items() if v is not None},
            clarifications=needs,
            confidence=max(0.0, min(1.0, confidence)),
            llm_used=True,
        )


class ConservativeSemanticInterpreter:
    """Hermetic fallback, not the primary production NLP layer."""

    async def interpret(self, query: str, *, context: dict[str, Any] | None = None) -> SemanticFrame:
        text = query.strip()
        low = text.casefold()
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

    def __init__(
        self,
        inner,
        interpreter: SemanticInterpreter | None = None,
        semantics: LearnedSemanticsStore | None = None,
        grounder: SemanticGrounder | None = None,
    ) -> None:
        self.inner = inner
        self.interpreter = interpreter or ConservativeSemanticInterpreter()
        self.semantics = semantics
        self.grounder = grounder
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
            data={
                "missing_field": need.field,
                "semantic_frame": dict(pending.frame.slots),
                "_harness": {"llm_used": pending.frame.llm_used, "dialogue_state": "clarifying"},
            },
            warnings=["clarification_required"],
        )

    @staticmethod
    def _apply_answers(frame: SemanticFrame, answers: dict[str, str]) -> SemanticFrame:
        query = frame.canonical_query
        slots = dict(frame.slots)
        for field, value in answers.items():
            slots[field] = value
            token = "{" + field + "}"
            if token in query:
                query = query.replace(token, value)
            elif value and value.casefold() not in query.casefold():
                query = f"{query} {value}"
        return SemanticFrame(
            canonical_query=query,
            intent_hint=frame.intent_hint,
            slots=slots,
            clarifications=[],
            confidence=frame.confidence,
            llm_used=frame.llm_used,
        )

    def learn_explicit_definition(self, *, term: str, meaning: str, trace_id: str, scope: str = "global") -> LearnedSemanticRule:
        if self.semantics is None:
            raise RuntimeError("learned semantics store is not configured")
        return self.semantics.learn_explicit_definition(term=term, meaning=meaning, source_trace_id=trace_id, scope=scope)

    @staticmethod
    def _source_failure(session: str, warning: str, answer: str, started: float) -> HarnessResponse:
        return HarnessResponse(
            status=ResponseStatus.FAILED,
            trace_id=str(uuid.uuid4()),
            session_id=session,
            answer=answer,
            warnings=[warning],
            latency_ms=(time.perf_counter() - started) * 1000,
        )

    async def _execute_frame(self, frame: SemanticFrame, session: str, started: float) -> HarnessResponse:
        hint = (frame.intent_hint or "").strip().replace("-", "_").casefold()
        structured_filters = {
            "assignee": frame.slots.get("member_login") or frame.slots.get("assignee"),
            "sprint_id": frame.slots.get("sprint_id"),
            "release_id": frame.slots.get("release_id"),
            "product": frame.slots.get("product"),
            "status": frame.slots.get("status"),
            "phrase": frame.slots.get("phrase"),
        }
        args = {k: str(v) for k, v in structured_filters.items() if v not in (None, "")}

        if hint in {"task_search", "task_search_composite"} and args:
            try:
                result = await self.capabilities.execute("task.search.composite", args)
                skill = self.skills.resolve("task_search")
                response = HarnessResponse(
                    status=ResponseStatus.COMPLETED,
                    trace_id=str(uuid.uuid4()),
                    session_id=session,
                    answer=result.answer,
                    intent="task_search",
                    skill_id=skill.id,
                    skill_version=skill.version,
                    data=result.data,
                    evidence=result.evidence,
                    warnings=result.warnings,
                    latency_ms=(time.perf_counter() - started) * 1000,
                )
                self._decorate(response, frame.llm_used)
                return response
            except AS21CapabilityUnavailable:
                return self._source_failure(session, "source_capability_unavailable", "Источник AS21 не предоставляет данные, необходимые для этого запроса.", started)
            except AS21SourceUnavailable:
                return self._source_failure(session, "source_unavailable", "Источник AS21 временно недоступен. Данные не интерпретируются как пустой результат.", started)
            except AS21SourceError:
                return self._source_failure(session, "source_protocol_error", "Источник AS21 вернул некорректные данные.", started)

        response = await self.inner.process(HarnessRequest(query=frame.canonical_query, session_id=session))
        self._decorate(response, frame.llm_used)
        response.latency_ms = max(response.latency_ms, (time.perf_counter() - started) * 1000)
        return response

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
            return await self._execute_frame(self._apply_answers(pending.frame, pending.answers), session, started)

        semantic_context: dict[str, Any] = {"session_id": session}
        if self.semantics is not None:
            semantic_context["learned_semantics"] = self.semantics.context("global")
        if self.grounder is not None:
            try:
                semantic_context.update(await self.grounder.semantic_context())
            except AS21CapabilityUnavailable:
                return self._source_failure(session, "source_capability_unavailable", "Источник AS21 не предоставляет данные для проверки контекста запроса.", started)
            except AS21SourceUnavailable:
                return self._source_failure(session, "source_unavailable", "Источник AS21 временно недоступен. Нельзя безопасно интерпретировать запрос без проверки источника.", started)
            except AS21SourceError:
                return self._source_failure(session, "source_protocol_error", "Источник AS21 вернул некорректные данные при проверке контекста.", started)

        try:
            frame = await self.interpreter.interpret(request.query, context=semantic_context)
        except Exception:
            return self._source_failure(session, "semantic_interpretation_failure", "Не удалось безопасно интерпретировать запрос. Попробуйте переформулировать его.", started)

        if frame.confidence < 0.45 and not frame.clarifications:
            frame.clarifications.append(ClarificationNeed("intent", "Я не уверен, что правильно понял запрос. Что именно вы хотите получить?"))

        if self.grounder is not None:
            try:
                frame = await self.grounder.ground(frame, request.query)
            except AS21CapabilityUnavailable:
                return self._source_failure(session, "source_capability_unavailable", "Источник AS21 не предоставляет данные для проверки сущностей запроса.", started)
            except AS21SourceUnavailable:
                return self._source_failure(session, "source_unavailable", "Источник AS21 временно недоступен. Нельзя подтвердить сущности запроса.", started)
            except AS21SourceError:
                return self._source_failure(session, "source_protocol_error", "Источник AS21 вернул некорректные данные при проверке сущностей.", started)

        if frame.clarifications:
            pending = _PendingDialogue(frame=frame, remaining=list(frame.clarifications))
            self._pending[session] = pending
            return self._clarification_response(session, pending)

        return await self._execute_frame(frame, session, started)

    @staticmethod
    def _decorate(response: HarnessResponse, llm_used: bool) -> None:
        if response.data is None:
            response.data = {}
        if isinstance(response.data, dict):
            meta = response.data.setdefault("_harness", {})
            if isinstance(meta, dict):
                meta["llm_used"] = llm_used
                meta["dialogue_state"] = "answered"
                meta["feedback_prompt"] = "Ответ помог? Что бы вы хотели улучшить?"
