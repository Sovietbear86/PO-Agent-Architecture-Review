"""Hermes-inspired Agent Core v3 foundation.

This module is intentionally additive.  It defines the immutable contracts and
validation primitives used by the v3 strangler path while the legacy Harness
remains the default runtime.  No source retrieval happens here: REAL AS21 access
continues through the existing authoritative adapters/capabilities.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Callable, Mapping, Protocol
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
    def __init__(self, code: AgentCoreV3FailureCode, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message); self.code = code; self.details = dict(details or {})

@dataclass(frozen=True)
class SessionEnvelope:
    conversation_id: str; runtime_session_id: str; memory_scope_id: str | None; turn_id: str; parent_turn_id: str | None = None
    @classmethod
    def new_conversation(cls, *, memory_scope_id: str | None = None) -> "SessionEnvelope":
        cid=str(uuid.uuid4()); return cls(cid,str(uuid.uuid4()),memory_scope_id,str(uuid.uuid4()))
    def next_turn(self, *, turn_id: str | None = None) -> "SessionEnvelope":
        return SessionEnvelope(self.conversation_id,self.runtime_session_id,self.memory_scope_id,turn_id or str(uuid.uuid4()),self.turn_id)

@dataclass(frozen=True)
class Postcondition:
    field:str; operator:str; expected:str
    def to_dict(self): return {"field":self.field,"operator":self.operator,"expected":self.expected}

@dataclass(frozen=True)
class AcceptedTurnContract:
    turn_id:str; intent:str; constraints:Mapping[str,str]; requested_constraints:frozenset[str]; source_authority:str=SOURCE_AUTHORITY_REAL_AS21; required_postconditions:tuple[Postcondition,...]=(); semantic_confidence:float=1.0
    def __post_init__(self):
        frozen=MappingProxyType({str(k):str(v) for k,v in dict(self.constraints).items() if str(v).strip()}); object.__setattr__(self,"constraints",frozen)
        requested=frozenset(str(x) for x in self.requested_constraints); object.__setattr__(self,"requested_constraints",requested)
        missing=sorted(requested-set(frozen))
        if missing: raise AgentCoreV3ContractError(AgentCoreV3FailureCode.CONSTRAINT_LOSS,"Requested constraints disappeared before contract acceptance",details={"missing":missing,"constraints":dict(frozen)})
        if not 0<=float(self.semantic_confidence)<=1: raise ValueError("semantic_confidence must be between 0 and 1")
    def to_dict(self): return {"turn_id":self.turn_id,"intent":self.intent,"constraints":dict(self.constraints),"requested_constraints":sorted(self.requested_constraints),"source_authority":self.source_authority,"required_postconditions":[x.to_dict() for x in self.required_postconditions],"semantic_confidence":self.semantic_confidence}

@dataclass(frozen=True)
class CapabilityContractV3:
    id:str; version:str; supported_constraints:frozenset[str]; source_authority:str; executor_id:str; oracle_id:str|None=None; postconditions:tuple[Postcondition,...]=()
    def validate_turn(self, turn:AcceptedTurnContract):
        unsupported=sorted(turn.requested_constraints-self.supported_constraints)
        if unsupported: raise AgentCoreV3ContractError(AgentCoreV3FailureCode.UNSUPPORTED_CONSTRAINT,f"Capability {self.id} does not support all requested constraints",details={"unsupported":unsupported,"capability_id":self.id})
        missing=sorted(f for f in turn.requested_constraints if not str(turn.constraints.get(f,"")).strip())
        if missing: raise AgentCoreV3ContractError(AgentCoreV3FailureCode.UNRESOLVED_CONSTRAINT,f"Capability {self.id} received unresolved requested constraints",details={"missing":missing,"capability_id":self.id})
        if turn.source_authority!=self.source_authority: raise AgentCoreV3ContractError(AgentCoreV3FailureCode.RESULT_CONTRACT_VIOLATION,"Capability source authority does not match the accepted turn contract")

@dataclass(frozen=True)
class PostconditionCheck:
    field:str; expected:str; actual:str|None; passed:bool; entity_id:str|None=None
    def to_dict(self): return {"field":self.field,"expected":self.expected,"actual":self.actual,"passed":self.passed,"entity_id":self.entity_id}
@dataclass(frozen=True)
class ValidationResult:
    checks:tuple[PostconditionCheck,...]=()
    @property
    def passed(self): return all(x.passed for x in self.checks)
    def to_dict(self): return {"passed":self.passed,"checks":[x.to_dict() for x in self.checks]}

class ResultPostconditionValidator:
    _SPACE_FIELDS=("space","project","project_space","swtr_space"); _ASSIGNEE_FIELDS=("assignee_login","assignee_id","assigned_to","assignee")
    @staticmethod
    def _value_id(value):
        if isinstance(value,str): return value.strip() or None
        if isinstance(value,Mapping):
            for k in ("code","login","externalId","id","value","name"):
                c=value.get(k)
                if isinstance(c,(str,int)) and str(c).strip(): return str(c).strip()
        return None
    @classmethod
    def _extract(cls,task,fields):
        sd=task.get("source_data") if isinstance(task.get("source_data"),Mapping) else {}
        for f in fields:
            for obj in (task,sd):
                if f in obj:
                    v=cls._value_id(obj.get(f))
                    if v:return v
        return None
    @staticmethod
    def _task_rows(data):
        if not isinstance(data,Mapping): return []
        rows=data.get("tasks"); return [x for x in rows if isinstance(x,Mapping)] if isinstance(rows,list) else []
    def validate(self,contract,data):
        rows=self._task_rows(data); checks=[]
        for task in rows:
            entity=self._value_id(task.get("key")) or self._value_id(task.get("source_id")) or self._value_id(task.get("id"))
            for field in sorted(contract.requested_constraints):
                expected=str(contract.constraints[field]).strip(); actual=None; passed=True
                if field in {"space","product"}: actual=self._extract(task,self._SPACE_FIELDS); passed=bool(actual) and actual.casefold()==expected.casefold()
                elif field in {"assignee","member_login"}: actual=self._extract(task,self._ASSIGNEE_FIELDS); passed=bool(actual) and actual.casefold()==expected.casefold()
                elif field=="task_key": actual=entity; passed=bool(actual) and actual.casefold()==expected.casefold()
                elif field=="status":
                    actual=str(task.get("status") or task.get("status_category") or "").strip(); exp=expected.casefold()
                    if exp in {"not_completed","open_tasks","unresolved","active"}: passed=str(task.get("status_category") or "").casefold() not in {"done","completed","closed"} and str(task.get("status") or "").casefold() not in {"closed","resolved","done","completed"}
                    else: passed=exp in str(task.get("status") or "").casefold() or exp in str(task.get("status_category") or "").casefold()
                else: continue
                checks.append(PostconditionCheck(field,expected,actual,passed,entity))
        result=ValidationResult(tuple(checks))
        if not result.passed: raise AgentCoreV3ContractError(AgentCoreV3FailureCode.RESULT_CONTRACT_VIOLATION,"Source result violates accepted turn constraints",details={"failures":[x.to_dict() for x in result.checks if not x.passed],"turn_contract":contract.to_dict()})
        return result

def guard_constraint_preservation(requested_fields,grounded_constraints,supported_constraints,executor_args):
    requested=frozenset(requested_fields); grounded={k for k,v in grounded_constraints.items() if str(v).strip()}; supported=frozenset(supported_constraints); executor={k for k,v in executor_args.items() if str(v).strip()}
    if not requested<=grounded: raise AgentCoreV3ContractError(AgentCoreV3FailureCode.CONSTRAINT_LOSS,"Requested constraint missing after grounding",details={"missing":sorted(requested-grounded)})
    if not requested<=supported: raise AgentCoreV3ContractError(AgentCoreV3FailureCode.UNSUPPORTED_CONSTRAINT,"Requested constraint is unsupported by selected capability",details={"unsupported":sorted(requested-supported)})
    if not requested<=executor: raise AgentCoreV3ContractError(AgentCoreV3FailureCode.CONSTRAINT_LOSS,"Requested constraint missing from executor arguments",details={"missing":sorted(requested-executor)})

class V3Processor(Protocol):
    async def process(self,request:HarnessRequest,*,envelope:SessionEnvelope)->HarnessResponse:...
PilotSelector=Callable[[HarnessRequest],bool]
class AgentCoreV3RoutingSeam:
    def __init__(self,legacy:Any,*,enabled:bool=False,processor:V3Processor|None=None,pilot_selector:PilotSelector|None=None):
        self.legacy=legacy; self.enabled=bool(enabled); self.processor=processor; self.pilot_selector=pilot_selector or (lambda _r:False); self.adapter=legacy.adapter; self.router=legacy.router; self.capabilities=legacy.capabilities; self.skills=legacy.skills
    async def process(self,request):
        if not self.enabled or not self.pilot_selector(request): return await self.legacy.process(request)
        if self.processor is None: raise AgentCoreV3ContractError(AgentCoreV3FailureCode.V3_PROCESSOR_UNAVAILABLE,"Agent Core v3 routing was enabled without a v3 processor")
        sid=request.session_id or str(uuid.uuid4()); envelope=SessionEnvelope(sid,sid,None,str(uuid.uuid4())); return await self.processor.process(request,envelope=envelope)
    def __getattr__(self,name): return getattr(self.legacy,name)
