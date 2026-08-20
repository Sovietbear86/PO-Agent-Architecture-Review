"""LLM-first semantic core for production PO Harness.

Natural-language understanding belongs to the semantic model. Deterministic code
only validates the closed capability vocabulary and structural source identifiers.
A second semantic audit pass verifies that the candidate frame preserved every
independent constraint from the user's request before execution.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from po_agent.llm.client import LLMClient, LLMMessage

from .dialogue_runtime import ClarificationNeed, SemanticFrame, SemanticInterpreter

_TASK_KEY_RE = re.compile(r"(?<!-)\b[A-ZА-Я][A-ZА-Я0-9_]{1,15}-\d+(?![-A-ZА-Я0-9_])\b", re.I)
_SPRINT_ID_RE = re.compile(r"\b[A-ZА-Я][A-ZА-Я0-9_]{1,15}-SPRNT-\d+\b", re.I)
_TASK_KEY_FULL = re.compile(r"^[A-ZА-Я][A-ZА-Я0-9_]{1,15}-\d+$", re.I)
_SPRINT_ID_FULL = re.compile(r"^[A-ZА-Я][A-ZА-Я0-9_]{1,15}-SPRNT-\d+$", re.I)


def _extract_json_object(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if not text:
        return None
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.I | re.S).strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I | re.S).strip()
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else None
    except Exception:
        pass
    for start, char in enumerate(text):
        if char != "{":
            continue
        depth = 0
        in_string = False
        escaped = False
        for index in range(start, len(text)):
            current = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif current == "\\":
                    escaped = True
                elif current == '"':
                    in_string = False
                continue
            if current == '"':
                in_string = True
            elif current == "{":
                depth += 1
            elif current == "}":
                depth -= 1
                if depth == 0:
                    try:
                        value = json.loads(text[start:index + 1])
                    except Exception:
                        break
                    return value if isinstance(value, dict) else None
    return None


@dataclass(frozen=True)
class DialogueAct:
    act: str
    specific_correction: bool = False
    clarification_question: str | None = None


class LLMFirstSemanticInterpreter(SemanticInterpreter):
    """Production interpreter with two-pass semantic extraction and strict slot hygiene."""

    SYSTEM = """You are the natural-language semantic layer of a Product Owner Harness.
Return ONE JSON object only with keys:
canonical_query, intent_hint, slots, clarifications, confidence, dialogue_act.
clarifications is an array of {field, question, options}.

The context contains complete allowed_intents and available_capabilities.
intent_hint MUST be one allowed_intent for a supported operation, or null only when
no capability can produce the requested result. Never invent intent labels.

Understand free-form Russian and English by MEANING: grammatical cases, reordered
words, synonyms, abbreviations, natural names and clear minor typos. Do not depend on
magic keywords. For task searches preserve EVERY independent user constraint in slots.
Typical slots: person_raw, member_login, sprint_raw, sprint_id, release_raw, release_id,
status_raw, status_semantic, status, product, phrase, task_key.

Rules:
- person_raw is the user's human name/reference. Never invent login/externalId.
- product is the requested product/space scope only when explicitly intended.
- Exact task/sprint IDs written by the user must be preserved exactly.
- Concrete source statuses may go in status; business meanings such as 'незакрытые'
  should use status_semantic/status_raw unless the requested meaning is unambiguous.
- Multi-filter requests use task_search and keep ALL filters.
- Never calculate metrics or fabricate source facts.
- If a requested constraint cannot be represented confidently, add clarification;
  DO NOT silently drop that constraint and broaden the query.

Conversation corrections: context.previous_turn is trusted semantic conversation state.
For correction/recheck merge the previous intent/slots with only the user's change.
A generic challenge preserves previous slots and asks one targeted clarification after
fresh source recheck. dialogue_act is one of new/correction/recheck.
"""

    AUDIT_SYSTEM = """You are the semantic-frame auditor for a production agent.
Given the original user query, context and a candidate semantic frame, return ONE JSON
object with keys intent_hint, slots, clarifications, confidence, audit_ok.

Audit by MEANING, not keyword matching. Your job is to prevent false broadening.
1. Enumerate mentally every independent constraint explicitly requested by the user:
   person, product/space, sprint, release, status/meaning, exact task ID, period, etc.
2. Ensure each requested constraint is present in slots. If the candidate omitted one,
   restore it using the user's wording (e.g. person_raw/status_raw/sprint_raw).
