"""H1B processor that makes the Hermes-style loop the primary v3 control flow.

The loop remains planner-first for capability selection, but semantic grounding is
performed once before planning so human references are resolved to authoritative
source identities rather than sent to AS21 as raw names.
"""
from __future__ import annotations

import time
import uuid
from typing import Any, Mapping

from .agent_core_v3 import (
    AcceptedTurnContract,
    AgentCoreV3ContractError,
    AgentCoreV3FailureCode,
    SessionEnvelope,
)
from .agent_core_v3_loop import AgentLoopObservationV3, resolve_observation_reference
from .agent_core_v3_pilot import AgentCoreV3PilotProcessor
from .contracts import Evidence, HarnessRequest, HarnessResponse, ResponseStatus


class AgentCoreV3H1BProcessor(AgentCoreV3PilotProcessor):
    """Run certified v3 task requests through a grounded bounded agent loop."""

    @staticmethod
    def _resolve_ground_reference(value: str, grounded_values: Mapping[str, str]) -> str:
        raw = str(value or "").strip()
        if not raw.startswith("$ground."):
            return raw
        field = raw[len("$ground."):].strip()
        resolved = str(grounded_values.get(field) or "").strip()
        if not resolved:
            raise AgentCoreV3ContractError(
                AgentCoreV3FailureCode.UNRESOLVED_CONSTRAINT,
                "H1B planner referenced an unavailable grounded semantic value",
                details={"reference": raw},
            )
        return resolved

    async def _run_grounded_agent_loop(
        self,
        request: HarnessRequest,
        envelope: SessionEnvelope,
        started: float,
        *,
        grounded_values: Mapping[str, str],
        semantic_meta: Mapping[str, Any],
    ) -> HarnessResponse:
        if self.loop_planner is None:
            raise AgentCoreV3ContractError(
                AgentCoreV3FailureCode.V3_PROCESSOR_UNAVAILABLE,
                "H1B multi-step planner is unavailable",
            )

        observations: list[AgentLoopObservationV3] = []
        all_evidence: list[Evidence] = []
        trace_steps: list[dict[str, Any]] = []
        last_answer = ""
        seen_calls: set[tuple[str, tuple[tuple[str, str], ...]]] = set()

        for step in range(1, self.loop_planner.max_steps + 1):
            action = await self.loop_planner.next_action(
                user_query=request.query,
                registry=self.registry,
                observations=observations,
                grounded_values=grounded_values,
            )
            if action.action == "final":
                final_answer = action.final_answer or last_answer or "Запрос выполнен по подтвержденным данным источника."
                return HarnessResponse(
                    status=ResponseStatus.COMPLETED,
                    trace_id=str(uuid.uuid4()),
                    session_id=envelope.runtime_session_id,
                    answer=final_answer,
                    intent="agent_loop",
                    skill_id="agent-core-v3-h1b-loop",
                    skill_version="3.2.1-h1b",
                    data={
                        "observations": [item.to_dict() for item in observations],
                        "_agent_core_v3": {
                            "stage": "H1B",
                            "architecture_stage": "H1B_AGENT_LOOP",
                            "conversation_id": envelope.conversation_id,
                            "runtime_session_id": envelope.runtime_session_id,
                            "turn_id": envelope.turn_id,
                            "planner_class": type(self.loop_planner).__name__,
                            "capability_catalog_size": len(self.registry),
                            "loop_steps": trace_steps,
                            "loop_step_count": len(observations),
                            "grounded_values": dict(grounded_values),
                            "semantic_prepass": dict(semantic_meta),
                            "source_authority": "REAL_AS21",
                            "execution_ready": True,
                        },
                    },
                    evidence=all_evidence,
                    latency_ms=(time.perf_counter() - started) * 1000,
                )

            if not action.capability_id:
                raise AgentCoreV3ContractError(
                    AgentCoreV3FailureCode.UNSUPPORTED_CONSTRAINT,
                    "H1B planner did not select a capability",
                )
            registration = self.registry.get(action.capability_id)
            resolved: dict[str, str] = {}
            raw_constraints = dict(action.constraints or {})
            for field, raw_value in raw_constraints.items():
                raw_text = str(raw_value or "").strip()
                if raw_text.startswith("$ground."):
                    resolved[field] = self._resolve_ground_reference(raw_text, grounded_values)
                    continue
                if raw_text.startswith("$obs."):
                    resolved[field] = resolve_observation_reference(raw_text, observations=observations)
                    continue

                # A human-name literal is allowed only when the semantic grounder
                # resolved it to an authoritative member login. Execution receives
                # the canonical login, never the raw person surface form.
                if field == "assignee":
                    person_raw = str(grounded_values.get("person_raw") or "").strip()
                    member_login = str(grounded_values.get("member_login") or "").strip()
                    if member_login and person_raw and raw_text.casefold() == person_raw.casefold():
                        resolved[field] = member_login
                        continue

                if not self._literal_is_source_safe(field, raw_text, request.query):
                    raise AgentCoreV3ContractError(
                        AgentCoreV3FailureCode.UNRESOLVED_CONSTRAINT,
                        "H1B planner proposed a literal constraint not grounded in the user request, semantic grounder, or observations",
                        details={"field": field, "value": raw_text},
                    )
                resolved[field] = raw_text

            call_key = (registration.contract.id, tuple(sorted(resolved.items())))
            if call_key in seen_calls:
                raise AgentCoreV3ContractError(
                    AgentCoreV3FailureCode.UNSUPPORTED_CONSTRAINT,
                    "H1B planner attempted a duplicate capability call",
                    details={"capability_id": registration.contract.id, "constraints": resolved},
                )
            seen_calls.add(call_key)
            intent = next(iter(sorted(registration.intents)))
            contract = AcceptedTurnContract(
                turn_id=f"{envelope.turn_id}:{step}",
                intent=intent,
                constraints=resolved,
                requested_constraints=frozenset(resolved),
            )
            reg, executor_args, answer, data, evidence, validation = await self._execute_contract(contract)
            observation = AgentLoopObservationV3(
                step=step,
                capability_id=reg.contract.id,
                constraints=resolved,
                data=dict(data),
            )
            observations.append(observation)
            all_evidence.extend(evidence)
            last_answer = answer
            trace_steps.append({
                "step": step,
                "capability_id": reg.contract.id,
                "executor_id": reg.contract.executor_id,
                "constraints": resolved,
                "executor_args": executor_args,
                "postcondition_results": validation.to_dict(),
                "observation_keys": sorted(data.keys()),
                "planner_rationale": action.rationale,
            })
            if data.get("found") is False:
                return HarnessResponse(
                    status=ResponseStatus.FAILED,
                    trace_id=str(uuid.uuid4()),
                    session_id=envelope.runtime_session_id,
                    answer=answer,
                    intent=intent,
                    skill_id=reg.contract.id,
                    skill_version=reg.contract.version,
                    data={
                        "observations": [item.to_dict() for item in observations],
                        "_agent_core_v3": {
                            "stage": "H1B",
                            "architecture_stage": "H1B_AGENT_LOOP",
                            "failure_code": "SOURCE_ENTITY_NOT_FOUND",
                            "loop_steps": trace_steps,
                            "grounded_values": dict(grounded_values),
                            "execution_ready": False,
                        },
                    },
                    evidence=all_evidence,
                    latency_ms=(time.perf_counter() - started) * 1000,
                )

        raise AgentCoreV3ContractError(
            AgentCoreV3FailureCode.UNSUPPORTED_CONSTRAINT,
            "H1B agent loop exhausted its bounded step budget without a final answer",
            details={"max_steps": self.loop_planner.max_steps},
        )

    async def process(self, request: HarnessRequest, *, envelope: SessionEnvelope) -> HarnessResponse:
        started = time.perf_counter()
        if self.loop_planner is None:
            return await super().process(request, envelope=envelope)
        try:
            _contract, raw, grounded, clarification = await self._semantic_contract(request, envelope)
            if clarification is not None:
                clarification.latency_ms = (time.perf_counter() - started) * 1000
                return clarification
            grounded_values = dict(grounded.slots)
            semantic_meta = {
                "llm_used": raw.llm_used,
                "raw_intent": raw.intent_hint,
                "raw_slots": dict(raw.slots),
                "grounded_intent": grounded.intent_hint,
            }
            return await self._run_grounded_agent_loop(
                request,
                envelope,
                started,
                grounded_values=grounded_values,
                semantic_meta=semantic_meta,
            )
        except AgentCoreV3ContractError as exc:
            return HarnessResponse(
                status=ResponseStatus.FAILED,
                trace_id=str(uuid.uuid4()),
                session_id=envelope.runtime_session_id,
                answer="Agent Core v3 остановил выполнение: план или результат не прошёл контракт безопасности.",
                data={"_agent_core_v3": {
                    "stage": "H1B",
                    "architecture_stage": "H1B_AGENT_LOOP",
                    "conversation_id": envelope.conversation_id,
                    "runtime_session_id": envelope.runtime_session_id,
                    "turn_id": envelope.turn_id,
                    "failure_code": exc.code.value,
                    "details": exc.details,
                    "capability_catalog_size": len(self.registry),
                    "execution_ready": False,
                }},
                warnings=[exc.code.value],
                latency_ms=(time.perf_counter() - started) * 1000,
            )
