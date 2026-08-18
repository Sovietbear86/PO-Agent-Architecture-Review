"""Runtime construction for fake, production AS21, and frozen AS21 sources."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from po_agent.adapters import FakeAS21Adapter, FrozenAS21Adapter, SWTRShadowBatch, TaskApiAS21Adapter
from po_agent.adapters.as21 import AS21Adapter

from .dialogue_runtime import LLMJsonSemanticInterpreter, SemanticInterpreter
from .entity_grounding import GroundedEntityResolver, TeamDirectory
from .historical_wiring import enable_historical_skills
from .learned_semantics import LearnedSemanticsStore
from .observed_runtime import ObservedHarnessRuntime
from .semantic_authorization import (
    BlindConsensusSemanticInterpreter,
    BlindRecoveryLLMJsonSemanticInterpreter,
)
from .session_corrections import SessionCorrectionDialogueHarnessRuntime, SessionCorrectionStore
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
    """Build the canonical Harness stack around an already selected adapter.

    This is shared by live and frozen sources so offline SWTR evaluation executes
    the same production capability/runtime chain instead of a test-only mock.
    """
    team_path = _resolve_team_config(team_config_path, mode)
    team_source = YamlTeamCompetencySource(team_path) if team_path is not None else None
    dependencies = SourceDependencyBundle(
        sprint_snapshots=sprint_snapshots,
        team_competencies=team_source,
        release_timeline=release_timeline,
    )
    readiness = build_source_readiness(adapter, extra_facts=dependencies.facts)

    executable = SourceAwareHarnessRuntime(adapter, source_facts=readiness.available_facts)
    if team_source is not None and team_source.has_declared_profiles():
        enable_team_matching(executable, team_source)
    if sprint_snapshots is not None or release_timeline is not None:
        enable_historical_skills(executable, sprint_snapshots=sprint_snapshots, release_timeline=release_timeline)

    semantics = LearnedSemanticsStore(learned_semantics_path) if learned_semantics_path else None
    directory = TeamDirectory.from_yaml(team_path)
    grounder = GroundedEntityResolver(adapter, team=directory, semantics=semantics)

    selected_interpreter = semantic_interpreter
    if isinstance(semantic_interpreter, LLMJsonSemanticInterpreter):
        # Keep the original primary semantic pass and slot extraction, but avoid a
        # second catalog-wide recovery inside it. Blind consensus is now the single
        # recovery/authorization layer, eliminating duplicate LLM ranking work.
        fast_delegate = BlindRecoveryLLMJsonSemanticInterpreter(
            semantic_interpreter.client,
            model=semantic_interpreter.model,
        )
        selected_interpreter = BlindConsensusSemanticInterpreter(fast_delegate)

    correction_store = SessionCorrectionStore()
    dialogue = SessionCorrectionDialogueHarnessRuntime(
        executable,
        interpreter=selected_interpreter,
        semantics=semantics,
        grounder=grounder,
        correction_store=correction_store,
    )
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
        adapter = TaskApiAS21Adapter(base_url=task_api_base_url, timeout_seconds=task_api_timeout_seconds)
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
    """Build the real Harness stack over a previously captured SWTR batch.

    No live AS21/Task API object is created or retained. Therefore all capability
    reads are satisfied from the immutable frozen corpus and cannot reconnect to
    SWTR after the capture boundary has closed.
    """
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
