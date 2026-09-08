"""Typed decision protocol for the H1B Hermes-style agent loop.

The planner encodes the control decision structurally as exactly one CALL or one FINAL
branch. Execution, grounding, observation binding, postconditions and source authority
remain deterministic outside the model.

Important provider note: the current Qwen 3.8 OpenAI-compatible endpoint corrupts
JSON when `response_format` is supplied. Therefore this planner intentionally uses
plain completion requests and validates the returned typed object locally. Retries
use a fresh conversation so a malformed provider response cannot poison later attempts.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

from po_agent.llm.client import LLMClient, LLMMessage

from .agent_core_v3 import AgentCoreV3ContractError, AgentCoreV3FailureCode
from .agent_core_v3_loop import AgentLoopActionV3, AgentLoopObservationV3, _extract_json_object
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
- Output JSON only. No markdown and no prose outside the JSON object.
"""

    REPAIR = """Your previous planner response was not an executable typed decision.
Return exactly ONE JSON object only. Choose exactly one branch:
CALL => non-null call and final=null.
FINAL => call=null and non-null final.answer.
Do not return both null. Do not add an action field. Do not invent source facts."""

    def __init__(self, client: LLMClient, *, model: str | None = None, max_steps: int = 4) -> None:
        self.client = client
        self.model = model
        self.max_steps = max(2, int(max_steps))

    @staticmethod
    def _decode_candidate(data: Mapping[str, Any], *, registry: CapabilityRegistryV3) -> AgentLoopActionV3 | None:
        call = data.get("call")
        final = data.get("final")
        rationale = str(data.get("rationale") or "").strip() or None

        call_selected = isinstance(call, Mapping)
        final_selected = isinstance(final, Mapping)
        if call_selected == final_selected:
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

    @classmethod
    def _attempt_messages(
        cls,
        *,
        payload: Mapping[str, Any],
        repair: bool,
    ) -> list[LLMMessage]:
        messages = [
            LLMMessage(role="system", content=cls.SYSTEM),
            LLMMessage(role="user", content=json.dumps(payload, ensure_ascii=False)),
        ]
        if repair:
            messages.append(LLMMessage(role="user", content=cls.REPAIR))
        return messages

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
        failures: list[dict[str, Any]] = []

        # Qwen 3.8's current OpenAI-compatible endpoint double-wraps/corrupts JSON
        # when response_format is present. Do not send response_format at all.
        # Every retry starts from a fresh base conversation to avoid poisoning the
        # model with malformed output from the previous provider attempt.
        for attempt in range(1, 4):
            messages = self._attempt_messages(payload=payload, repair=attempt > 1)
            try:
                response = await self.client.complete(
                    messages,
                    model=self.model,
                    temperature=0.0,
                    max_tokens=350,
                )
            except Exception as exc:
                failures.append({"attempt": attempt, "reason": "provider_error", "type": type(exc).__name__})
                continue

            if not response.choices:
                failures.append({"attempt": attempt, "reason": "no_choice"})
                continue

            raw = response.choices[0].message.content or ""
            parsed = _extract_json_object(raw)
            if parsed is None:
                failures.append({"attempt": attempt, "reason": "invalid_json"})
                continue

            decision = self._decode_candidate(parsed, registry=registry)
            if decision is not None:
                return decision

            failures.append({
                "attempt": attempt,
                "reason": "no_typed_branch",
                "has_call": isinstance(parsed.get("call"), Mapping),
                "has_final": isinstance(parsed.get("final"), Mapping),
            })

        raise AgentCoreV3ContractError(
            AgentCoreV3FailureCode.V3_PROCESSOR_UNAVAILABLE,
            "H1B typed planner failed bounded CALL-or-FINAL decision",
            details={"attempts": failures},
        )
