"""Runtime construction for fake, production AS21, and frozen AS21 sources."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from po_agent.adapters import FakeAS21Adapter, FrozenAS21Adapter, SWTRShadowBatch
from po_agent.adapters.as21 import AS21Adapter
from po_agent.adapters.evidence_validated_task_api import EvidenceValidatedProductionTaskApiAS21Adapter
from .agent_core_v3 import AgentCoreV3RoutingSeam
from .agent_core_v3_pilot import AgentCoreV3PilotProcessor, AgentCoreV3PilotSelector
from .core8_semantic_precision import Core8SemanticPrecisionInterpreter
from .core8_hardening import enable_core8_hardened_composite
from .correction_runtime import CorrectionAwareHarnessRuntime
from .dialogue_runtime import LLMJsonSemanticInterpreter, SemanticInterpreter
from .entity_grounding import GroundedEntityResolver, TeamDirectory
from .fail_closed_dialogue_runtime import FailClosedIntentPreservingDialogueHarnessRuntime
from .historical_wiring import enable_historical_skills
from .learned_semantics import LearnedSemanticsStore
from .observed_runtime import ObservedHarnessRuntime
from .production_entity_grounding_v2 import ProductionEntityResolverV2
from .resilient_semantics import ResilientBlindConsensusSemanticInterpreter, ResilientBlindRecoveryLLMJsonSemanticInterpreter
from .semantic_core_v2 import ConversationAwareSemanticInterpreter, FailClosedSemanticInterpreter, LLMFirstSemanticInterpreter
from .semantic_slot_recovery import RecoveringLLMFirstSemanticInterpreter
from .semantic_correction_runtime_v2 import SemanticCorrectionRuntimeV2
from .source_aware_runtime import SourceAwareHarnessRuntime
from .source_contracts import ReleaseTimelineSource, SourceDependencyBundle, SprintSnapshotSource, YamlTeamCompetencySource
from .source_readiness import SourceReadinessReport, build_source_readiness
from .team_matching_wiring import enable_team_matching
RuntimeMode=Literal["fake","task-api","frozen"]
@dataclass(frozen=True)
class RuntimeBundle:
    mode:RuntimeMode; runtime:ObservedHarnessRuntime; adapter:AS21Adapter; readiness:SourceReadinessReport; dependencies:SourceDependencyBundle; semantics:LearnedSemanticsStore|None=None

def _resolve_team_config(explicit,mode):
    if explicit:
        p=Path(explicit); return p if p.exists() else None
    if mode!="task-api": return None
    return next((p for p in (Path("../task-api/config/team_members.yaml"),Path("task-api/config/team_members.yaml")) if p.exists()),None)

def _build_runtime_with_adapter(adapter:AS21Adapter,*,mode:RuntimeMode,team_config_path=None,sprint_snapshots=None,release_timeline=None,semantic_interpreter=None,learned_semantics_path=None,agent_core_v3_enabled:bool=False)->RuntimeBundle:
    team_path=_resolve_team_config(team_config_path,mode); team_source=YamlTeamCompetencySource(team_path) if team_path is not None else None
    dependencies=SourceDependencyBundle(sprint_snapshots=sprint_snapshots,team_competencies=team_source,release_timeline=release_timeline); readiness=build_source_readiness(adapter,extra_facts=dependencies.facts)
    executable=SourceAwareHarnessRuntime(adapter,source_facts=readiness.available_facts)
    if mode=="task-api": enable_core8_hardened_composite(executable)
    if team_source is not None and team_source.has_declared_profiles(): enable_team_matching(executable,team_source)
    if sprint_snapshots is not None or release_timeline is not None: enable_historical_skills(executable,sprint_snapshots=sprint_snapshots,release_timeline=release_timeline)
    semantics=LearnedSemanticsStore(learned_semantics_path) if learned_semantics_path else None; directory=TeamDirectory.from_yaml(team_path)
    grounder=ProductionEntityResolverV2(adapter,team=directory,semantics=semantics) if mode=="task-api" else GroundedEntityResolver(adapter,team=directory,semantics=semantics)
    if mode=="task-api":
        if isinstance(semantic_interpreter,LLMJsonSemanticInterpreter): selected_interpreter=ConversationAwareSemanticInterpreter(RecoveringLLMFirstSemanticInterpreter(semantic_interpreter.client,model=semantic_interpreter.model))
        elif isinstance(semantic_interpreter,ConversationAwareSemanticInterpreter): selected_interpreter=semantic_interpreter
        elif isinstance(semantic_interpreter,LLMFirstSemanticInterpreter): selected_interpreter=ConversationAwareSemanticInterpreter(RecoveringLLMFirstSemanticInterpreter(semantic_interpreter.client,model=semantic_interpreter.model))
        else: selected_interpreter=FailClosedSemanticInterpreter()
    else:
        selected_interpreter=semantic_interpreter
        if isinstance(semantic_interpreter,LLMJsonSemanticInterpreter): selected_interpreter=ResilientBlindConsensusSemanticInterpreter(ResilientBlindRecoveryLLMJsonSemanticInterpreter(semantic_interpreter.client,model=semantic_interpreter.model))
        if selected_interpreter is not None: selected_interpreter=Core8SemanticPrecisionInterpreter(selected_interpreter)
    dialogue=FailClosedIntentPreservingDialogueHarnessRuntime(executable,interpreter=selected_interpreter,semantics=semantics,grounder=grounder)
    if mode=="task-api" and isinstance(selected_interpreter,ConversationAwareSemanticInterpreter): dialogue=SemanticCorrectionRuntimeV2(dialogue,selected_interpreter)
    else: dialogue=CorrectionAwareHarnessRuntime(dialogue)
    processor=None; selector=None
    if mode=="task-api" and agent_core_v3_enabled:
        processor=AgentCoreV3PilotProcessor(adapter,interpreter=selected_interpreter,grounder=grounder); selector=AgentCoreV3PilotSelector()
    dialogue=AgentCoreV3RoutingSeam(dialogue,enabled=agent_core_v3_enabled,processor=processor,pilot_selector=selector)
    return RuntimeBundle(mode,ObservedHarnessRuntime(dialogue),adapter,readiness,dependencies,semantics)

def build_runtime_bundle(mode="fake",*,task_api_base_url="http://localhost:8003",task_api_timeout_seconds=30.0,team_config_path=None,sprint_snapshots=None,release_timeline=None,semantic_interpreter=None,learned_semantics_path=None,agent_core_v3_enabled=False):
    normalized=mode.strip().lower()
    if normalized=="fake": adapter=FakeAS21Adapter(); selected="fake"
    elif normalized in {"task-api","task_api","real"}: adapter=EvidenceValidatedProductionTaskApiAS21Adapter(base_url=task_api_base_url,timeout_seconds=task_api_timeout_seconds); selected="task-api"
    else: raise ValueError(f"Unsupported PO_AGENT_AS21_MODE: {mode}")
    return _build_runtime_with_adapter(adapter,mode=selected,team_config_path=team_config_path,sprint_snapshots=sprint_snapshots,release_timeline=release_timeline,semantic_interpreter=semantic_interpreter,learned_semantics_path=learned_semantics_path,agent_core_v3_enabled=agent_core_v3_enabled)

def build_frozen_runtime_bundle(batch:SWTRShadowBatch,*,team_config_path=None,sprint_snapshots=None,release_timeline=None,semantic_interpreter=None,learned_semantics_path=None,agent_core_v3_enabled=False):
    return _build_runtime_with_adapter(FrozenAS21Adapter.from_shadow_batch(batch),mode="frozen",team_config_path=team_config_path,sprint_snapshots=sprint_snapshots,release_timeline=release_timeline,semantic_interpreter=semantic_interpreter,learned_semantics_path=learned_semantics_path,agent_core_v3_enabled=agent_core_v3_enabled)
