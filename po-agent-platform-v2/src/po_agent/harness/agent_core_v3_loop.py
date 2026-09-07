"""Bounded Hermes-style plan/execute/observe loop for Agent Core v3 H1B.

The planner is LLM-driven, but execution remains deterministic and source-safe.
The LLM may select only capabilities present in the registry and may bind a
constraint either to a literal value from the original user request or to a
previous authoritative observation. It never receives permission to invent
source identifiers or bypass capability contracts/postconditions.
"""
from __future__ import annotations

import json
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
  1) a literal value explicitly present in the original user_query; or
  2) an observation reference in the exact form $obs.<step>.<path>, where <step>
     is a previous observation step and <path> addresses a field in that
     observation's data, for example $obs.1.task.assignee_login.
- Never invent source ids, logins, task keys, spaces, statuses, people or counts.
- If the next operation depends on a fact returned by a previous capability,
  reference that observation instead of guessing the value.

For final:
- Use only facts present in observations.
- If the requested result is not yet supported by observations, do NOT finalize;
  call another capability when one in the catalog can obtain it.
- Do not claim facts that are absent from observations.

Planning policy:
- Break compound requests into the minimum sequence of capability calls.
- Re-plan after every observation.
- Do not repeat a capability call with the same resolved constraints.
- Respect user constraints across all steps.
- The authoritative source is accessed only by executors; you are a planner only.
"""

    def __init__(self, client: LLMClient, *, model: str | None = None, max_steps: int = 4) -> None:
        self.client = client
        self.model = model
        self.max_steps = max(2, int(max_steps))

    @staticmethod
    def _parse(raw: str) -> dict[str, Any] | None:
        text = (raw or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        try:
            value = json.loads(text)
        except Exception:
            return None
        return value if isinstance(value, dict) else None

    async def next_action(
        self,
        *,
        user_query: str,
        registry: CapabilityRegistryV3,
        observations: list[AgentLoopObservationV3],
    ) -> AgentLoopActionV3:
        catalog = list(registry.compact_catalog(family="tasks"))
        payload = {
            "user_query": user_query,
            "capability_catalog": catalog,
            "observations": [item.to_dict() for item in observations],
            "step_budget_remaining": self.max_steps - len(observations),
        }
        messages = [
            LLMMessage(role="system", content=self.SYSTEM),
            LLMMessage(role="user", content=json.dumps(payload, ensure_ascii=False)),
        ]
        data: dict[str, Any] | None = None
        for extra in ({"response_format": {"type": "json_object"}}, {}):
            try:
                response = await self.client.complete(
                    messages,
                    model=self.model,
                    temperature=0.0,
                    max_tokens=700,
                    **extra,
                )
            except Exception:
                continue
            if response.choices:
                data = self._parse(response.choices[0].message.content)
                if data is not None:
                    break
        if data is None:
            raise AgentCoreV3ContractError(
                AgentCoreV3FailureCode.V3_PROCESSOR_UNAVAILABLE,
                "H1B agent-loop planner did not return valid JSON",
            )

        action = str(data.get("action") or "").strip()
        if action == "final":
            return AgentLoopActionV3(
                action="final",
                final_answer=str(data.get("final_answer") or "").strip() or None,
                rationale=str(data.get("rationale") or "").strip() or None,
            )
        if action != "call_capability":
            raise AgentCoreV3ContractError(
                AgentCoreV3FailureCode.UNSUPPORTED_CONSTRAINT,
                "H1B planner returned an unsupported action",
                details={"action": action},
            )

        capability_id = str(data.get("capability_id") or "").strip()
        registration = registry.get(capability_id)
        raw_constraints = data.get("constraints")
        constraints = {
            str(k): str(v).strip()
            for k, v in raw_constraints.items()
            if isinstance(raw_constraints, dict) and v not in (None, "") and str(v).strip()
        } if isinstance(raw_constraints, dict) else {}
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
            rationale=str(data.get("rationale") or "").strip() or None,
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
