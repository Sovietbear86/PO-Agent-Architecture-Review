"""Typed decision protocol for the H1B Hermes-style agent loop.

The previous planner encoded the control decision in a free string field named
``action``. Some OpenAI-compatible Qwen endpoints returned syntactically valid
JSON while leaving that field (and sometimes every field) empty. H1B must not
make orchestration correctness depend on one fragile enum token.

This planner therefore uses a structural union:

    {"call": {"capability_id": "...", "constraints": {...}}, "final": null, ...}

or

    {"call": null, "final": {"answer": "..."}, ...}

The branch is derived from the shape itself. Execution, grounding, observation
binding, postconditions and source authority remain deterministic elsewhere.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

from po_agent.llm.client import LLMClient, LLMMessage

from .agent_core_v3 import AgentCoreV3ContractError, AgentCoreV3FailureCode
from .agent_core_v3_loop import (
    AgentLoopActionV3,
    AgentLoopObservationV3,
    _extract_json_object,
)
from .agent_core_v3_registry import CapabilityRegistryV3


class TypedAgentLoopPlannerV3:
    """Bounded planner whose decision is encoded by CALL-vs-FINAL shape."""

    SYSTEM = """You are the bounded planner for a Product Owner agent.
Return exactly ONE JSON object in exactly one of these two forms.

CALL:
{"call":{"capability_id":"<id from capability_catalog>","constraints":{"field":"value"}},"final":null,"rationale":"short reason"}

FINAL:
{"call":null,"final":{"answer":"answer using only observations"},"rationale":"short reason"}

Rules:
- Exactly one of call/final must be non-null. Never return both null.
- For CALL, capability_id must be from capability_catalog and constraints must be supported by it.
- Constraint values may only be literals present in user_query, $ground.<field> from grounded_values, or $obs.<step>.<path> from observations.
- Prefer $ground.member_login for a grounded person.
- If the next step depends on a source fact from a previous capability, use $obs; never guess it.
- FINAL is allowed only when observations support the requested result, or when the requested operation is outside the available catalog and the answer explicitly says it is unsupported.
- Break compound requests into the minimum sequence of capability calls and re-plan after each observation.
- Never invent task keys, logins, spaces, statuses, people, counts or any other source fact.
- Do not repeat the same capability with the same constraints.
"""

    REPAIR = """The previous object did not select exactly one typed decision.
Return ONE corrected object now. Choose exactly one branch:
CALL => non-null call and final=null.
FINAL => call=null and non-null final.answer.
Do not return both null. Do not add an action field. Do not invent source facts."""

    def __init__(self, client: LLMClient, *, model: str | None = None, max_steps: int = 4) -> None:
        self.client = client
        self.model = model
        self.max_steps = max(2, int(max_steps))

    @staticmethod
    def _response_schema() -> dict[str, Any]:
        # Keep a fixed outer object rather than oneOf/discriminator because some
        # compatible endpoints only partially enforce complex JSON Schema.
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "po_agent_h1b_typed_decision",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "call": {
                            "anyOf": [
                                {"type": "null"},
                                {
                                    "type": "object",
                                    "properties": {
                                        "capability_id": {"type": "string"},
                                        "constraints": {
                                            "type": "object",
                                            "additionalProperties": {"type": "string"},
                                        },
                                    },
                                    "required": ["capability_id", "constraints"],
                                    "additionalProperties": False,
                                },
                            ]
                        },
                        "final": {
                            "anyOf": [
                                {"type": "null"},
                                {
                                    "type": "object",
                                    "properties": {"answer": {"type": "string"}},
                                    "required": ["answer"],
                                    "additionalProperties": False,
                                },
                            ]
                        },
                        "rationale": {"type": ["string", "null"]},
                    },
                    "required": ["call", "final", "rationale"],
                    "additionalProperties": False,
                },
            },
        }

    @staticmethod
    def _decode_candidate(
        data: Mapping[str, Any],
        *,
        registry: CapabilityRegistryV3,
    ) -> AgentLoopActionV3 | None:
        """Decode only structurally complete CALL or FINAL objects."""
        call = data.get("call")
        final = data.get("final")
        rationale = str(data.get("rationale") or "").strip() or None

        call_selected = isinstance(call, Mapping)
        final_selected = isinstance(final, Mapping)
        if call_selected == final_selected:  # both selected or both absent/null
            return None

        if call_selected:
            capability_id = str(call.get("capability_id") or "").strip()
            raw_constraints = call.get("constraints")
            if not capability_id or not isinstance(raw_constraints, Mapping):
                return None
            registration = registry.get(capability_id)
            constraints = {
                str(key): str(value).strip()
                for key, value in raw_constraints.items()
                if value not in (None, "") and str(value).strip()
            }
            unsupported = sorted(set(constraints) - set(registration.contract.supported_constraints))
            if unsupported:
                raise AgentCoreV3ContractError(
                    AgentCoreV3FailureCode.UNSUPPORTED_CONSTRAINT,
                    "H1B typed planner proposed constraints outside the capability contract",
                    details={"capability_id": capability_id, "unsupported": unsupported},
                )
            return AgentLoopActionV3(
                action="call_capability",
                capability_id=capability_id,
                constraints=constraints,
                rationale=rationale,
            )

        answer = str(final.get("answer") or "").strip()
        if not answer:
            return None
        return AgentLoopActionV3(action="final", final_answer=answer, rationale=rationale)

    async def next_action(
        self,
        *,
        user_query: str,
        registry: CapabilityRegistryV3,
        observations: list[AgentLoopObservationV3],
        grounded_values: Mapping[str, str] | None = None,
    ) -> AgentLoopActionV3:
        payload = {
            "user_query": user_query,
            "grounded_values": dict(grounded_values or {}),
            "capability_catalog": list(registry.compact_catalog(family="tasks")),
            "observations": [item.to_dict() for item in observations],
            "step_budget_remaining": self.max_steps - len(observations),
        }
        messages = [
            LLMMessage(role="system", content=self.SYSTEM),
            LLMMessage(role="user", content=json.dumps(payload, ensure_ascii=False)),
        ]
        failures: list[dict[str, Any]] = []
        formats = (
            {"response_format": self._response_schema()},
            {"response_format": {"type": "json_object"}},
            {},
        )
        for attempt, extra in enumerate(formats, start=1):
            raw = ""
            try:
                response = await self.client.complete(
                    messages,
                    model=self.model,
                    temperature=0.0,
                    max_tokens=350,
                    **extra,
                )
            except Exception as exc:
                failures.append({"attempt": attempt, "reason": "provider_error", "type": type(exc).__name__})
                continue
            if response.choices:
                raw = response.choices[0].message.content or ""
                parsed = _extract_json_object(raw)
                if parsed is not None:
                    decision = self._decode_candidate(parsed, registry=registry)
                    if decision is not None:
                        return decision
                    failures.append({
                        "attempt": attempt,
                        "reason": "no_typed_branch",
                        "has_call": isinstance(parsed.get("call"), Mapping),
                        "has_final": isinstance(parsed.get("final"), Mapping),
                    })
                else:
                    failures.append({"attempt": attempt, "reason": "invalid_json"})
            else:
                failures.append({"attempt": attempt, "reason": "no_choice"})

            messages = [
                *messages,
                LLMMessage(role="assistant", content=raw or "{}"),
                LLMMessage(role="user", content=self.REPAIR),
            ]

        raise AgentCoreV3ContractError(
            AgentCoreV3FailureCode.V3_PROCESSOR_UNAVAILABLE,
            "H1B typed planner failed bounded CALL-or-FINAL decision",
            details={"attempts": failures},
        )
