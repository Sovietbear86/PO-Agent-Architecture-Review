"""LLM-first semantic core for production PO Harness.

Natural-language understanding belongs to the semantic model. Deterministic
code only validates the closed capability vocabulary and preserves structural
source identifiers explicitly written by the user. No Russian/English phrase
regex is used to infer assignee, status, product, period, or business meaning.
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
    """Production interpreter with closed-set local validation and provider recovery."""

    SYSTEM = """You are the natural-language semantic layer of a Product Owner Harness.
Return ONE JSON object only with keys:
canonical_query, intent_hint, slots, clarifications, confidence, dialogue_act.
clarifications is an array of {field, question, options}.

The supplied context contains the complete allowed_intents and available_capabilities.
intent_hint MUST be exactly one allowed_intent for a supported operation, or null only
when no capability can produce the requested outcome. Never invent intent labels.

IMPORTANT ARCHITECTURE RULES:
- Understand free-form Russian and English by MEANING, including grammatical cases,
  reordered words, synonyms, abbreviations, natural names, typos that remain clear,
  and phrases such as 'у Гаранина', 'пользователя Моисеева', 'что висит на Родионе',
  'в пространстве DMS', 'по DMS', 'со статусом OPEN'. Do not require magic keywords.
- For task search, put independent constraints in slots. Typical slots are person_raw,
  member_login, sprint_raw, sprint_id, release_raw, release_id, status_raw,
  status_semantic, status, product, phrase, task_key.
- person_raw is the human wording of a person/name. Do NOT invent a login. Grounding
  resolves person_raw to a source-backed identity.
- product is a semantic product/space selector such as DMS/OLP only when the user asks
  for that scope. Do not infer unrelated products.
- 'open', 'незакрытые', 'в работе' and similar business words are semantics, not source
  status IDs. Use status_semantic/status_raw unless the user explicitly supplied a
  concrete source status such as OPEN.
- Exact task/sprint IDs explicitly written by the user must be preserved verbatim.
  Source grounding validates them later.
- For multi-filter searches use task_search and put ALL filters in slots.
- Do not calculate metrics or fabricate source facts.

CONVERSATION / CORRECTION:
- context.previous_turn, when present, is trusted conversation state containing the
  previous user query and semantic frame, NOT a new source fact.
- If the user says the previous answer is wrong, asks to recheck, says they made a
  typo, says 'I meant ...', corrects a person/status/sprint/product, or otherwise
  refers to the previous request, set dialogue_act to 'correction' or 'recheck'.
- Merge the previous semantic intent/slots with ONLY the correction supplied now.
- A generic challenge with no corrected value (e.g. 'ты не прав, проверь ещё раз')
  must preserve the previous intent/slots and add one targeted clarification asking
  what semantic assumption or result should be changed after recheck.
- An explicit correction (e.g. 'Опечатался, речь о пользователе Моисеев А.В. в DMS')
  should update the relevant slots and normally execute without demanding magic words.
- A normal unrelated new request has dialogue_act='new'.

canonical_query is an auditable semantic rendering; execution is driven by validated
intent_hint + grounded slots, not by literal matching of canonical_query.
"""

    REPAIR_SYSTEM = """Repair the previous semantic JSON for the same user request.
Return JSON only. Use only an intent from allowed_intents. Preserve every independently
requested filter. Do not invent source identifiers. Natural-language paraphrases must
not be rejected merely because they do not contain a preferred keyword."""

    DIALOGUE_ACT_SYSTEM = """Classify the current message relative to the previous PO
Harness request. Return JSON only: {\"act\": one of [\"new\",\"recheck\",\"correction\"],
\"specific_correction\": boolean, \"clarification_question\": string|null}.
'recheck' means the user challenges the previous result without supplying a replacement
semantic value. 'correction' means the user supplies or changes a person/status/sprint/
product/period/meaning from the previous request. Do this by meaning, not keyword rules.
For recheck, clarification_question should be a short targeted question about what
assumption/result needs correction. For new, it must be null."""

    def __init__(self, client: LLMClient, *, model: str | None = None) -> None:
        self.client = client
        self.model = model

    async def _complete_json(self, messages: list[LLMMessage], *, max_tokens: int = 900) -> dict[str, Any] | None:
        attempts = (
            {"response_format": {"type": "json_object"}},
            {},
        )
        for extra in attempts:
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
            if not response.choices:
                continue
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
    def _structural_overlay(query: str, slots: dict[str, str]) -> dict[str, str]:
        """Preserve exact structural IDs only; never infer natural-language semantics."""
        out = dict(slots)
        sprints = list(dict.fromkeys(match.group(0).upper() for match in _SPRINT_ID_RE.finditer(query)))
        tasks = list(dict.fromkeys(match.group(0).upper() for match in _TASK_KEY_RE.finditer(query)))
        if len(sprints) == 1:
            out["sprint_id"] = sprints[0]
            # A provider must not reinterpret SPRNT-1 as a task key.
            if not tasks:
                out.pop("task_key", None)
                out.pop("task_id", None)
                out.pop("issue_key", None)
        if len(tasks) == 1:
            out["task_key"] = tasks[0]
        return out

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
        return DialogueAct(
            act=act,
            specific_correction=bool(data.get("specific_correction")),
            clarification_question=str(question).strip() if question else None,
        )

    async def interpret(self, query: str, *, context: dict[str, Any] | None = None) -> SemanticFrame:
        semantic_context = dict(context or {})
        allowed = self._allowed(semantic_context)
        payload = json.dumps({"query": query, "context": semantic_context}, ensure_ascii=False)
        messages = [LLMMessage(role="system", content=self.SYSTEM), LLMMessage(role="user", content=payload)]
        data = await self._complete_json(messages)
        if data is None:
            raise ValueError("semantic_model_unavailable_or_invalid_json")

        intent = self._normalize_intent(data.get("intent_hint"))
        if intent not in allowed and intent != "learn_semantic":
            repair_payload = json.dumps(
                {"query": query, "context": semantic_context, "invalid_semantic_frame": data},
                ensure_ascii=False,
            )
            repaired = await self._complete_json(
                [LLMMessage(role="system", content=self.SYSTEM), LLMMessage(role="system", content=self.REPAIR_SYSTEM), LLMMessage(role="user", content=repair_payload)]
            )
            if repaired is not None:
                data = repaired
                intent = self._normalize_intent(data.get("intent_hint"))

        slots_raw = data.get("slots") if isinstance(data.get("slots"), dict) else {}
        slots = {str(k): str(v) for k, v in slots_raw.items() if v not in (None, "")}
        slots = self._structural_overlay(query, slots)
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
                needs.append(ClarificationNeed(
                    "intent",
                    "Я не смог однозначно сопоставить запрос с доступной операцией PO Agent. Уточните, какой результат вы хотите получить.",
                ))

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
    """Inject prior semantic state so paraphrases/corrections do not need regex rules."""

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
    """Never pretend regex routing is natural-language understanding in production."""

    async def interpret(self, query: str, *, context: dict[str, Any] | None = None) -> SemanticFrame:
        del context
        return SemanticFrame(
            canonical_query=query,
            intent_hint=None,
            slots={},
            clarifications=[ClarificationNeed(
                "semantic_model",
                "Семантическая модель недоступна. Я не буду угадывать смысл запроса по шаблонам; восстановите LLM-подключение и повторите запрос.",
            )],
            confidence=0.0,
            llm_used=False,
        )
