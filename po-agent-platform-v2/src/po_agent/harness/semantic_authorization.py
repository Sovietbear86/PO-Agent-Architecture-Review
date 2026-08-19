"""Independent blind semantic authorization for the dialogue Harness.

The verifier deliberately does not receive the primary/recovery-selected capability.
It classifies the original request against the catalog with an explicit unsupported
sentinel, then deterministic consensus decides whether an intent may survive.
"""
from __future__ import annotations

import json
from typing import Any

from po_agent.llm.client import LLMMessage

from .dialogue_runtime import (
    ClarificationNeed,
    DialogueHarnessRuntime,
    LLMJsonSemanticInterpreter,
    SemanticFrame,
)


_UNSUPPORTED = "__unsupported__"


class BlindRecoveryLLMJsonSemanticInterpreter(LLMJsonSemanticInterpreter):
    """Primary interpreter variant that leaves null-intent recovery to blind consensus.

    The base interpreter's recovery path performs its own catalog-wide pairwise
    ranking. Once blind consensus is enabled that work is duplicate: the blind
    layer performs the authoritative independent recovery immediately afterwards.
    Skipping primary recovery removes a second potentially expensive ranking pass
    without changing the primary happy path or its slot extraction.

    Some OpenAI-compatible enterprise gateways accept ordinary JSON completions
    but reject `response_format=json_schema`. The production SBT gateway has shown
    exactly that behavior. Authorization therefore retries the *same strict prompt*
    without provider-side schema enforcement; the response is still parsed and
    validated locally. This is compatibility recovery, not a semantic bypass.
    """

    async def _repair_missing_intent(self, query: str, semantic_context: dict[str, Any]) -> str | None:
        del query, semantic_context
        return None

    async def _semantic_entails_capability(self, query: str, intent: str, capabilities: list[dict[str, Any]]) -> bool:
        selected = next((item for item in capabilities if str(item.get("intent")) == intent), None)
        if selected is None:
            return False
        payload = json.dumps(
            {
                "query": query,
                "selected_capability_contract": {
                    "intent": selected.get("intent"),
                    "domain": selected.get("domain"),
                    "capability_id": selected.get("capability_id"),
                    "description": selected.get("description"),
                },
            },
            ensure_ascii=False,
        )
        messages = [
            LLMMessage(role="system", content=self.SEMANTIC_ENTAILMENT_SYSTEM),
            LLMMessage(role="user", content=payload),
        ]
        for with_schema in (True, False):
            try:
                kwargs: dict[str, Any] = {
                    "model": self.model,
                    "temperature": 0.0,
                    "max_tokens": 160,
                }
                if with_schema:
                    kwargs["response_format"] = self._entailment_response_format()
                response = await self.client.complete(messages, **kwargs)
                if not response.choices:
                    continue
                data = self._parse_json_content(response.choices[0].message.content)
                if data is None:
                    continue
                return bool(
                    data.get("business_object_match") is True
                    and data.get("operation_match") is True
                    and data.get("outcome_match") is True
                    and data.get("supported") is True
                )
            except Exception:
                continue
        return False


class IntentPreservingDialogueHarnessRuntime(DialogueHarnessRuntime):
    """Expose an already selected semantic intent while grounding asks for details."""

    @staticmethod
    def _clarification_response(session, pending):
        response = DialogueHarnessRuntime._clarification_response(session, pending)
        intent = (pending.frame.intent_hint or "").strip()
        if intent:
            response.intent = intent
            if response.data is None:
                response.data = {}
            if isinstance(response.data, dict):
                meta = response.data.setdefault("_harness", {})
                if isinstance(meta, dict):
                    meta["semantic_intent"] = intent
                    meta["execution_ready"] = False
        return response