3. Remove constraints that the user did not request.
4. Structural IDs must be concise entity values only, never the whole sentence.
5. Do not invent logins, IDs, source facts or statuses. Grounding happens later.
6. If a constraint is genuinely ambiguous, keep the raw semantic value and add a
   clarification instead of deleting it.
7. Preserve an allowed intent. For multi-filter task retrieval use task_search.

The audited frame must never execute a broader query than the user requested simply
because one constraint was difficult to parse."""

    REPAIR_SYSTEM = """Repair the previous semantic JSON for the same user request.
Return JSON only. Use only an allowed intent. Preserve every independently requested
filter. Do not invent source identifiers."""

    DIALOGUE_ACT_SYSTEM = """Classify the current message relative to the previous PO
Harness request. Return JSON only: {\"act\": one of [\"new\",\"recheck\",\"correction\"],
\"specific_correction\": boolean, \"clarification_question\": string|null}.
'recheck' challenges the previous result without a replacement semantic value.
'correction' changes person/status/sprint/product/period/meaning. Classify by meaning,
not literal trigger phrases."""

    def __init__(self, client: LLMClient, *, model: str | None = None) -> None:
        self.client = client
        self.model = model

    async def _complete_json(self, messages: list[LLMMessage], *, max_tokens: int = 1000) -> dict[str, Any] | None:
        for extra in ({"response_format": {"type": "json_object"}}, {}):
            try:
                response = await self.client.complete(
                    messages,
                    model=self.model,
                    temperature=0.0,
                    max_tokens=max_tokens,
                    **extra,
                )
            except Exception:
                continue
            if response.choices:
                data = _extract_json_object(response.choices[0].message.content)
                if data is not None:
                    return data
        return None

    @staticmethod
    def _allowed(context: dict[str, Any]) -> set[str]:
        return {str(item) for item in context.get("allowed_intents", []) if item}

    @staticmethod
    def _normalize_intent(value: Any) -> str | None:
        if value is None:
            return None
        raw = str(value).strip().replace("-", "_").replace(" ", "_").casefold()
        return raw or None

    @staticmethod
    def _string_slots(value: Any) -> dict[str, str]:
        if not isinstance(value, dict):
            return {}
        return {str(k): str(v).strip() for k, v in value.items() if v not in (None, "") and str(v).strip()}

    @classmethod
    def _structural_overlay(cls, query: str, slots: dict[str, str]) -> dict[str, str]:
        """Structural IDs in user text override any malformed LLM identifier slot."""
        out = dict(slots)
        sprints = list(dict.fromkeys(m.group(0).upper() for m in _SPRINT_ID_RE.finditer(query)))
        tasks = list(dict.fromkeys(m.group(0).upper() for m in _TASK_KEY_RE.finditer(query)))
        if len(sprints) == 1:
            out["sprint_id"] = sprints[0]
            out.pop("sprint_raw", None)
            # A sprint token must never degrade into SPRNT-1 task lookup.
            if not tasks:
                out.pop("task_key", None)
                out.pop("task_id", None)
                out.pop("issue_key", None)
        elif "sprint_id" in out and not _SPRINT_ID_FULL.fullmatch(out["sprint_id"]):
            out["sprint_raw"] = out.pop("sprint_id")

        if len(tasks) == 1:
            out["task_key"] = tasks[0]
        elif "task_key" in out and not _TASK_KEY_FULL.fullmatch(out["task_key"]):
            out.pop("task_key", None)
        return out

    async def _audit(self, query: str, context: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps({"query": query, "context": context, "candidate_frame": candidate}, ensure_ascii=False)
        audited = await self._complete_json(
            [LLMMessage(role="system", content=self.AUDIT_SYSTEM), LLMMessage(role="user", content=payload)],
            max_tokens=800,
        )
        if not audited:
            return candidate
        merged = dict(candidate)
        for key in ("intent_hint", "slots", "clarifications", "confidence"):
            if key in audited:
                merged[key] = audited[key]
        return merged

    async def classify_dialogue_act(self, current: str, previous_query: str) -> DialogueAct:
        payload = json.dumps({"previous_query": previous_query, "current_message": current}, ensure_ascii=False)
        data = await self._complete_json(
            [LLMMessage(role="system", content=self.DIALOGUE_ACT_SYSTEM), LLMMessage(role="user", content=payload)],
            max_tokens=180,
        )
        if not data:
            return DialogueAct("new")
        act = str(data.get("act") or "new").strip().casefold()
        if act not in {"new", "recheck", "correction"}:
            act = "new"
        question = data.get("clarification_question")
        return DialogueAct(act, bool(data.get("specific_correction")), str(question).strip() if question else None)

    async def interpret(self, query: str, *, context: dict[str, Any] | None = None) -> SemanticFrame:
        semantic_context = dict(context or {})
        allowed = self._allowed(semantic_context)
        payload = json.dumps({"query": query, "context": semantic_context}, ensure_ascii=False)
        data = await self._complete_json([
            LLMMessage(role="system", content=self.SYSTEM),
            LLMMessage(role="user", content=payload),
        ])
        if data is None:
            raise ValueError("semantic_model_unavailable_or_invalid_json")

        intent = self._normalize_intent(data.get("intent_hint"))
        if intent not in allowed and intent != "learn_semantic":
            repaired = await self._complete_json([
                LLMMessage(role="system", content=self.SYSTEM),
                LLMMessage(role="system", content=self.REPAIR_SYSTEM),
                LLMMessage(role="user", content=json.dumps({"query": query, "context": semantic_context, "invalid_semantic_frame": data}, ensure_ascii=False)),
            ])
            if repaired is not None:
                data = repaired

        # Independent semantic audit is the production boundary against silent slot
        # loss. It is deliberately language-model based rather than phrase-regex based.
        data = await self._audit(query, semantic_context, data)
        intent = self._normalize_intent(data.get("intent_hint"))
        slots = self._structural_overlay(query, self._string_slots(data.get("slots")))
        act = str(data.get("dialogue_act") or "new").strip().casefold()
        if act in {"correction", "recheck"}:
            slots["dialogue_act"] = act

        needs: list[ClarificationNeed] = []
        for item in data.get("clarifications", []) or []:
            if isinstance(item, dict) and item.get("field") and item.get("question"):
                needs.append(ClarificationNeed(
                    str(item["field"]),
                    str(item["question"]),
                    tuple(str(x) for x in item.get("options", []) if x),
                ))

        if intent not in allowed and intent != "learn_semantic":
            intent = None
            if not any(need.field == "intent" for need in needs):
                needs.append(ClarificationNeed("intent", "Уточните, какой результат PO Agent должен получить."))

        canonical = str(data.get("canonical_query") or query).strip() or query
        try:
            confidence = float(data.get("confidence", 1.0))
        except (TypeError, ValueError):
            confidence = 0.0
        return SemanticFrame(
            canonical_query=canonical,
            intent_hint=intent,
            slots=slots,
            clarifications=needs,
            confidence=max(0.0, min(1.0, confidence)),
            llm_used=True,
        )


class ConversationAwareSemanticInterpreter(SemanticInterpreter):
    """Inject prior canonical semantic state for corrections and follow-ups."""

    def __init__(self, delegate: LLMFirstSemanticInterpreter) -> None:
        self.delegate = delegate
        self.client = delegate.client
        self.model = delegate.model
        self._last: dict[str, dict[str, Any]] = {}

    async def classify_dialogue_act(self, current: str, previous_query: str) -> DialogueAct:
        return await self.delegate.classify_dialogue_act(current, previous_query)

    async def interpret(self, query: str, *, context: dict[str, Any] | None = None) -> SemanticFrame:
        ctx = dict(context or {})
        session = str(ctx.get("session_id") or "")
        if session and session in self._last:
            ctx["previous_turn"] = self._last[session]
        frame = await self.delegate.interpret(query, context=ctx)
        if session:
            self._last[session] = {
                "query": query,
                "canonical_query": frame.canonical_query,
                "intent_hint": frame.intent_hint,
                "slots": dict(frame.slots),
            }
        return frame


class FailClosedSemanticInterpreter(SemanticInterpreter):
    async def interpret(self, query: str, *, context: dict[str, Any] | None = None) -> SemanticFrame:
        del context
        return SemanticFrame(
            canonical_query=query,
            intent_hint=None,
            slots={},
            clarifications=[ClarificationNeed(
                "semantic_model",
                "Семантическая модель недоступна. Я не буду угадывать смысл запроса по шаблонам.",
            )],
            confidence=0.0,
            llm_used=False,
        )
