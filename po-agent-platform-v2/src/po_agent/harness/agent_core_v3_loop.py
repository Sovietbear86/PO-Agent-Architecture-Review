"""Bounded Hermes-style plan/execute/observe loop for Agent Core v3 H1B.

The planner is LLM-driven, but execution remains deterministic and source-safe.
The LLM selects one of two typed decision shapes: CALL or FINAL. Execution never
relies on a free-form action string. Constraint values may come only from the
original request, source-grounded semantic values, or authoritative observations.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from po_agent.llm.client import LLMClient, LLMMessage

from .agent_core_v3 import AgentCoreV3ContractError, AgentCoreV3FailureCode
from .agent_core_v3_registry import CapabilityRegistryV3


@dataclass(frozen=True)
class AgentLoopActionV3:
    action: str
    capability_id: str | None = None
    constraints: Mapping[str, str] | None = None
    final_answer: str | None = None
    rationale: str | None = None


@dataclass(frozen=True)
class AgentLoopObservationV3:
    step: int
    capability_id: str
    constraints: Mapping[str, str]
    data: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "capability_id": self.capability_id,
            "constraints": dict(self.constraints),
            "data": dict(self.data),
        }


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


class AgentLoopPlannerV3:
    """LLM planner constrained to typed CALL/FINAL decisions and a closed registry."""

    SYSTEM = """You are the bounded planner for a Product Owner agent.
Return ONE JSON object only with exactly these top-level keys:
call, final, rationale.

You MUST choose exactly one typed decision shape:

CALL shape:
{"call":{"capability_id":"<id from capability_catalog>","constraints":{...}},"final":null,"rationale":"..."}

FINAL shape:
{"call":null,"final":{"answer":"..."},"rationale":"..."}

Never return an `action` field. The decision is determined by which typed branch is non-null.
Exactly one of `call` or `final` MUST be non-null.

For CALL:
- capability_id MUST be one id from capability_catalog.
- constraints MUST contain only constraints supported by that capability.
- A constraint value may be:
  1) a literal value explicitly present in the original user_query;
  2) a source-grounded semantic reference in the exact form $ground.<field> from grounded_values; or
  3) an observation reference in the exact form $obs.<step>.<path>.
- Prefer $ground.member_login for a person resolved by the semantic grounder.
- Never invent source ids, logins, task keys, spaces, statuses, people or counts.
- If the next operation depends on a fact returned by a previous capability, use an observation reference.

For FINAL:
- Use only facts present in observations.
- If the requested result is not yet supported by observations, do not finalize; CALL another capability when available.
- If the requested operation is outside the catalog, FINAL may explicitly say it is unsupported; never silently omit it.

Planning policy:
- Break compound requests into the minimum sequence of capability calls.
- Re-plan after every observation.
- Do not repeat a capability call with the same resolved constraints.
- Respect user constraints across all steps.
- The authoritative source is accessed only by executors; you are a planner only.
"""

    REPAIR = """Your previous typed planner decision was invalid or empty. Repair it now.
