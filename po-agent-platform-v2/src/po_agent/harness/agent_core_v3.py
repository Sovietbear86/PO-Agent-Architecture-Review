"""Hermes-inspired Agent Core v3 foundation.

This module is intentionally additive.  It defines the immutable contracts and
validation primitives used by the v3 strangler path while the legacy Harness
remains the default runtime.  No source retrieval happens here: REAL AS21 access
continues through the existing authoritative adapters/capabilities.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Awaitable, Callable, Mapping, Protocol
import uuid

from .contracts import HarnessRequest, HarnessResponse


SOURCE_AUTHORITY_REAL_AS21 = "REAL_AS21"


class AgentCoreV3FailureCode(str, Enum):
    CONSTRAINT_LOSS = "CONSTRAINT_LOSS"
    UNSUPPORTED_CONSTRAINT = "UNSUPPORTED_CONSTRAINT"
    UNRESOLVED_CONSTRAINT = "UNRESOLVED_CONSTRAINT"
    RESULT_CONTRACT_VIOLATION = "RESULT_CONTRACT_VIOLATION"
    V3_PROCESSOR_UNAVAILABLE = "V3_PROCESSOR_UNAVAILABLE"


class AgentCoreV3ContractError(RuntimeError):
    """Typed fail-closed error raised before an invalid v3 answer can escape."""

    def __init__(self, code: AgentCoreV3FailureCode, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.details = dict(details or {})


@dataclass(frozen=True)
class SessionEnvelope:
    """Explicit separation of visible conversation, transient runtime and memory scope."""

    conversation_id: str
    runtime_session_id: str
    memory_scope_id: str | None
    turn_id: str
    parent_turn_id: str | None = None

    @classmethod
    def new_conversation(cls, *, memory_scope_id: str | None = None) -> "SessionEnvelope":
        conversation_id = str(uuid.uuid4())
        return cls(
            conversation_id=conversation_id,
            runtime_session_id=str(uuid.uuid4()),
            memory_scope_id=memory_scope_id,
            turn_id=str(uuid.uuid4()),
        )

    def next_turn(self, *, turn_id: str | None = None) -> "SessionEnvelope":
        return SessionEnvelope(
            conversation_id=self.conversation_id,
            runtime_session_id=self.runtime_session_id,
            memory_scope_id=self.memory_scope_id,
            turn_id=turn_id or str(uuid.uuid4()),
            parent_turn_id=self.turn_id,
        )


@dataclass(frozen=True)
class Postcondition:
    field: str
    operator: str
    expected: str

    def to_dict(self) -> dict[str, str]:
        return {"field": self.field, "operator": self.operator, "expected": self.expected}


@dataclass(frozen=True)
class AcceptedTurnContract:
    """Immutable handoff between semantics/grounding and deterministic execution."""

    turn_id: str
    intent: str
    constraints: Mapping[str, str]
    requested_constraints: frozenset[str]
    source_authority: str = SOURCE_AUTHORITY_REAL_AS21
    required_postconditions: tuple[Postcondition, ...] = ()
    semantic_confidence: float = 1.0

    def __post_init__(self) -> None:
        frozen_constraints = MappingProxyType({str(k): str(v) for k, v in dict(self.constraints).items() if str(v).strip()})
        object.__setattr__(self, "constraints", frozen_constraints)
        requested = frozenset(str(item) for item in self.requested_constraints)
        object.__setattr__(self, "requested_constraints", requested)
        missing = sorted(requested - set(frozen_constraints))
        if missing:
            raise AgentCoreV3ContractError(
                AgentCoreV3FailureCode.CONSTRAINT_LOSS,
                "Requested constraints disappeared before contract acceptance",
                details={"missing": missing, "constraints": dict(frozen_constraints)},
            )
        if not 0.0 <= float(self.semantic_confidence) <= 1.0:
            raise ValueError("semantic_confidence must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "intent": self.intent,
            "constraints": dict(self.constraints),
            "requested_constraints": sorted(self.requested_constraints),
            "source_authority": self.source_authority,
            "required_postconditions": [item.to_dict() for item in self.required_postconditions],
            "semantic_confidence": self.semantic_confidence,
        }


@dataclass(frozen=True)
class CapabilityContractV3:
    id: str
    version: str
    supported_constraints: frozenset[str]
    source_authority: str
    executor_id: str
    oracle_id: str | None = None
    postconditions: tuple[Postcondition, ...] = ()

    def validate_turn(self, turn: AcceptedTurnContract) -> None:
        unsupported = sorted(turn.requested_constraints - self.supported_constraints)
        if unsupported:
            raise AgentCoreV3ContractError(
                AgentCoreV3FailureCode.UNSUPPORTED_CONSTRAINT,
                f"Capability {self.id} does not support all requested constraints",
                details={"unsupported": unsupported, "capability_id": self.id},
            )
        missing = sorted(field for field in turn.requested_constraints if not str(turn.constraints.get(field, "")).strip())
        if missing:
            raise AgentCoreV3ContractError(
                AgentCoreV3FailureCode.UNRESOLVED_CONSTRAINT,
                f"Capability {self.id} received unresolved requested constraints",
                details={"missing": missing, "capability_id": self.id},
            )
        if turn.source_authority != self.source_authority:
            raise AgentCoreV3ContractError(
                AgentCoreV3FailureCode.RESULT_CONTRACT_VIOLATION,
                "Capability source authority does not match the accepted turn contract",
                details={"turn": turn.source_authority, "capability": self.source_authority},
            )


@dataclass(frozen=True)
class PostconditionCheck:
    field: str
    expected: str
    actual: str | None
    passed: bool
    entity_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "expected": self.expected,
            "actual": self.actual,
            "passed": self.passed,
            "entity_id": self.entity_id,
        }


@dataclass(frozen=True)
class ValidationResult:
    checks: tuple[PostconditionCheck, ...] = ()

    @property
    def passed(self) -> bool:
        return all(item.passed for item in self.checks)

    def to_dict(self) -> dict[str, Any]:
        return {"passed": self.passed, "checks": [item.to_dict() for item in self.checks]}


class ResultPostconditionValidator:
    """Validate factual task rows against the immutable accepted constraints."""

    _SPACE_FIELDS = ("space", "project", "project_space", "swtr_space")
    _ASSIGNEE_FIELDS = ("assignee", "assignee_login", "assignee_id", "assigned_to")

    @staticmethod
    def _value_id(value: Any) -> str | None:
        if isinstance(value, str):
            text = value.strip()
            return text or None
        if isinstance(value, Mapping):
            for key in ("code", "login", "externalId", "id", "value", "name"):
                candidate = value.get(key)
                if isinstance(candidate, (str, int)) and str(candidate).strip():
                    return str(candidate).strip()
        return None

    @classmethod
    def _extract(cls, task: Mapping[str, Any], fields: tuple[str, ...]) -> str | None:
        source_data = task.get("source_data") if isinstance(task.get("source_data"), Mapping) else {}
        for field in fields:
            if field in task:
                value = cls._value_id(task.get(field))
                if value:
                    return value
            if field in source_data:
                value = cls._value_id(source_data.get(field))
                if value:
                    return value
        return None

    @staticmethod
    def _task_rows(data: Any) -> list[Mapping[str, Any]]:
        if not isinstance(data, Mapping):
            return []
        rows = data.get("tasks")
        if not isinstance(rows, list):
            return []
        return [item for item in rows if isinstance(item, Mapping)]

    def validate(self, contract: AcceptedTurnContract, data: Any) -> ValidationResult:
        rows = self._task_rows(data)
        checks: list[PostconditionCheck] = []

        for task in rows:
            entity_id = self._value_id(task.get("key")) or self._value_id(task.get("source_id")) or self._value_id(task.get("id"))
            for field in sorted(contract.requested_constraints):
                expected = str(contract.constraints[field]).strip()
                if field in {"space", "product"}:
                    actual = self._extract(task, self._SPACE_FIELDS)
                    passed = bool(actual) and actual.casefold() == expected.casefold()
                elif field in {"assignee", "member_login"}:
                    actual = self._extract(task, self._ASSIGNEE_FIELDS)
                    passed = bool(actual) and actual.casefold() == expected.casefold()
                else:
                    # H1A only enforces task row fields for the first pilot family.
                    # Other constraints are still protected by capability support and
                    # cannot disappear; family-specific validators are added later.
                    continue
                checks.append(PostconditionCheck(field=field, expected=expected, actual=actual, passed=passed, entity_id=entity_id))

        result = ValidationResult(tuple(checks))
        if not result.passed:
            failures = [item.to_dict() for item in result.checks if not item.passed]
            raise AgentCoreV3ContractError(
                AgentCoreV3FailureCode.RESULT_CONTRACT_VIOLATION,
                "Source result violates accepted turn constraints",
                details={"failures": failures, "turn_contract": contract.to_dict()},
            )
        return result


def guard_constraint_preservation(
    requested_fields: set[str] | frozenset[str],
    grounded_constraints: Mapping[str, str],
    supported_constraints: set[str] | frozenset[str],
    executor_args: Mapping[str, str],
) -> None:
    """Fail closed if a requested constraint disappears anywhere in the handoff."""

    requested = frozenset(requested_fields)
    grounded = {key for key, value in grounded_constraints.items() if str(value).strip()}
    executor = {key for key, value in executor_args.items() if str(value).strip()}
    supported = frozenset(supported_constraints)

    if not requested <= grounded:
        raise AgentCoreV3ContractError(
            AgentCoreV3FailureCode.CONSTRAINT_LOSS,
            "Requested constraint missing after grounding",
            details={"missing": sorted(requested - grounded)},
        )
    if not requested <= supported:
        raise AgentCoreV3ContractError(
            AgentCoreV3FailureCode.UNSUPPORTED_CONSTRAINT,
            "Requested constraint is unsupported by selected capability",
            details={"unsupported": sorted(requested - supported)},
        )
    if not requested <= executor:
        raise AgentCoreV3ContractError(
            AgentCoreV3FailureCode.CONSTRAINT_LOSS,
            "Requested constraint missing from executor arguments",
            details={"missing": sorted(requested - executor)},
        )


class V3Processor(Protocol):
    async def process(self, request: HarnessRequest, *, envelope: SessionEnvelope) -> HarnessResponse: ...


PilotSelector = Callable[[HarnessRequest], bool]


class AgentCoreV3RoutingSeam:
    """Disabled-by-default strangler seam between legacy Harness and Agent Core v3.

    H1A does not route production traffic to v3.  The wrapper exists now so later
    stages can enable individual certified capability families without replacing
    the proven source/data plane or changing all callers at once.
    """

    def __init__(
        self,
        legacy: Any,
        *,
        enabled: bool = False,
        processor: V3Processor | None = None,
        pilot_selector: PilotSelector | None = None,
    ) -> None:
        self.legacy = legacy
        self.enabled = bool(enabled)
        self.processor = processor
        self.pilot_selector = pilot_selector or (lambda _request: False)

        # Preserve the runtime surface expected by ObservedHarnessRuntime.
        self.adapter = legacy.adapter
        self.router = legacy.router
        self.capabilities = legacy.capabilities
        self.skills = legacy.skills

    async def process(self, request: HarnessRequest) -> HarnessResponse:
        if not self.enabled or not self.pilot_selector(request):
            return await self.legacy.process(request)
        if self.processor is None:
            raise AgentCoreV3ContractError(
                AgentCoreV3FailureCode.V3_PROCESSOR_UNAVAILABLE,
                "Agent Core v3 routing was enabled without a v3 processor",
            )
        runtime_session_id = request.session_id or str(uuid.uuid4())
        envelope = SessionEnvelope(
            conversation_id=runtime_session_id,
            runtime_session_id=runtime_session_id,
            memory_scope_id=None,
            turn_id=str(uuid.uuid4()),
        )
        return await self.processor.process(request, envelope=envelope)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.legacy, name)
