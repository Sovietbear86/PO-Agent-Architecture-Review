"""Agent Core v3 H1B task vertical with bounded Hermes-style agent loop."""
from __future__ import annotations

import re
import time
import uuid
from typing import Any, Mapping

from po_agent.adapters.as21 import AS21Adapter
from po_agent.domain.models import Task

from .agent_core_v3 import (
    AcceptedTurnContract,
    AgentCoreV3ContractError,
    AgentCoreV3FailureCode,
    ResultPostconditionValidator,
    SessionEnvelope,
    guard_constraint_preservation,
)
from .agent_core_v3_loop import AgentLoopObservationV3, AgentLoopPlannerV3, resolve_observation_reference
from .agent_core_v3_registry import build_h1_task_registry
from .contracts import Evidence, HarnessRequest, HarnessResponse, ResponseStatus
from .dialogue_runtime import SemanticGrounder, SemanticInterpreter, _semantic_capability_contract

_APPROVED_SPACES = frozenset({"WMB", "STS", "OLP", "DMS", "CRPV"})
_TASK_KEY_RE = re.compile(r"\b[A-ZА-Я][A-ZА-Я0-9_]{1,15}-\d+(?![-A-ZА-Я0-9_])\b", re.I)
_H1B_COLLECTION_MAX_RESULTS = 10000


class AgentCoreV3PilotSelector:
    """Route only the certified task-family strangler slice."""

    @staticmethod
    def __call__(request: HarnessRequest) -> bool:
        text = request.query.strip()
        lower = text.casefold()
        if _TASK_KEY_RE.search(text):
            return True
        if not any(marker in lower for marker in ("задач", "task")):
            return False
        return any(marker in lower for marker in ("гаранин", "калачан", "assignee", "исполнител"))