class BlindConsensusSemanticInterpreter:
    """Wrap the LLM interpreter with an independent catalog-driven consensus gate."""

    DOMAIN_SYSTEM = """You are an independent blind semantic scope ranker for a PO Harness.
You do NOT know which capability another model selected. Compare only the TWO supplied candidates against the original user request.
Return JSON only with keys matching the requested candidate key and confidence.
Return the candidate whose business domain/scope is semantically closer to the requested operation and outcome.
The special candidate __unsupported__ means the request is outside the compared PO Harness domain.
Missing IDs, people, sprint IDs, release IDs or other source slots do not make a supported operation unsupported; grounding happens later.
Candidate ranking is not source grounding. Return exactly one supplied candidate.
"""

    CAPABILITY_SYSTEM = """You are an independent blind semantic capability ranker inside one PO Harness domain.
You do NOT know which capability another model selected. Compare only the TWO supplied candidates against the original user request.
Return JSON only with keys matching the requested candidate key and confidence.
Return the candidate whose declared operation/outcome is semantically closer to what the user asks for.
The special candidate __unsupported__ means the selected catalog operation/domain does not directly perform the requested outcome.
Missing or ambiguous source entities do not make an otherwise supported operation unsupported; grounding/clarification happens later.
Do not broaden capabilities by analogy. Return exactly one supplied candidate.
"""

    def __init__(self, delegate: LLMJsonSemanticInterpreter) -> None:
        self.delegate = delegate
        self.client = delegate.client
        self.model = delegate.model

    @staticmethod
    def _parse(raw: str) -> dict[str, Any] | None:
        text = raw.strip()
        if text.startswith("```"):
            text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            data = json.loads(text)
        except Exception:
            return None
        return data if isinstance(data, dict) else None

    @staticmethod
    def _response_format(key: str, allowed: list[str]) -> dict[str, Any]:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": f"po_harness_blind_{key}",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        key: {"type": "string", "enum": allowed},
                        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    },
                    "required": [key, "confidence"],
                    "additionalProperties": False,
                },
            },
        }

    async def _choice(self, *, system: str, payload: dict[str, Any], key: str, allowed: list[str]) -> str | None:
        if not allowed:
            return None
        messages = [
            LLMMessage(role="system", content=system),
            LLMMessage(role="user", content=json.dumps(payload, ensure_ascii=False)),
        ]
        # Prefer provider-enforced JSON schema. If the OpenAI-compatible gateway
        # does not implement response_format, retry the identical authorization
        # prompt without it and enforce the closed set locally below.
        for with_schema in (True, False):
            try:
                kwargs: dict[str, Any] = {
                    "model": self.model,
                    "temperature": 0.0,
                    "max_tokens": 180,
                }
                if with_schema:
                    kwargs["response_format"] = self._response_format(key, allowed)
                response = await self.client.complete(messages, **kwargs)
                if not response.choices:
                    continue
                data = self._parse(response.choices[0].message.content)
                candidate = str(data.get(key) or "").strip() if data else ""
                if candidate in allowed:
                    return candidate
            except Exception:
                continue
        return None

    async def _pair_winner(
        self,
        *,
        query: str,
        system: str,
        key: str,
        first: str,
        second: str,
        details: dict[str, dict[str, Any]],
    ) -> str | None:
        pair = [first, second]
        return await self._choice(
            system=system,
            payload={
                "query": query,
                "candidate_pair": pair,
                "candidate_details": [details.get(item, {"value": item}) for item in pair],
            },
            key=key,
            allowed=pair,
        )

    async def _bounded_rank(
        self,
        *,
        query: str,
        system: str,
        key: str,
        candidates: list[str],
        details: dict[str, dict[str, Any]],
    ) -> str | None:
        supported = list(
            dict.fromkeys(candidate for candidate in candidates if candidate and candidate != _UNSUPPORTED)
        )
        if not supported:
            return None

        current = supported
        while len(current) > 1:
            next_round: list[str] = []
            index = 0
            while index < len(current):
                first = current[index]
                if index + 1 >= len(current):
                    next_round.append(first)
                    index += 1
                    continue
                second = current[index + 1]
                winner = await self._pair_winner(
                    query=query,
                    system=system,
                    key=key,
                    first=first,
                    second=second,
                    details=details,
                )
                if winner is None:
                    return None
                next_round.append(winner)
                index += 2
            current = next_round

        champion = current[0]
        if _UNSUPPORTED not in details:
            return champion

        authorization_winner = await self._pair_winner(
            query=query,
            system=system,
            key=key,
            first=champion,
            second=_UNSUPPORTED,
            details=details,
        )
        return champion if authorization_winner == champion else None

    @staticmethod
    def _domain_signatures(capabilities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        domains: dict[str, dict[str, Any]] = {}
        for capability in capabilities:
            domain = str(capability.get("domain") or "").strip()
            if not domain:
                continue
            signature = domains.setdefault(domain, {"domain": domain, "capabilities": []})
            signature["capabilities"].append(
                {
                    "intent": capability.get("intent"),
                    "description": capability.get("description"),
                }
            )
        return [domains[name] for name in sorted(domains)]

    async def _blind_classify(self, query: str, context: dict[str, Any]) -> tuple[str, str] | None:
        capabilities = [item for item in context.get("available_capabilities", []) if isinstance(item, dict)]
        signatures = self._domain_signatures(capabilities)
        domains = [str(item["domain"]) for item in signatures]
        if not domains:
            return None

        domain_details = {str(item["domain"]): item for item in signatures}
        domain_details[_UNSUPPORTED] = {
            "domain": _UNSUPPORTED,
            "description": "The requested business object or outcome is outside all implemented PO Harness domains.",
        }
        domain = await self._bounded_rank(
            query=query,
            system=self.DOMAIN_SYSTEM,
            key="domain",
            candidates=domains,
            details=domain_details,
        )
        if domain is None:
            return None

        domain_capabilities = [item for item in capabilities if str(item.get("domain") or "") == domain]
        intents = [str(item.get("intent")) for item in domain_capabilities if item.get("intent")]
        if not intents:
            return None
        capability_details = {str(item.get("intent")): item for item in domain_capabilities if item.get("intent")}
        capability_details[_UNSUPPORTED] = {
            "intent": _UNSUPPORTED,
            "domain": domain,
            "description": "The requested operation/outcome is not directly implemented by any capability in this domain.",
        }
        intent = await self._bounded_rank(
            query=query,
            system=self.CAPABILITY_SYSTEM,
            key="intent_hint",
            candidates=intents,
            details=capability_details,
        )
        if intent is None:
            return None
        return domain, intent

    @staticmethod
    def _without_intent_clarification(frame: SemanticFrame) -> list[ClarificationNeed]:
        return [need for need in frame.clarifications if need.field != "intent"]

    @staticmethod
    def _rejected(frame: SemanticFrame) -> SemanticFrame:
        needs = list(frame.clarifications)
        if not any(need.field == "intent" for need in needs):
            needs.append(
                ClarificationNeed(
                    "intent",
                    "Я не нашёл независимого подтверждения поддерживаемой операции. Уточните, что вы хотите получить в рамках возможностей PO Agent.",
                )
            )
        return SemanticFrame(
            frame.canonical_query,
            None,
            dict(frame.slots),
            needs,
            frame.confidence,
            frame.llm_used,
        )

    async def interpret(self, query: str, *, context: dict[str, Any] | None = None) -> SemanticFrame:
        semantic_context = context or {}
        frame = await self.delegate.interpret(query, context=semantic_context)
        if (frame.intent_hint or "").strip().casefold() == "learn_semantic":
            return frame

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
