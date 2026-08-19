"""Provider-tolerant semantic wrappers for the production Harness.

The internal OpenAI-compatible gateway may return JSON inside markdown/reasoning
text and may reject provider-level response_format. Execution remains fail-closed:
provider transport tolerance never creates source facts or arbitrary intents.

For a deliberately tiny set of unambiguous Core-8 utterance shapes we also keep
a deterministic, catalog-closed recovery path. This is not a general NLP router:
it only recognizes explicit business objects/operations that map one-to-one to an
implemented catalog intent. Everything else still requires the semantic model or
fails closed.
"""
from __future__ import annotations

import json
import re
from typing import Any

from po_agent.llm.client import LLMMessage

from .dialogue_runtime import ClarificationNeed, SemanticFrame
from .semantic_authorization import (
    BlindConsensusSemanticInterpreter,
    BlindRecoveryLLMJsonSemanticInterpreter,
)

_TASK_KEY_RE = re.compile(r"\b[A-ZА-Я][A-ZА-Я0-9_]{1,15}-\d+\b", re.I)


def extract_json_object(raw: str) -> dict[str, Any] | None:
    """Extract one JSON object from common Qwen/OpenAI-compatible wrappers."""
    text = (raw or "").strip()
    if not text:
        return None

    candidates = [text]
    if text.startswith("```"):
        candidates.append(re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I | re.S).strip())
    without_think = re.sub(r"<think>.*?</think>", "", text, flags=re.I | re.S).strip()
    if without_think and without_think not in candidates:
        candidates.append(without_think)

    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except Exception:
            continue
        if isinstance(value, dict):
            return value

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
                    fragment = text[start:index + 1]
                    try:
                        value = json.loads(fragment)
                    except Exception:
                        break
                    return value if isinstance(value, dict) else None
    return None


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def _person_raw(query: str) -> str | None:
    """Extract only an explicitly written surname after common task/person forms."""
    patterns = (
        r"(?:задач[аиуы]?|нагрузк\w*|исполнител\w*)\s+([А-ЯЁ][а-яё]{2,})",
        r"(?:у|для)\s+([А-ЯЁ][а-яё]{2,})",
    )
    for pattern in patterns:
        match = re.search(pattern, query)
        if match:
            return match.group(1)
    return None


def _explicit_product(query: str) -> str | None:
    low = query.casefold()
    if "olap" in low or re.search(r"\bolp\b", low):
        return "OLP"
    if "datamarts" in low or "data marts" in low or re.search(r"\bdms\b", low):
        return "DMS"
    return None


