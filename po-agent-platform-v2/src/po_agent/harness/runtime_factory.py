"""Runtime construction for fake, production AS21, and frozen AS21 sources."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from po_agent.adapters import FakeAS21Adapter, FrozenAS21Adapter, SWTRShadowBatch
from po_agent.adapters.as21 import AS21Adapter
from po_agent.adapters.hardened_production_task_api import HardenedProductionTaskApiAS21Adapter

from .core8_semantic_precision import Core8SemanticPrecisionInterpreter
from .core8_hardening import enable_core8_hardened_composite
from .correction_runtime import CorrectionAwareHarnessRuntime
from .dialogue_runtime import LLMJsonSemanticInterpreter, SemanticInterpreter
from .entity_grounding import GroundedEntityResolver, TeamDirectory
from .fail_closed_dialogue_runtime import FailClosedIntentPreservingDialogueHarnessRuntime
from .historical_wiring import enable_historical_skills
from .learned_semantics import LearnedSemanticsStore
from .live_entity_grounding import LiveGroundedEntityResolver
from .observed_runtime import ObservedHarnessRuntime
from .resilient_semantics import (
    ResilientBlindConsensusSemanticInterpreter,
    ResilientBlindRecoveryLLMJsonSemanticInterpreter,
)
from .source_aware_runtime import SourceAwareHarnessRuntime
from .source_contracts import (
    ReleaseTimelineSource,
    SourceDependencyBundle,
    SprintSnapshotSource,
    YamlTeamCompetencySource,
)
from .source_readiness import SourceReadinessReport, build_source_readiness
from .team_matching_wiring import enable_team_matching

RuntimeMode = Literal["fake", "task-api", "frozen"]


@dataclass(frozen=True)
class RuntimeBundle:
    mode: RuntimeMode
    runtime: ObservedHarnessRuntime
    adapter: AS21Adapter
    readiness: SourceReadinessReport
    dependencies: SourceDependencyBundle
    semantics: LearnedSemanticsStore | None = None


def _resolve_team_config(explicit: str | None, mode: RuntimeMode) -> Path | None:
    if explicit:
        path = Path(explicit)
        return path if path.exists() else None
    if mode != "task-api":
        return None
    candidates = (Path("../task-api/config/team_members.yaml"), Path("task-api/config/team_members.yaml"))
    return next((path for path in candidates if path.exists()), None)


def _build_runtime_with_adapter(
    adapter: AS21Adapter,
    *,
    mode: RuntimeMode,
    team_config_path: str | None = None,
    sprint_snapshots: SprintSnapshotSource | None = None,
    release_timeline: ReleaseTimelineSource | None = None,
    semantic_interpreter: SemanticInterpreter | None = None,
    learned_semantics_path: str | None = None,
) -> RuntimeBundle:
    """Build the canonical Harness stack around an already selected adapter."""
    team_path = _resolve_team_config(team_config_path, mode)
    team_source = YamlTeamCompetencySource(team_path) if team_path is not None else None
    dependencies = SourceDependencyBundle(
        sprint_snapshots=sprint_snapshots,
        team_competencies=team_source,
        release_timeline=release_timeline,
    )
    readiness = build_source_readiness(adapter, extra_facts=dependencies.facts)

    executable = SourceAwareHarnessRuntime(adapter, source_facts=readiness.available_facts)
    if mode == "task-api":
        # The production composite path must preserve every requested selector
        # and intersect by canonical task keys, not object identity.
        enable_core8_hardened_composite(executable)
    if team_source is not None and team_source.has_declared_profiles():
        enable_team_matching(executable, team_source)
    if sprint_snapshots is not None or release_timeline is not None:
        enable_historical_skills(executable, sprint_snapshots=sprint_snapshots, release_timeline=release_timeline)

    semantics = LearnedSemanticsStore(learned_semantics_path) if learned_semantics_path else None
    directory = TeamDirectory.from_yaml(team_path)
    if mode == "task-api":
        grounder = LiveGroundedEntityResolver(adapter, team=directory, semantics=semantics)
    else:
        grounder = GroundedEntityResolver(adapter, team=directory, semantics=semantics)

    selected_interpreter = semantic_interpreter
    if isinstance(semantic_interpreter, LLMJsonSemanticInterpreter):
        fast_delegate = ResilientBlindRecoveryLLMJsonSemanticInterpreter(
            semantic_interpreter.client,
            model=semantic_interpreter.model,
        )
        selected_interpreter = ResilientBlindConsensusSemanticInterpreter(fast_delegate)

    if selected_interpreter is not None:
        selected_interpreter = Core8SemanticPrecisionInterpreter(selected_interpreter)

    dialogue = FailClosedIntentPreservingDialogueHarnessRuntime(
        executable,
        interpreter=selected_interpreter,
        semantics=semantics,
        grounder=grounder,
    )
    # Negative user feedback must reopen the evidence chain before any answer
    # is treated as final. This wrapper is session-scoped and cannot promote a
    # learned rule on its own.
    dialogue = CorrectionAwareHarnessRuntime(dialogue)
    runtime = ObservedHarnessRuntime(dialogue)

    return RuntimeBundle(
        mode=mode,
        runtime=runtime,
        adapter=adapter,
        readiness=readiness,
        dependencies=dependencies,
        semantics=semantics,
    )


def build_runtime_bundle(
    mode: str = "fake",
    *,
    task_api_base_url: str = "http://localhost:8003",
    task_api_timeout_seconds: float = 30.0,
    team_config_path: str | None = None,
    sprint_snapshots: SprintSnapshotSource | None = None,
    release_timeline: ReleaseTimelineSource | None = None,
    semantic_interpreter: SemanticInterpreter | None = None,
    learned_semantics_path: str | None = None,
) -> RuntimeBundle:
    normalized = mode.strip().lower()
    if normalized == "fake":
        adapter: AS21Adapter = FakeAS21Adapter()
        selected: RuntimeMode = "fake"
    elif normalized in {"task-api", "task_api", "real"}:
        adapter = HardenedProductionTaskApiAS21Adapter(
            base_url=task_api_base_url,
            timeout_seconds=task_api_timeout_seconds,
        )
        selected = "task-api"
    else:
        raise ValueError(f"Unsupported PO_AGENT_AS21_MODE: {mode}")

    return _build_runtime_with_adapter(
        adapter,
        mode=selected,
        team_config_path=team_config_path,
        sprint_snapshots=sprint_snapshots,
        release_timeline=release_timeline,
        semantic_interpreter=semantic_interpreter,
        learned_semantics_path=learned_semantics_path,
    )


def build_frozen_runtime_bundle(
    batch: SWTRShadowBatch,
    *,
    team_config_path: str | None = None,
    sprint_snapshots: SprintSnapshotSource | None = None,
    release_timeline: ReleaseTimelineSource | None = None,
    semantic_interpreter: SemanticInterpreter | None = None,
    learned_semantics_path: str | None = None,
) -> RuntimeBundle:
    """Build the real Harness stack over a previously captured SWTR batch."""
    adapter = FrozenAS21Adapter.from_shadow_batch(batch)
    return _build_runtime_with_adapter(
        adapter,
        mode="frozen",
        team_config_path=team_config_path,
        sprint_snapshots=sprint_snapshots,
        release_timeline=release_timeline,
        semantic_interpreter=semantic_interpreter,
        learned_semantics_path=learned_semantics_path,
    )
