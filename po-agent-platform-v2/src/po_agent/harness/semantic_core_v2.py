"""LLM-first semantic core for production PO Harness.

Natural-language understanding belongs to the semantic model. Deterministic code
only validates the closed capability vocabulary and structural/source-safe slot shape.
A semantic audit plus contract-repair pass prevents silent loss or broadening of user
constraints before execution.
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
_RAW_SURFACE_SLOTS = ("person_raw", "product", "status_raw", "sprint_raw", "release_raw")


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
    """Production interpreter with semantic audit and strict slot-contract repair."""

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

EXTRACTION CONTRACT — extraction and source resolution are different stages:
- person_raw is the concise human reference AS WRITTEN by the user. Keep grammatical
  case. Do not resolve it to a login, externalId or canonical nominative form.
- product is only the concise product/project/space value from the request.
- status_raw is only the concise status wording from the request; status_semantic may
  carry its business meaning. Do not put the whole sentence into either slot.
- sprint_raw/release_raw are only concise identifiers/names, never surrounding prose.
- member_login is allowed only when the USER LITERALLY supplied a login. Never derive
  or invent it from a human name. Person resolution happens downstream.
- When person + product + status/sprint occur together, emit ALL constraints.

Synthetic examples (illustrate shape; do not copy values):
Input: "Что назначено Смирнова в PAY-SPRNT-7?"
slots: {"person_raw":"Смирнова", "sprint_raw":"PAY-SPRNT-7"}
Input: "Покажи карточки со статусом in progress"
slots: {"status_raw":"in progress"}
Input: "Какие задачи есть в BILLING?"
slots: {"product":"BILLING"}
Input: "Покажи open-задачи Петровой в CRM"
slots: {"person_raw":"Петровой", "product":"CRM", "status_raw":"open"}

Rules:
- Exact task/sprint IDs written by the user must be preserved exactly.
- Multi-filter requests use task_search and keep ALL filters.
- Never calculate metrics or fabricate source facts.
- If a requested constraint cannot be represented confidently, preserve its raw value
  and add clarification; DO NOT silently drop it and broaden the query.

Conversation corrections: context.previous_turn is trusted semantic conversation state.
For correction/recheck merge the previous intent/slots with only the user's change.
A generic challenge preserves previous slots and asks one targeted clarification after
fresh source recheck. dialogue_act is one of new/correction/recheck.
"""

    AUDIT_SYSTEM = """You are the semantic-frame auditor for a production agent.
Given the original user query, context and a candidate semantic frame, return ONE JSON
object with keys intent_hint, slots, clarifications, confidence, audit_ok.

Audit by MEANING, not keyword matching. Prevent false broadening.
1. Enumerate every independent constraint expressed by the user: person/assignee,
   product/project/space, sprint, release, status/meaning, exact task ID, period, etc.
2. Restore every omitted constraint using a CONCISE surface value from the user query.
3. person_raw must preserve the user's human reference and grammatical case. Never
   replace it with member_login unless that exact login occurs literally in the query.
4. product/status_raw/sprint_raw/release_raw must be compact values, not full clauses.
5. Compound requests must retain all person/product/status/sprint filters.
6. Structural IDs must be concise entity values only, never the whole sentence.
7. Do not invent logins, IDs, source facts or statuses.
8. If genuinely ambiguous, retain the raw value and add clarification.
9. Preserve an allowed intent; multi-filter task retrieval uses task_search.

Synthetic checks:
"Работа Кузнецова в ANALYTICS" -> person_raw="Кузнецова", product="ANALYTICS".
"Задачи со статусом blocked" -> status_raw="blocked".
The audited frame must never execute a broader query because parsing was difficult."""

    REPAIR_SYSTEM = """Repair the previous semantic JSON for the same user request.
Return JSON only. Use only an allowed intent. Preserve every independently requested
filter. Raw slots must contain compact surface values from the user's request, not the
whole sentence. Never derive member_login from a human name. Do not invent identifiers."""

    CONTRACT_REPAIR_SYSTEM = """The semantic frame violates the PO Harness slot contract.
Return ONE corrected JSON object only with keys canonical_query, intent_hint, slots,
clarifications, confidence, dialogue_act.

Mandatory contract:
- person_raw = concise human reference copied from the user's wording, grammatical case
  preserved. Never convert a name into member_login.
- member_login may exist only if the exact login string appears literally in user query.
- product/status_raw/sprint_raw/release_raw = concise values copied from user wording;
  they must never contain most/all of the sentence or text from another request.
- retain every independently expressed filter; do not broaden the request.
- structural IDs may be normalized only when literally present in the query.
- if uncertain, add clarification instead of inventing a value.
The supplied violations explain what must be repaired. Do not reuse invalid slot text."""

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
        return {
            str(k): str(v).strip()
            for k, v in value.items()
            if v not in (None, "") and str(v).strip()
        }

    @staticmethod
    def _surface_contains(query: str, value: str) -> bool:
        """Check if value appears as a meaningful substring in query.

        Returns False if value is nearly the entire query (likely LLM prose leakage).
        """
        if not value:
            return False
        value_folded = value.casefold()
        query_folded = query.casefold()
        if value_folded not in query_folded:
            return False
        # Prevent matching when value is nearly the entire query (LLM prose leakage)
        # A valid surface span should be significantly shorter than the query
        # Allow up to ~70% of query length for reasonable surface spans
        return len(value.strip()) <= len(query.strip()) * 0.7

    @classmethod
    def _slot_contract_issues(cls, query: str, slots: dict[str, str]) -> list[str]:
        """Detect unsafe semantic slot shapes without doing language interpretation."""
        issues: list[str] = []
        query_text = query.strip()
        query_folded = query_text.casefold()
        for name in _RAW_SURFACE_SLOTS:
            value = slots.get(name)
            if not value:
                continue
            compact = value.strip()
            # Raw slots are surface spans. Foreign text or nearly the entire query is
            # evidence that the LLM leaked prose/session state into a value slot.
            if compact.casefold() not in query_folded:
                issues.append(f"{name}:not_surface_span")
            elif len(query_text) >= 16 and len(compact) >= max(16, int(len(query_text) * 0.72)):
                issues.append(f"{name}:looks_like_full_query")

        # status_semantic must not be a full query or long prose. It should be a
        # concise semantic term like "open_tasks" or "resolved". If it looks like
        # a natural language query (too long, not in original query), drop it.
        status_semantic = slots.get("status_semantic")
        if status_semantic:
            compact = str(status_semantic).strip()
            if len(compact) >= max(16, int(len(query_text) * 0.5)):
                issues.append("status_semantic:looks_like_full_query")
            elif compact.casefold() not in query_folded:
                issues.append("status_semantic:not_surface_span")

        member_login = slots.get("member_login")
        # member_login is a source identifier, not a surface span. It may be derived
        # from person_raw or other sources. Only allow it if:
        # 1. It's a valid login format AND either:
        #    a. person_raw is also present (valid derivation from raw person name)
        #    b. member_login IS in the query (explicit in user text)
        if member_login and not cls._surface_contains(query, member_login):
            # Allow member_login only if it's a valid login AND person_raw is also present
            if cls._looks_like_valid_login(member_login):
                if not slots.get("person_raw"):
                    # member_login without person_raw - check if it's in the query
                    # If not, it's unsafe (LLM derived value without source)
                    issues.append("member_login:not_explicit_in_query")
            else:
                # Not a valid login format - always unsafe
                issues.append("member_login:not_explicit_in_query")
        if member_login and not slots.get("person_raw") and not cls._surface_contains(query, member_login):
            # Same check for person_raw:missing_while_login_was_derived
            if cls._looks_like_valid_login(member_login):
                if not slots.get("person_raw"):
                    issues.append("person_raw:missing_while_login_was_derived")
            else:
                issues.append("person_raw:missing_while_login_was_derived")
        return issues

    @classmethod
    def _drop_unsafe_slots(cls, query: str, slots: dict[str, str]) -> dict[str, str]:
        """Fail-safe hygiene after an unsuccessful repair; never execute broadened junk."""
        out = dict(slots)
        issues = cls._slot_contract_issues(query, out)
        for issue in issues:
            name = issue.split(":", 1)[0]
            if name in out:
                out.pop(name, None)
        return out

    @classmethod
    def _looks_like_valid_login(cls, value: str) -> bool:
        """Check if a member_login value looks like a valid login (not prose)."""
        compact = value.strip()
        if not compact:
            return False
        # A valid login typically:
        # - Is short (less than 30 characters)
        # - Contains a dot (e.g., "Garanin.R.V") or is a short email-like string
        # - Doesn't contain common prose words
        if len(compact) > 30:
            return False
        # Contains dot (e.g., "Garanin.R.V") - common login pattern
        if "." in compact:
            return True
        # Contains uppercase letters (e.g., "IvanovIV") - common in Russian logins
        if any(c.isupper() for c in compact):
            return True
        # Contains underscore (e.g., "ivanov_iv") - common login pattern
        if "_" in compact:
            return True
        # Contains @ (e.g., "ivanov@company.com") - email-like login
        if "@" in compact:
            return True
        # Very short (2-10 chars) - likely a short login like "ivanov"
        if 2 <= len(compact) <= 10:
            return True
        return False

    @classmethod
    def _structural_overlay(cls, query: str, slots: dict[str, str]) -> dict[str, str]:
        """Structural IDs in user text override any malformed LLM identifier slot."""
        out = dict(slots)
        sprints = list(dict.fromkeys(m.group(0).upper() for m in _SPRINT_ID_RE.finditer(query)))
        tasks = list(dict.fromkeys(m.group(0).upper() for m in _TASK_KEY_RE.finditer(query)))
        if len(sprints) == 1:
            out["sprint_id"] = sprints[0]
            out.pop("sprint_raw", None)
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
        payload = json.dumps(
            {"query": query, "context": context, "candidate_frame": candidate},
            ensure_ascii=False,
        )
        audited = await self._complete_json(
            [
                LLMMessage(role="system", content=self.AUDIT_SYSTEM),
                LLMMessage(role="user", content=payload),
            ],
            max_tokens=800,
        )
        if not audited:
            return candidate
        merged = dict(candidate)
        for key in ("intent_hint", "slots", "clarifications", "confidence"):
            if key in audited:
                merged[key] = audited[key]
        return merged

    async def _repair_slot_contract(
        self,
        query: str,
        context: dict[str, Any],
        candidate: dict[str, Any],
    ) -> tuple[dict[str, Any], list[str]]:
        slots = self._string_slots(candidate.get("slots"))
        issues = self._slot_contract_issues(query, slots)
        if not issues:
            return candidate, []
        payload = json.dumps(
            {
                "query": query,
                "context": context,
                "invalid_semantic_frame": candidate,
                "violations": issues,
            },
            ensure_ascii=False,
        )
        repaired = await self._complete_json(
            [
                LLMMessage(role="system", content=self.SYSTEM),
                LLMMessage(role="system", content=self.CONTRACT_REPAIR_SYSTEM),
                LLMMessage(role="user", content=payload),
            ],
            max_tokens=800,
        )
        if repaired is None:
            return candidate, issues
        # If repair returned empty or invalid slots, fall back to original candidate
        repaired_slots = self._string_slots(repaired.get("slots"))
        if not repaired_slots:
            return candidate, issues
        remaining = self._slot_contract_issues(
            query,
            repaired_slots,
        )
        # If repair still has issues, fall back to original candidate
        if remaining:
            return candidate, remaining
        return repaired, []

    async def classify_dialogue_act(self, current: str, previous_query: str) -> DialogueAct:
        payload = json.dumps(
            {"previous_query": previous_query, "current_message": current},
            ensure_ascii=False,
        )
        data = await self._complete_json(
            [
                LLMMessage(role="system", content=self.DIALOGUE_ACT_SYSTEM),
                LLMMessage(role="user", content=payload),
            ],
            max_tokens=180,
        )
        if not data:
            return DialogueAct("new")
        act = str(data.get("act") or "new").strip().casefold()
        if act not in {"new", "recheck", "correction"}:
            act = "new"
        question = data.get("clarification_question")
        return DialogueAct(
            act,
            bool(data.get("specific_correction")),
            str(question).strip() if question else None,
        )

    async def interpret(self, query: str, *, context: dict[str, Any] | None = None) -> SemanticFrame:
        semantic_context = dict(context or {})
        allowed = self._allowed(semantic_context)
        payload = json.dumps(
            {"query": query, "context": semantic_context},
            ensure_ascii=False,
        )
        data = await self._complete_json(
            [
                LLMMessage(role="system", content=self.SYSTEM),
                LLMMessage(role="user", content=payload),
            ]
        )
        if data is None:
            raise ValueError("semantic_model_unavailable_or_invalid_json")

        intent = self._normalize_intent(data.get("intent_hint"))
        if intent not in allowed and intent != "learn_semantic":
            repaired = await self._complete_json(
                [
                    LLMMessage(role="system", content=self.SYSTEM),
                    LLMMessage(role="system", content=self.REPAIR_SYSTEM),
                    LLMMessage(
                        role="user",
                        content=json.dumps(
                            {
                                "query": query,
                                "context": semantic_context,
                                "invalid_semantic_frame": data,
                            },
                            ensure_ascii=False,
                        ),
                    ),
                ]
            )
            if repaired is not None:
                data = repaired

        data = await self._audit(query, semantic_context, data)
        data, contract_issues = await self._repair_slot_contract(query, semantic_context, data)
        intent = self._normalize_intent(data.get("intent_hint"))
        raw_slots = self._string_slots(data.get("slots"))
        if contract_issues:
            raw_slots = self._drop_unsafe_slots(query, raw_slots)
        slots = self._structural_overlay(query, raw_slots)

        act = str(data.get("dialogue_act") or "new").strip().casefold()
        if act in {"correction", "recheck"}:
            slots["dialogue_act"] = act

        needs: list[ClarificationNeed] = []
        for item in data.get("clarifications", []) or []:
            if isinstance(item, dict) and item.get("field") and item.get("question"):
                needs.append(
                    ClarificationNeed(
                        str(item["field"]),
                        str(item["question"]),
                        tuple(str(x) for x in item.get("options", []) if x),
                    )
                )
        if contract_issues:
            needs.append(
                ClarificationNeed(
                    "semantic_contract",
                    "Уточните значения фильтров: семантическая модель не смогла безопасно отделить их от текста запроса.",
                )
            )

        if intent not in allowed and intent != "learn_semantic":
            intent = None
            if not any(need.field == "intent" for need in needs):
                needs.append(
                    ClarificationNeed(
                        "intent",
                        "Уточните, какой результат PO Agent должен получить.",
                    )
                )

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

    async def interpret(self, query: str, *, context: dict[str, Any] | None = None, _preserve_cache: bool = False) -> SemanticFrame:
        ctx = dict(context or {})
        session = str(ctx.get("session_id") or "")
        # For rechecks (_semantic_correction_recheck=True), do NOT update the cache after interpretation
        # This prevents the recheck from polluting the conversation state
        should_update_cache = session and not _preserve_cache and not ctx.get("_semantic_correction_recheck")
        if session and session in self._last and not ctx.get("_semantic_correction_recheck"):
            ctx["previous_turn"] = self._last[session]
        frame = await self.delegate.interpret(query, context=ctx)
        if should_update_cache:
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
            clarifications=[
                ClarificationNeed(
                    "semantic_model",
                    "Семантическая модель недоступна. Я не буду угадывать смысл запроса по шаблонам.",
                )
            ],
            confidence=0.0,
            llm_used=False,
        )