def deterministic_core8_frame(query: str, *, allowed: set[str]) -> SemanticFrame | None:
    """Recognize only high-precision Core-8 operation shapes.

    The recognizer never resolves source IDs other than an explicit task key and
    never accepts an intent outside the catalog-derived ``allowed`` set. Entity
    names, current sprint and release identifiers remain subject to the normal
    source grounder.
    """
    text = query.strip()
    low = text.casefold()
    key_match = _TASK_KEY_RE.search(text)
    task_key = key_match.group(0).upper() if key_match else None
    intent: str | None = None
    slots: dict[str, str] = {}

    # Exact-task operations: require an explicit source key, which makes the
    # business object unambiguous without guessing any source fact.
    if task_key:
        slots["task_key"] = task_key
        if _contains_any(low, ("качеств", "постановк", "quality")):
            intent = "task_quality"
        elif _contains_any(low, ("суммар", "резюм", "кратко", "что нужно сделать", "summary")):
            intent = "task_summary"
        elif _contains_any(low, ("подбери исполн", "рекоменд", "кому назнач", "assignee")):
            intent = "team_assignee_recommendation"
        elif _contains_any(low, ("компетенц", "соответств", "подходит", "competency")):
            intent = "team_competency_match"
        elif _contains_any(low, ("покажи задач", "найди задач", "открой задач", "task")):
            intent = "task_lookup"

    # Task search must explicitly mention tasks plus a search/show operation.
    if intent is None and _contains_any(low, ("задач", "tasks")) and _contains_any(low, ("найди", "покажи", "выведи", "search", "find", "show")):
        intent = "task_search"
        person = _person_raw(text)
        if person:
            slots["person_raw"] = person
        product = _explicit_product(text)
        if product:
            slots["product"] = product
        if _contains_any(low, ("открыт", "незаверш", "open", "not completed")):
            # Preserve the business term; learned semantics/clarification decides
            # its exact status predicate. We do not silently invent AS21 statuses.
            slots["status_semantic"] = "open"
            slots["status_raw"] = "открытые" if "открыт" in low else "not_completed"
        if _contains_any(low, ("актуальн", "текущ", "current", "active")) and _contains_any(low, ("спринт", "sprint")):
            slots["sprint_raw"] = "current"

    if intent is None and _contains_any(low, ("спринт", "sprint")):
        product = _explicit_product(text)
        if product:
            slots["product"] = product
        if _contains_any(low, ("текущ", "актуальн", "current")) and _contains_any(low, ("какой", "покажи", "what", "show")):
            intent = "sprint_current"
            slots["sprint_raw"] = "current"
        elif _contains_any(low, ("здоров", "готовност", "health", "readiness")):
            intent = "sprint_health"
            if _contains_any(low, ("текущ", "актуальн", "current")):
                slots["sprint_raw"] = "current"
        elif _contains_any(low, ("velocity", "велосит", "скорост", "производительност")):
            intent = "sprint_velocity"
            if _contains_any(low, ("текущ", "актуальн", "current")):
                slots["sprint_raw"] = "current"

    if intent is None and _contains_any(low, ("нагрузк", "workload", "загружен")):
        intent = "team_workload"
        person = _person_raw(text)
        if person:
            slots["person_raw"] = person

    if intent is None and _contains_any(low, ("релиз", "release")) and _contains_any(low, ("здоров", "готовност", "health", "readiness", "риск")):
        intent = "release_health"
        release_match = re.search(r"\b(?:release|релиз)\s+([A-Za-zА-Яа-я0-9_.-]{2,80})", text, re.I)
        if release_match:
            slots["release_raw"] = release_match.group(1)
        product = _explicit_product(text)
        if product:
            slots["product"] = product

    if intent is None or intent not in allowed:
        return None
    return SemanticFrame(
        canonical_query=text,
        intent_hint=intent,
        slots=slots,
        clarifications=[],
        confidence=1.0,
        llm_used=False,
    )


class ResilientBlindRecoveryLLMJsonSemanticInterpreter(BlindRecoveryLLMJsonSemanticInterpreter):
    """Primary semantic pass with provider tolerance and closed deterministic recovery."""

    @staticmethod
    def _parse_json_content(raw: str) -> dict[str, Any] | None:
        return extract_json_object(raw)

    async def _initial_completion(self, messages: list[LLMMessage]):
        try:
            return await self.client.complete(
                messages,
                model=self.model,
                temperature=0.0,
                max_tokens=900,
                response_format={"type": "json_object"},
            )
        except Exception:
            return await self.client.complete(
                messages,
                model=self.model,
                temperature=0.0,
                max_tokens=900,
            )

    async def interpret(self, query: str, *, context: dict[str, Any] | None = None) -> SemanticFrame:
        semantic_context = context or {}
        allowed = [str(x) for x in semantic_context.get("allowed_intents", []) if x]
        fallback = deterministic_core8_frame(query, allowed=set(allowed))
        payload = json.dumps({"query": query, "context": semantic_context}, ensure_ascii=False)
        try:
            response = await self._initial_completion(
                [LLMMessage(role="system", content=self.SYSTEM), LLMMessage(role="user", content=payload)]
            )
            if not response.choices:
                raise ValueError("semantic_initial_no_choices")
            data = extract_json_object(response.choices[0].message.content)
            if not isinstance(data, dict):
                raise ValueError("semantic_initial_json_parse")
            if not isinstance(data.get("canonical_query"), str):
                raise ValueError("semantic_initial_contract")
        except Exception:
            if fallback is not None:
                return fallback
            raise

        capabilities = [item for item in semantic_context.get("available_capabilities", []) if isinstance(item, dict)]
        original_intent = str(data.get("intent_hint") or "").strip()
        semantic_rejected = False

        if original_intent and original_intent.casefold() == "learn_semantic":
            data["intent_hint"] = "learn_semantic"
        elif original_intent:
            resolved = self._canonical_capability_for_intent(original_intent, allowed, capabilities)
            if resolved is None:
                if fallback is not None:
                    return fallback
                data["intent_hint"] = None
                semantic_rejected = True
            else:
                canonical_intent, _ = resolved
                if await self._semantic_entails_capability(query, canonical_intent, capabilities):
                    data["intent_hint"] = canonical_intent
                elif fallback is not None:
                    return fallback
                else:
                    data["intent_hint"] = None
                    semantic_rejected = True
        elif fallback is not None:
            return fallback
        else:
            semantic_rejected = True

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
        if semantic_rejected and not needs:
            needs.append(
                ClarificationNeed(
                    "intent",
                    "Я не нашёл поддерживаемую операцию для этого запроса. Уточните, что вы хотите получить в рамках возможностей PO Agent.",
                )
            )
        try:
            confidence = float(data.get("confidence", 1.0))
        except (TypeError, ValueError):
            confidence = 0.0
        return SemanticFrame(
            data["canonical_query"].strip() or query,
            str(data.get("intent_hint")) if data.get("intent_hint") else None,
            {str(k): str(v) for k, v in (data.get("slots") or {}).items() if v is not None},
            needs,
            max(0.0, min(1.0, confidence)),
            True,
        )


