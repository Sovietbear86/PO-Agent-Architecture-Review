"""Controlled Skill Forge for evidence-backed Harness evolution.

The forge converts mined failure clusters into declarative candidate artifacts.
Artifacts describe *what* should change and how it must be evaluated, but they
contain no executable patch and cannot mutate runtime, Skill Catalog or source
files.  Executable patch synthesis belongs to a later sandboxed stage.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import uuid

from .failure_miner import FailureCluster
from .improvement_candidates import ImprovementCandidate


class ForgeArtifactKind(str, Enum):
    ROUTING_METADATA = "routing_metadata"
    ENTITY_CONTEXT_POLICY = "entity_context_policy"
    EVIDENCE_SYNTHESIS_CONTRACT = "evidence_synthesis_contract"
    MANUAL_REVIEW = "manual_review"


@dataclass(frozen=True)
class ForgePolicy:
    """Bounds what Skill Forge v1 is allowed to propose."""

    max_examples: int = 20
    max_target_skills: int = 8
    require_shadow_evaluation: bool = True
    require_human_approval: bool = True

    def __post_init__(self) -> None:
        if self.max_examples < 1:
            raise ValueError("max_examples must be positive")
        if self.max_target_skills < 1:
            raise ValueError("max_target_skills must be positive")


@dataclass(frozen=True)
class SkillArtifact:
    artifact_id: str
    created_at: str
    source_failure_key: str
    source_eval_ids: tuple[str, ...]
    kind: ForgeArtifactKind
    title: str
    rationale: str
    target_skill_ids: tuple[str, ...]
    target_intents: tuple[str, ...]
    examples: tuple[str, ...]
    proposed_change: dict[str, object]
    acceptance_contract: dict[str, object]
    shadow_eval_plan: dict[str, object]
    executable: bool = False
    apply: bool = False
    requires_human_approval: bool = True

    def __post_init__(self) -> None:
        if not self.artifact_id:
            raise ValueError("artifact_id is required")
        if not self.source_failure_key:
            raise ValueError("source_failure_key is required")
        if self.executable or self.apply:
            raise ValueError("Skill Forge v1 artifacts must be non-executable and non-applying")

    def to_improvement_candidate(self) -> ImprovementCandidate:
        """Bridge the forge artifact into the existing governed lifecycle."""
        payload = {
            "forge_artifact_id": self.artifact_id,
            "artifact_kind": self.kind.value,
            "targets": {
                "skill_ids": list(self.target_skill_ids),
                "intents": list(self.target_intents),
            },
            "proposal": dict(self.proposed_change),
            "acceptance_contract": dict(self.acceptance_contract),
            "shadow_eval_plan": dict(self.shadow_eval_plan),
            "apply": False,
            "executable": False,
        }
        return ImprovementCandidate(
            candidate_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc).isoformat(),
            kind=f"forge:{self.kind.value}",
            title=self.title,
            rationale=self.rationale,
            source_failure_key=self.source_failure_key,
            source_eval_ids=self.source_eval_ids,
            proposed_change=payload,
            requires_human_approval=self.requires_human_approval,
        )


class SkillForge:
    """Generate bounded declarative improvement artifacts from failure evidence."""

    def __init__(self, policy: ForgePolicy | None = None) -> None:
        self.policy = policy or ForgePolicy()

    def forge(self, cluster: FailureCluster) -> SkillArtifact:
        if cluster.count < 1 or not cluster.eval_ids:
            raise ValueError("failure cluster must contain evidence")

        examples = tuple(cluster.queries[: self.policy.max_examples])
        targets = tuple(cluster.affected_skill_ids[: self.policy.max_target_skills])
        intents = tuple(cluster.expected_intents)
        kind, proposal = self._proposal(cluster, targets, intents)

        acceptance = {
            "must_pass_source_eval_ids": list(cluster.eval_ids),
            "must_not_increase_safety_regressions": True,
            "must_not_increase_new_code_regressions": True,
            "must_not_increase_wrong_skill_selections": True,
            "must_not_increase_hallucinated_entities": True,
            "must_not_increase_ungrounded_answers": True,
            "required_expected_intents": list(intents),
        }
        shadow_plan = {
            "mode": "baseline_vs_candidate",
            "eval_ids": list(cluster.eval_ids),
            "same_seed_for_both_runners": True,
            "require_shadow_evaluation": self.policy.require_shadow_evaluation,
            "human_approval_required": self.policy.require_human_approval,
        }

        return SkillArtifact(
            artifact_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc).isoformat(),
            source_failure_key=cluster.key,
            source_eval_ids=cluster.eval_ids,
            kind=kind,
            title=f"Forge improvement for {cluster.key}",
            rationale=(
                f"Failure cluster {cluster.key} contains {cluster.count} curated eval seed(s). "
                f"{cluster.recommendation}"
            ),
            target_skill_ids=targets,
            target_intents=intents,
            examples=examples,
            proposed_change=proposal,
            acceptance_contract=acceptance,
            shadow_eval_plan=shadow_plan,
            requires_human_approval=self.policy.require_human_approval,
        )

    @staticmethod
    def _proposal(
        cluster: FailureCluster,
        target_skills: tuple[str, ...],
        target_intents: tuple[str, ...],
    ) -> tuple[ForgeArtifactKind, dict[str, object]]:
        if cluster.category == "intent_mismatch":
            return ForgeArtifactKind.ROUTING_METADATA, {
                "operation": "propose_semantic_metadata_adjustment",
                "target_skill_ids": list(target_skills),
                "expected_intents": list(target_intents),
                "constraint": "catalog_driven_no_phrase_dictionary",
                "execution_authority": "none",
            }
        if cluster.category == "entity_resolution":
            return ForgeArtifactKind.ENTITY_CONTEXT_POLICY, {
                "operation": "propose_entity_context_contract_adjustment",
                "target_entity": cluster.key.split(":", 1)[-1],
                "constraint": "source_grounding_remains_mandatory",
                "execution_authority": "none",
            }
        if cluster.category == "answer_fact":
            return ForgeArtifactKind.EVIDENCE_SYNTHESIS_CONTRACT, {
                "operation": "propose_evidence_synthesis_contract_adjustment",
                "constraint": "source_backed_facts_only",
                "execution_authority": "none",
            }
        return ForgeArtifactKind.MANUAL_REVIEW, {
            "operation": "manual_architecture_review",
            "constraint": "no_automatic_change",
            "execution_authority": "none",
        }