class AgentCoreV3PilotProcessor:
    def __init__(
        self,
        adapter: AS21Adapter,
        *,
        interpreter: SemanticInterpreter,
        grounder: SemanticGrounder,
        loop_planner: AgentLoopPlannerV3 | None = None,
    ) -> None:
        self.adapter = adapter
        self.interpreter = interpreter
        self.grounder = grounder
        self.loop_planner = loop_planner
        self.registry = build_h1_task_registry()
        self.validator = ResultPostconditionValidator()

    @staticmethod
    def _task_dict(task: Task) -> dict[str, Any]:
        return {
            "key": task.key,
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "status_category": task.status_category.value,
            "assignee": task.assignee,
            "assignee_login": task.assignee_login,
            "assignee_id": task.assignee_id,
            "project_space": task.project_space,
            "sprint_id": task.sprint_id,
            "release_id": task.release_id,
            "source": task.source,
            "source_data": task.source_data,
        }

    @staticmethod
    def _explicit_space(query: str) -> str | None:
        tokens = {token.upper() for token in re.findall(r"\b[A-Za-zА-Яа-я0-9_-]+\b", query)}
        matches = sorted(tokens & _APPROVED_SPACES)
        return matches[0] if len(matches) == 1 else None

    @staticmethod
    def _requested_fields(query: str, raw_slots: Mapping[str, str]) -> frozenset[str]:
        requested: set[str] = set()
        if _TASK_KEY_RE.search(query) or raw_slots.get("task_key") or raw_slots.get("task_raw"):
            requested.add("task_key")
        if any(raw_slots.get(key) for key in ("person_raw", "member_login", "assignee", "assignee_raw", "person_name")):
            requested.add("assignee")
        if AgentCoreV3PilotProcessor._explicit_space(query) or raw_slots.get("product"):
            requested.add("space")
        lower = query.casefold()
        if any(marker in lower for marker in ("открыт", "незакрыт", "незаверш", "open", "not completed")) or raw_slots.get("status") or raw_slots.get("status_semantic") or raw_slots.get("status_raw"):
            requested.add("status")
        return frozenset(requested)

    @staticmethod
    def _canonical_constraints(query: str, grounded_slots: Mapping[str, str]) -> dict[str, str]:
        constraints: dict[str, str] = {}
        task_key = str(grounded_slots.get("task_key") or "").strip()
        if not task_key:
            match = _TASK_KEY_RE.search(query)
            task_key = match.group(0).upper() if match else ""
        if task_key:
            constraints["task_key"] = task_key.upper()
        assignee = str(grounded_slots.get("member_login") or grounded_slots.get("assignee") or "").strip()
        if assignee:
            constraints["assignee"] = assignee
        space = str(grounded_slots.get("product") or "").strip().upper() or AgentCoreV3PilotProcessor._explicit_space(query)
        if space:
            constraints["space"] = space.upper()
        status = str(grounded_slots.get("status") or grounded_slots.get("status_semantic") or "").strip()
        if status:
            constraints["status"] = status
        return constraints

    async def _semantic_contract(self, request: HarnessRequest, envelope: SessionEnvelope):
        context = await self.grounder.semantic_context()
        allowed_intents, capabilities = _semantic_capability_contract()
        context = dict(context)
        context["allowed_intents"] = allowed_intents
        context["available_capabilities"] = capabilities
        context["agent_core_v3_capability_catalog"] = self.registry.compact_catalog(family="tasks")
        raw = await self.interpreter.interpret(request.query, context=context)
        grounded = await self.grounder.ground(raw, request.query)
        if grounded.clarifications:
            need = grounded.clarifications[0]
            return None, raw, grounded, HarnessResponse(
                status=ResponseStatus.NEEDS_CLARIFICATION,
                trace_id=str(uuid.uuid4()),
                session_id=envelope.runtime_session_id,
                question=need.question,
                options=list(need.options),
                intent=grounded.intent_hint,
                data={"_agent_core_v3": {
                    "stage": "H1B",
                    "architecture_stage": "H1A_REGISTRY",
                    "conversation_id": envelope.conversation_id,
                    "runtime_session_id": envelope.runtime_session_id,
                    "turn_id": envelope.turn_id,
                    "llm_used": raw.llm_used,
                    "raw_semantic_frame": {"intent": raw.intent_hint, "slots": dict(raw.slots)},
                    "grounded_values": dict(grounded.slots),
                    "capability_catalog_size": len(self.registry),
                    "execution_ready": False,
                }},
            )
        requested = self._requested_fields(request.query, raw.slots)
        constraints = self._canonical_constraints(request.query, grounded.slots)
        intent = str(grounded.intent_hint or "").strip()
        if "task_key" in requested:
            intent = "task_lookup"
        elif requested & {"assignee", "space", "status"}:
            intent = "task_search"
        contract = AcceptedTurnContract(
            turn_id=envelope.turn_id,
            intent=intent,
            constraints=constraints,
            requested_constraints=requested,
            semantic_confidence=float(grounded.confidence),
        )
        return contract, raw, grounded, None

    async def _execute_lookup(self, contract: AcceptedTurnContract) -> tuple[str, dict[str, Any], list[Evidence]]:
        key = contract.constraints["task_key"].upper()
        task = await self.adapter.get_task(key)
        if task is None:
            return (
                f"Задача {key} не найдена.",
                {"task_key": key, "found": False},
                [Evidence(type="task_lookup", source="as21", entity_id=key, label="lookup", value="not_found")],
            )
        row = self._task_dict(task)
        return (
            f"{task.key} — {task.title}. Статус: {task.status.value}. Исполнитель: {task.assignee or 'не назначен'}.",
            {"task": row, "tasks": [row], "found": True},
            [Evidence(type="task", source="as21", entity_id=task.key, label=task.title, value=task.status.value)],
        )

    async def _execute_search(self, contract: AcceptedTurnContract) -> tuple[str, dict[str, Any], list[Evidence]]:
        assignee = str(contract.constraints.get("assignee") or "").strip()
        if not assignee:
            raise AgentCoreV3ContractError(
                AgentCoreV3FailureCode.UNRESOLVED_CONSTRAINT,
                "H1B task-search pilot requires a grounded assignee",
            )
        space = str(contract.constraints.get("space") or "").strip().upper()
        jql = f"assignee = {assignee}"
        if space:
            jql += f" AND project = {space}"
        # H1B collection capabilities promise source-complete task sets for the
        # current assignee query. Never inherit the adapter's display-oriented
        # default of 50, because that silently truncates authoritative results
        # and makes the reported count factually wrong. The live assignee route
        # is already bounded server-side (100 rows x 100 pages), so align the
        # executor with that certified source window explicitly.
        tasks = await self.adapter.search_tasks(jql, max_results=_H1B_COLLECTION_MAX_RESULTS)
        status = str(contract.constraints.get("status") or "").strip().casefold()
        if status:
            if status in {"not_completed", "open_tasks", "unresolved", "active"}:
                tasks = [task for task in tasks if not task.is_completed]
            else:
                tasks = [task for task in tasks if status in task.status.value.casefold() or status in task.status_category.value.casefold()]
        rows = [self._task_dict(task) for task in tasks]
        return (
            f"Найдено задач: {len(rows)}.",
            {"count": len(rows), "filters": dict(contract.constraints), "tasks": rows},
            [Evidence(type="task", source="as21", entity_id=task.key, label=task.title, value=task.status.value) for task in tasks],
        )

    async def _execute_contract(self, contract: AcceptedTurnContract):
        registration = self.registry.resolve_intent(contract.intent)
        registration.contract.validate_turn(contract)
        executor_args = dict(contract.constraints)
        guard_constraint_preservation(
            contract.requested_constraints,
            contract.constraints,
            registration.contract.supported_constraints,
            executor_args,
        )
        if registration.contract.executor_id == "task_lookup_executor_v3":
            answer, data, evidence = await self._execute_lookup(contract)
        elif registration.contract.executor_id == "task_search_executor_v3":
            answer, data, evidence = await self._execute_search(contract)
        else:
            raise AgentCoreV3ContractError(
                AgentCoreV3FailureCode.V3_PROCESSOR_UNAVAILABLE,
                f"No executor bound for capability {registration.contract.id}",
                details={"executor_id": registration.contract.executor_id},
            )
        validation = self.validator.validate(contract, data)
        return registration, executor_args, answer, data, evidence, validation

    @staticmethod
    def _literal_is_source_safe(field: str, value: str, query: str) -> bool:
        raw = value.strip()
        if not raw:
            return False
        if raw.startswith("$obs."):
            return True
        if field == "task_key":
            return raw.upper() in {m.group(0).upper() for m in _TASK_KEY_RE.finditer(query)}
        if field == "space":
            return raw.upper() == (AgentCoreV3PilotProcessor._explicit_space(query) or "")
        return raw.casefold() in query.casefold()

    async def _run_agent_loop(self, request: HarnessRequest, envelope: SessionEnvelope, started: float) -> HarnessResponse:
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
                    skill_version="3.2.0-h1b",
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
                            "source_authority": "REAL_AS21",
                            "execution_ready": True,
                        },
                    },
                    evidence=all_evidence,
                    latency_ms=(time.perf_counter() - started) * 1000,
                )

            assert action.capability_id is not None
            registration = self.registry.get(action.capability_id)
            resolved: dict[str, str] = {}
            raw_constraints = dict(action.constraints or {})
            for field, raw_value in raw_constraints.items():
                if not self._literal_is_source_safe(field, raw_value, request.query):
                    raise AgentCoreV3ContractError(
                        AgentCoreV3FailureCode.UNRESOLVED_CONSTRAINT,
                        "H1B planner proposed a literal constraint not grounded in the user request or observations",
                        details={"field": field, "value": raw_value},
                    )
                resolved[field] = resolve_observation_reference(raw_value, observations=observations)
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
                    data={"observations": [item.to_dict() for item in observations], "_agent_core_v3": {
                        "stage": "H1B",
                        "architecture_stage": "H1B_AGENT_LOOP",
                        "failure_code": "SOURCE_ENTITY_NOT_FOUND",
                        "loop_steps": trace_steps,
                        "execution_ready": False,
                    }},
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
        try:
            contract, raw, grounded, clarification = await self._semantic_contract(request, envelope)
            if clarification is not None:
                clarification.latency_ms = (time.perf_counter() - started) * 1000
                return clarification
            assert contract is not None
            try:
                registration, executor_args, answer, data, evidence, validation = await self._execute_contract(contract)
            except AgentCoreV3ContractError as exc:
                if exc.code == AgentCoreV3FailureCode.UNSUPPORTED_CONSTRAINT and self.loop_planner is not None:
                    return await self._run_agent_loop(request, envelope, started)
                raise
            meta = {
                "stage": "H1B",
                "architecture_stage": "H1A_REGISTRY",
                "conversation_id": envelope.conversation_id,
                "runtime_session_id": envelope.runtime_session_id,
                "memory_scope_id": envelope.memory_scope_id,
                "turn_id": envelope.turn_id,
                "interpreter_class": type(self.interpreter).__name__,
                "llm_used": raw.llm_used,
                "raw_semantic_frame": {"intent": raw.intent_hint, "slots": dict(raw.slots), "confidence": raw.confidence},
                "grounded_values": dict(grounded.slots),
                "accepted_turn_contract": contract.to_dict(),
                "capability_id": registration.contract.id,
                "capability_version": registration.contract.version,
                "capability_family": registration.family,
                "capability_catalog_size": len(self.registry),
                "executor_id": registration.contract.executor_id,
                "executor_args": executor_args,
                "source_authority": registration.contract.source_authority,
                "oracle_id": registration.contract.oracle_id,
                "postcondition_results": validation.to_dict(),
                "execution_ready": True,
            }
            data = dict(data)
            data["_agent_core_v3"] = meta
            status = ResponseStatus.COMPLETED if data.get("found") is not False else ResponseStatus.FAILED
            return HarnessResponse(
                status=status,
                trace_id=str(uuid.uuid4()),
                session_id=envelope.runtime_session_id,
                answer=answer,
                intent=contract.intent,
                skill_id=registration.contract.id,
                skill_version=registration.contract.version,
                data=data,
                evidence=evidence,
                latency_ms=(time.perf_counter() - started) * 1000,
            )
        except AgentCoreV3ContractError as exc:
            return HarnessResponse(
                status=ResponseStatus.FAILED,
                trace_id=str(uuid.uuid4()),
                session_id=envelope.runtime_session_id,
                answer="Agent Core v3 остановил выполнение: результат не соответствует принятому контракту запроса.",
                data={"_agent_core_v3": {
                    "stage": "H1B",
                    "architecture_stage": "H1B_AGENT_LOOP" if self.loop_planner is not None else "H1A_REGISTRY",
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