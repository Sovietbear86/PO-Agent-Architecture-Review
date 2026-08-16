"""Independent blind semantic authorization for the dialogue Harness.

The verifier deliberately does not receive the primary/recovery-selected capability.
It classifies the original request against the catalog with an explicit unsupported
sentinel, then deterministic consensus decides whether an intent may survive.
"""
from __future__ import annotations

import json
from typing import Any

from po_agent.llm.client import LLMMessage

from .dialogue_runtime import ClarificationNeed, LLMJsonSemanticInterpreter, SemanticFrame


_UNSUPPORTED = "__unsupported__"


class BlindConsensusSemanticInterpreter:
    """Wrap the LLM interpreter with an independent catalog-driven consensus gate."""

    DOMAIN_SYSTEM = """You are an independent blind semantic scope classifier for a PO Harness.
You do NOT know which capability another model selected. Classify only the original user request.
Return exactly one supplied domain, or __unsupported__ when the requested business object/outcome is outside all supplied PO Harness domains.
Missing IDs, people, sprint IDs, release IDs or other source slots do not make a supported operation unsupported; grounding happens later.
Do not force an unrelated PO domain merely because the query contains generic words such as show, find, calculate, tell, or search.
"""

    CAPABILITY_SYSTEM = """You are an independent blind semantic capability classifier inside one PO Harness domain.
You do NOT know which capability another model selected. Classify only the original user request against the supplied catalog capabilities.
Return exactly one supplied canonical intent, or __unsupported__ when none directly performs the requested operation/outcome.
Missing or ambiguous source entities do not make an otherwise supported operation unsupported; grounding/clarification happens later.
Do not broaden capabilities by analogy and do not treat generic text processing as a domain operation.
"""

    def __init__(self, delegate: LLMJsonSemanticInterpreter) -> None:
        self.delegate = delegate
        self.client = delegate.client
        self.model = delegate.model

    @staticmethod
    def _parse(raw: str) -> dict[str, Any] | None:
        try:
            data = json.loads(raw.strip())
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
        try:
            response = await self.client.complete(
                [
                    LLMMessage(role="system", content=system),
                    LLMMessage(role="user", content=json.dumps(payload, ensure_ascii=False)),
                ],
                model=self.model,
                temperature=0.0,
                max_tokens=180,
                response_format=self._response_format(key, allowed),
            )
            if not response.choices:
                return None
            data = self._parse(response.choices[0].message.content)
            candidate = str(data.get(key) or "").strip() if data else ""
            return candidate if candidate in allowed else None
        except Exception:
            return None

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

        domain = await self._choice(
            system=self.DOMAIN_SYSTEM,
            payload={
                "query": query,
                "domain_contracts": signatures,
                "unsupported_value": _UNSUPPORTED,
            },
            key="domain",
            allowed=domains + [_UNSUPPORTED],
        )
        if domain is None or domain == _UNSUPPORTED:
            return None

        domain_capabilities = [item for item in capabilities if str(item.get("domain") or "") == domain]
        intents = [str(item.get("intent")) for item in domain_capabilities if item.get("intent")]
        if not intents:
            return None
        intent = await self._choice(
            system=self.CAPABILITY_SYSTEM,
            payload={
                "query": query,
                "selected_domain": domain,
                "capability_contracts": domain_capabilities,
                "unsupported_value": _UNSUPPORTED,
            },
            key="intent_hint",
            allowed=intents + [_UNSUPPORTED],
        )
        if intent is None or intent == _UNSUPPORTED:
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