Return exactly one JSON object with top-level keys call, final, rationale.
Set exactly ONE of call/final to a non-null object and the other to null.
For CALL, choose an exact capability_id from the supplied catalog and safe constraints.
For FINAL, provide a non-empty answer supported by observations.
Never emit an `action` field. Never return both call and final null. Never invent source facts."""

    def __init__(self, client: LLMClient, *, model: str | None = None, max_steps: int = 4) -> None:
        self.client = client
        self.model = model
        self.max_steps = max(2, int(max_steps))

    @staticmethod
    def _parse(raw: str) -> dict[str, Any] | None:
        return _extract_json_object(raw)

    @staticmethod
    def _response_schema() -> dict[str, Any]:
        # Keep the schema simple for OpenAI-compatible endpoints: branch exclusivity
        # is enforced deterministically below instead of relying on provider oneOf.
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "po_agent_h1b_typed_decision",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "call": {
                            "type": ["object", "null"],
                            "properties": {
                                "capability_id": {"type": "string"},
                                "constraints": {"type": "object", "additionalProperties": {"type": "string"}},
                            },
                            "required": ["capability_id", "constraints"],
                            "additionalProperties": False,
                        },
                        "final": {
                            "type": ["object", "null"],
                            "properties": {"answer": {"type": "string"}},
                            "required": ["answer"],
                            "additionalProperties": False,
                        },
                        "rationale": {"type": ["string", "null"]},
                    },
                    "required": ["call", "final", "rationale"],
                    "additionalProperties": False,
                },
            },
        }

    @staticmethod
    def _typed_candidate(data: Mapping[str, Any]) -> AgentLoopActionV3 | None:
        """Decode a typed CALL/FINAL object without guessing the missing branch."""
        call = data.get("call")
        final = data.get("final")
        rationale = str(data.get("rationale") or "").strip() or None

        call_present = isinstance(call, Mapping)
        final_present = isinstance(final, Mapping)
        if call_present == final_present:  # both present or both absent/null
            return None

        if call_present:
            capability_id = str(call.get("capability_id") or "").strip()
            raw_constraints = call.get("constraints")
            if not capability_id or not isinstance(raw_constraints, Mapping):
                return None
            constraints = {
                str(k): str(v).strip()
                for k, v in raw_constraints.items()
                if v not in (None, "") and str(v).strip()
            }
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
        catalog = list(registry.compact_catalog(family="tasks"))
        payload = {
            "user_query": user_query,
            "grounded_values": dict(grounded_values or {}),
            "capability_catalog": catalog,
            "observations": [item.to_dict() for item in observations],
            "step_budget_remaining": self.max_steps - len(observations),
        }
        messages = [
            LLMMessage(role="system", content=self.SYSTEM),
            LLMMessage(role="user", content=json.dumps(payload, ensure_ascii=False)),
        ]
        invalid_shapes: list[dict[str, Any]] = []
        attempts = (
            {"response_format": self._response_schema()},
            {"response_format": {"type": "json_object"}},
            {},
        )
        for attempt_index, extra in enumerate(attempts, start=1):
            try:
                response = await self.client.complete(
                    messages,
                    model=self.model,
                    temperature=0.0,
                    max_tokens=450,
                    **extra,
                )
            except Exception as exc:
                invalid_shapes.append({"attempt": attempt_index, "reason": "provider_error", "error": type(exc).__name__})
                continue
            if not response.choices:
                invalid_shapes.append({"attempt": attempt_index, "reason": "no_choices"})
                continue

            raw_content = response.choices[0].message.content
            candidate = self._parse(raw_content)
            action = self._typed_candidate(candidate) if candidate is not None else None
            if action is not None:
                if action.action == "call_capability":
                    registration = registry.get(action.capability_id or "")
                    constraints = dict(action.constraints or {})
                    unsupported = sorted(set(constraints) - set(registration.contract.supported_constraints))
                    if unsupported:
                        raise AgentCoreV3ContractError(
                            AgentCoreV3FailureCode.UNSUPPORTED_CONSTRAINT,
                            "H1B planner proposed constraints outside the capability contract",
                            details={"capability_id": action.capability_id, "unsupported": unsupported},
                        )
                return action

            invalid_shapes.append({
                "attempt": attempt_index,
                "reason": "invalid_typed_decision",
                "has_call": isinstance(candidate.get("call"), Mapping) if candidate else False,
                "has_final": isinstance(candidate.get("final"), Mapping) if candidate else False,
                "legacy_action_present": bool(candidate and "action" in candidate),
            })
            messages = [
                *messages,
                LLMMessage(role="assistant", content=raw_content or "{}"),
                LLMMessage(role="user", content=self.REPAIR),
            ]

        raise AgentCoreV3ContractError(
            AgentCoreV3FailureCode.V3_PROCESSOR_UNAVAILABLE,
            "H1B agent-loop planner failed bounded typed-decision repair",
            details={"attempts": invalid_shapes},
        )


def resolve_observation_reference(
    value: str,
    *,
    observations: list[AgentLoopObservationV3],
) -> str:
    """Resolve $obs.<step>.<path> against already-validated observation data."""
    raw = str(value or "").strip()
    if not raw.startswith("$obs."):
        return raw
    parts = raw.split(".")
    if len(parts) < 4:
        raise AgentCoreV3ContractError(
            AgentCoreV3FailureCode.UNRESOLVED_CONSTRAINT,
            "Malformed H1B observation reference",
            details={"reference": raw},
        )
    try:
        step = int(parts[1])
    except ValueError as exc:
        raise AgentCoreV3ContractError(
            AgentCoreV3FailureCode.UNRESOLVED_CONSTRAINT,
            "Malformed H1B observation step",
            details={"reference": raw},
        ) from exc
    observation = next((item for item in observations if item.step == step), None)
    if observation is None:
        raise AgentCoreV3ContractError(
            AgentCoreV3FailureCode.UNRESOLVED_CONSTRAINT,
            "H1B planner referenced an unavailable observation",
            details={"reference": raw},
        )
    current: Any = observation.data
    for key in parts[2:]:
        if not isinstance(current, Mapping) or key not in current:
            raise AgentCoreV3ContractError(
                AgentCoreV3FailureCode.UNRESOLVED_CONSTRAINT,
                "H1B observation reference did not resolve to a source fact",
                details={"reference": raw},
            )
        current = current[key]
    if isinstance(current, (str, int, float)) and str(current).strip():
        return str(current).strip()
    raise AgentCoreV3ContractError(
        AgentCoreV3FailureCode.UNRESOLVED_CONSTRAINT,
        "H1B observation reference resolved to an unusable value",
        details={"reference": raw},
    )
