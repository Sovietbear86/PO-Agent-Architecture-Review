"""Agent Core v3 H1B pilot vertical.

The pilot deliberately supports only the first certified task family.  It uses the
existing LLM-first semantic interpreter and deterministic production grounder,
then freezes an AcceptedTurnContract before executing against the authoritative
adapter.  Unsupported queries fall back through the strangler seam to legacy.
"""
from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass
from typing import Any, Mapping

from po_agent.adapters.as21 import AS21Adapter
from po_agent.domain.models import Task

from .agent_core_v3 import (
    AcceptedTurnContract,
    AgentCoreV3ContractError,
    AgentCoreV3FailureCode,
    CapabilityContractV3,
    ResultPostconditionValidator,
    SOURCE_AUTHORITY_REAL_AS21,
    SessionEnvelope,
    guard_constraint_preservation,
)
from .contracts import Evidence, HarnessRequest, HarnessResponse, ResponseStatus
from .dialogue_runtime import SemanticGrounder, SemanticInterpreter, _semantic_capability_contract

_APPROVED_SPACES = frozenset({"WMB", "STS", "OLP", "DMS", "CRPV"})
_TASK_KEY_RE = re.compile(r"\b[A-ZА-Я][A-ZА-Я0-9_]{1,15}-\d+(?![-A-ZА-Я0-9_])\b", re.I)


@dataclass(frozen=True)
class V3CapabilityRegistration:
    contract: CapabilityContractV3


class PilotCapabilityRegistryV3:
    def __init__(self) -> None:
        source = SOURCE_AUTHORITY_REAL_AS21
        self._items = {
            "task_lookup": V3CapabilityRegistration(
                CapabilityContractV3(
                    id="task-lookup-v3",
                    version="3.0.0-h1b",
                    supported_constraints=frozenset({"task_key"}),
                    source_authority=source,
                    executor_id="task_lookup_executor_v3",
                    oracle_id="direct_mcp_read_unit",
                )
            ),
            "task_search": V3CapabilityRegistration(
                CapabilityContractV3(
                    id="task-search-v3",
                    version="3.0.0-h1b",
                    supported_constraints=frozenset({"assignee", "space", "status"}),
                    source_authority=source,
                    executor_id="task_search_executor_v3",
                    oracle_id="direct_mcp_task_search",
                )
            ),
        }

    def resolve(self, intent: str) -> V3CapabilityRegistration:
        key = "task_lookup" if intent == "task_lookup" else "task_search"
        if key not in self._items:
            raise AgentCoreV3ContractError(
                AgentCoreV3FailureCode.UNSUPPORTED_CONSTRAINT,
                f"No H1B v3 capability for intent {intent}",
            )
        return self._items[key]


class AgentCoreV3PilotSelector:
    """Route only the explicitly chosen first v3 task family."""

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
    ) -> None:
        self.adapter = adapter
        self.interpreter = interpreter
        self.grounder = grounder
        self.registry = PilotCapabilityRegistryV3()
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
                    "conversation_id": envelope.conversation_id,
                    "runtime_session_id": envelope.runtime_session_id,
                    "turn_id": envelope.turn_id,
                    "llm_used": raw.llm_used,
                    "raw_semantic_frame": {"intent": raw.intent_hint, "slots": dict(raw.slots)},
                    "grounded_values": dict(grounded.slots),
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
        tasks = await self.adapter.search_tasks(jql)
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

    async def process(self, request: HarnessRequest, *, envelope: SessionEnvelope) -> HarnessResponse:
        started = time.perf_counter()
        try:
            contract, raw, grounded, clarification = await self._semantic_contract(request, envelope)
            if clarification is not None:
                clarification.latency_ms = (time.perf_counter() - started) * 1000
                return clarification
            assert contract is not None
            registration = self.registry.resolve(contract.intent)
            registration.contract.validate_turn(contract)
            executor_args = dict(contract.constraints)
            guard_constraint_preservation(
                contract.requested_constraints,
                contract.constraints,
                registration.contract.supported_constraints,
                executor_args,
            )
            if contract.intent == "task_lookup":
                answer, data, evidence = await self._execute_lookup(contract)
            else:
                answer, data, evidence = await self._execute_search(contract)
            validation = self.validator.validate(contract, data)
            meta = {
                "stage": "H1B",
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
                "executor_id": registration.contract.executor_id,
                "executor_args": executor_args,
                "source_authority": registration.contract.source_authority,
                "oracle_id": registration.contract.oracle_id,
                "postcondition_results": validation.to_dict(),
                "execution_ready": True,
            }
            data = dict(data)
            data["_agent_core_v3"] = meta
            status = ResponseStatus.COMPLETED
            if data.get("found") is False:
                status = ResponseStatus.FAILED
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
                    "conversation_id": envelope.conversation_id,
                    "runtime_session_id": envelope.runtime_session_id,
                    "turn_id": envelope.turn_id,
                    "failure_code": exc.code.value,
                    "details": exc.details,
                    "execution_ready": False,
                }},
                warnings=[exc.code.value],
                latency_ms=(time.perf_counter() - started) * 1000,
            )