class ResilientBlindConsensusSemanticInterpreter(BlindConsensusSemanticInterpreter):
    """Blind verifier with provider tolerance and deterministic Core-8 authorization."""

    @staticmethod
    def _parse(raw: str) -> dict[str, Any] | None:
        return extract_json_object(raw)

    async def _choice(
        self,
        *,
        system: str,
        payload: dict[str, Any],
        key: str,
        allowed: list[str],
    ) -> str | None:
        if not allowed:
            return None
        messages = [
            LLMMessage(role="system", content=system),
            LLMMessage(role="user", content=json.dumps(payload, ensure_ascii=False)),
        ]
        attempts = (
            {"response_format": self._response_format(key, allowed)},
            {"response_format": {"type": "json_object"}},
            {},
        )
        for extra in attempts:
            try:
                response = await self.client.complete(
                    messages,
                    model=self.model,
                    temperature=0.0,
                    max_tokens=180,
                    **extra,
                )
            except Exception:
                continue
            if not response.choices:
                continue
            data = extract_json_object(response.choices[0].message.content)
            candidate = str(data.get(key) or "").strip() if data else ""
            if candidate in allowed:
                return candidate
        return None

    async def interpret(self, query: str, *, context: dict[str, Any] | None = None) -> SemanticFrame:
        semantic_context = context or {}
        frame = await self.delegate.interpret(query, context=semantic_context)
        if (frame.intent_hint or "").strip().casefold() == "learn_semantic":
            return frame

        # A deterministic delegate frame is already authorized by an exact
        # catalog-closed recognizer. Do not make provider availability a second
        # mandatory dependency for that same high-precision decision.
        if frame.llm_used is False:
            allowed = {str(x) for x in semantic_context.get("allowed_intents", []) if x}
            proof = deterministic_core8_frame(query, allowed=allowed)
            if proof is not None and proof.intent_hint == frame.intent_hint:
                return frame
            return self._rejected(frame)

        blind = await self._blind_classify(query, semantic_context)
        if blind is None:
            return self._rejected(frame)
        blind_domain, blind_intent = blind

        capabilities = [item for item in semantic_context.get("available_capabilities", []) if isinstance(item, dict)]
        selected = next(
            (item for item in capabilities if str(item.get("intent") or "") == str(frame.intent_hint or "")),
            None,
        )
        if selected is not None:
            selected_domain = str(selected.get("domain") or "")
            if selected_domain != blind_domain or str(frame.intent_hint) != blind_intent:
                return self._rejected(frame)
            return SemanticFrame(
                frame.canonical_query,
                str(frame.intent_hint),
                dict(frame.slots),
                self._without_intent_clarification(frame),
                frame.confidence,
                frame.llm_used,
            )
        return SemanticFrame(
            frame.canonical_query,
            blind_intent,
            dict(frame.slots),
            self._without_intent_clarification(frame),
            frame.confidence,
            frame.llm_used,
        )
