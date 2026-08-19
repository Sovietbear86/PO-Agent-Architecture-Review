"""Provider-tolerant semantic wrappers for the production Harness.

The internal OpenAI-compatible gateway may return JSON inside markdown/reasoning
text and may reject provider-level json_schema response_format.  Execution
remains fail-closed: this module only makes transport/serialization tolerant;
all candidate values are still checked against the catalog-derived closed set.
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


def extract_json_object(raw: str) -> dict[str, Any] | None:
    """Extract one JSON object from common Qwen/OpenAI-compatible wrappers.

    We first accept strict JSON.  Then we remove fenced markdown and completed
    <think> blocks.  Finally we scan balanced braces while respecting JSON
    string escaping.  Only a parsed object is accepted; prose is never treated
    as semantic data.
    """
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


class ResilientBlindRecoveryLLMJsonSemanticInterpreter(BlindRecoveryLLMJsonSemanticInterpreter):
    """Primary semantic pass with tolerant JSON transport and strict semantics."""

    @staticmethod
    def _parse_json_content(raw: str) -> dict[str, Any] | None:
        return extract_json_object(raw)

    async def _initial_completion(self, messages: list[LLMMessage]):
        # Prefer plain JSON-object mode when the gateway supports it, but retry
        # without provider-specific formatting for compatible internal models.
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
        payload = json.dumps({"query": query, "context": semantic_context}, ensure_ascii=False)
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

        allowed = [str(x) for x in semantic_context.get("allowed_intents", []) if x]
        capabilities = [item for item in semantic_context.get("available_capabilities", []) if isinstance(item, dict)]
        original_intent = str(data.get("intent_hint") or "").strip()
        semantic_rejected = False

        if original_intent and original_intent.casefold() == "learn_semantic":
            data["intent_hint"] = "learn_semantic"
        elif original_intent:
            resolved = self._canonical_capability_for_intent(original_intent, allowed, capabilities)
            if resolved is None:
                data["intent_hint"] = None
                semantic_rejected = True
            else:
                canonical_intent, _ = resolved
                if await self._semantic_entails_capability(query, canonical_intent, capabilities):
                    data["intent_hint"] = canonical_intent
                else:
                    data["intent_hint"] = None
                    semantic_rejected = True
        else:
            # Blind consensus owns missing-intent recovery.  Preserve fail-closed
            # behavior here rather than running a second catalog-wide tournament.
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
    """Blind verifier that tolerates provider formatting but keeps closed sets."""

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
