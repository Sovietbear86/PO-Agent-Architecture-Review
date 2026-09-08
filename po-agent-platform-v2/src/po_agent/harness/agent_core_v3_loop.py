"""Bounded Hermes-style plan/execute/observe loop for Agent Core v3 H1B.

The planner is LLM-driven, but execution remains deterministic and source-safe.
The LLM may select only capabilities present in the registry and may bind a
constraint either to a literal value from the original user request, to a
source-grounded semantic value, or to a previous authoritative observation.
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
    """LLM planner constrained to a closed capability registry and observations."""

    SYSTEM = """You are the bounded planner for a Product Owner agent.
Return ONE JSON object only with keys:
action, capability_id, constraints, final_answer, rationale.

action MUST be exactly one of: call_capability, final.
For call_capability:
- capability_id MUST be one id from capability_catalog.
- constraints MUST contain only constraints supported by that capability.
- A constraint value may be:
  1) a literal value explicitly present in the original user_query;
  2) a source-grounded semantic reference in the exact form $ground.<field> from grounded_values; or
  3) an observation reference in the exact form $obs.<step>.<path>.
- Prefer $ground.member_login for a person resolved by the semantic grounder.
- Never invent source ids, logins, task keys, spaces, statuses, people or counts.
- If the next operation depends on a fact returned by a previous capability,
  reference that observation instead of guessing the value.

For final:
- Use only facts present in observations.
- If the requested result is not yet supported by observations, do NOT finalize;
  call another capability when one in the catalog can obtain it.
- If the requested operation is outside the catalog, fail closed by returning final
  with a concise statement that the requested operation is unsupported; do not silently omit it.

Planning policy:
- Break compound requests into the minimum sequence of capability calls.
- Re-plan after every observation.
- Do not repeat a capability call with the same resolved constraints.
- Respect user constraints across all steps.
- The authoritative source is accessed only by executors; you are a planner only.
"""

    REPAIR = """Your previous planner object was not executable. Repair it now.
Return exactly one JSON object. The `action` value must be `call_capability` or `final`.
If a capability is needed, provide its exact capability_id from the catalog and safe constraints.
If the request is already fully answered by observations, return `final` with final_answer.
Do not return an empty action. Do not invent source facts."""

    def __init__(self, client: LLMClient, *, model: str | None = None, max_steps: int = 4) -> None:
        self.client = client
        self.model = model
        self.max_steps = max(2, int(max_steps))

    @staticmethod
    def _parse(raw: str) -> dict[str, Any] | None:
        return _extract_json_object(raw)

    @staticmethod
    def _response_schema() -> dict[str, Any]:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "po_agent_h1b_next_action",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["call_capability", "final"]},
                        "capability_id": {"type": ["string", "null"]},
                        "constraints": {"type": "object", "additionalProperties": {"type": "string"}},
                        "final_answer": {"type": ["string", "null"]},
                        "rationale": {"type": ["string", "null"]},
                    },
                    "required": ["action", "capability_id", "constraints", "final_answer", "rationale"],
                    "additionalProperties": False,
                },
            },
        }

    @staticmethod
    def _normalize_candidate(data: Mapping[str, Any], *, has_observations: bool) -> dict[str, Any]:
        """Normalize only shapes that are already semantically unambiguous.

        Provider-side JSON-schema enforcement is not reliable for every supported
        model. We may infer the action from a selected capability or an explicit
        final answer, but never invent a missing capability/final decision.
        """
        normalized = dict(data)
        action = str(normalized.get("action") or "").strip()
        capability_id = str(normalized.get("capability_id") or "").strip()
        raw_constraints = normalized.get("constraints")
        constraints = raw_constraints if isinstance(raw_constraints, dict) else {}
        final_answer = str(normalized.get("final_answer") or "").strip()
        if not action and capability_id:
            action = "call_capability"
        elif not action and has_observations and not capability_id and not constraints and final_answer:
            action = "final"
        normalized["action"] = action
        return normalized

    @staticmethod
    def _candidate_executable(data: Mapping[str, Any]) -> bool:
        action = str(data.get("action") or "").strip()
        capability_id = str(data.get("capability_id") or "").strip()
        final_answer = str(data.get("final_answer") or "").strip()
        if action == "call_capability":
            return bool(capability_id)
        if action == "final":
            return bool(final_answer)
        return False

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
        data: dict[str, Any] | None = None
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
            except Exception:
                continue
            if not response.choices:
                continue
            raw_content = response.choices[0].message.content
            candidate = self._parse(raw_content)
            if candidate is None:
                invalid_shapes.append({"attempt": attempt_index, "reason": "invalid_json"})
            else:
                candidate = self._normalize_candidate(candidate, has_observations=bool(observations))
                if self._candidate_executable(candidate):
                    data = candidate
                    break
                invalid_shapes.append({
                    "attempt": attempt_index,
                    "reason": "non_executable_action",
                    "action": str(candidate.get("action") or ""),
                    "capability_id": str(candidate.get("capability_id") or ""),
                    "has_final_answer": bool(str(candidate.get("final_answer") or "").strip()),
                })
            # The old code retried transport formats with the exact same prompt,
            # which produced the same empty action deterministically. Subsequent
            # attempts are explicit LLM repair turns instead.
            messages = [
                *messages,
                LLMMessage(role="assistant", content=raw_content or "{}"),
                LLMMessage(role="user", content=self.REPAIR),
            ]

        if data is None:
            raise AgentCoreV3ContractError(
                AgentCoreV3FailureCode.V3_PROCESSOR_UNAVAILABLE,
                "H1B agent-loop planner failed bounded decision repair",
                details={"attempts": invalid_shapes},
            )

        action = str(data.get("action") or "").strip()
        capability_id = str(data.get("capability_id") or "").strip()
        raw_constraints = data.get("constraints")
        constraints = {
            str(k): str(v).strip()
            for k, v in raw_constraints.items()
            if isinstance(raw_constraints, dict) and v not in (None, "") and str(v).strip()
        } if isinstance(raw_constraints, dict) else {}
        final_answer = str(data.get("final_answer") or "").strip() or None
        rationale = str(data.get("rationale") or "").strip() or None

        if action == "final":
            return AgentLoopActionV3(action="final", final_answer=final_answer, rationale=rationale)
        if action != "call_capability":
            raise AgentCoreV3ContractError(
                AgentCoreV3FailureCode.UNSUPPORTED_CONSTRAINT,
                "H1B planner returned an unsupported action",
                details={"action": action, "has_final_answer": bool(final_answer)},
            )

        registration = registry.get(capability_id)
        unsupported = sorted(set(constraints) - set(registration.contract.supported_constraints))
        if unsupported:
            raise AgentCoreV3ContractError(
                AgentCoreV3FailureCode.UNSUPPORTED_CONSTRAINT,
                "H1B planner proposed constraints outside the capability contract",
                details={"capability_id": capability_id, "unsupported": unsupported},
            )
        return AgentLoopActionV3(
            action="call_capability",
            capability_id=capability_id,
            constraints=constraints,
            rationale=rationale,
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
