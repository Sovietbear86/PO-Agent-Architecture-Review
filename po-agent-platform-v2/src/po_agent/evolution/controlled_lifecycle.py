"""Human-approved candidate lifecycle with explicit rollback for Learning Loop 014.

This component mutates only the SkillRegistry instance supplied by the caller.
It never talks to AS21 and never approves a candidate on its own.  The caller
must present a green shadow-evaluation artifact and explicit human approval.
"""
from dataclasses import dataclass
from typing import Optional

from po_agent.evolution.learning_loop import GateDecision
from po_agent.evolution.learning_orchestrator import CandidateEvaluationArtifact
from po_agent.skill.models import SkillStatus
from po_agent.skill.registry import SkillRegistry


@dataclass(frozen=True)
class PromotionReceipt:
    skill_id: str
    previous_version: str
    promoted_version: str
    approved_by: str


@dataclass(frozen=True)
class RollbackReceipt:
    skill_id: str
    restored_version: str
    rolled_back_version: str
    approved_by: str


class ControlledSkillLifecycle:
    """Apply a reviewed candidate to a registry and allow deterministic rollback."""

    def __init__(self, registry: SkillRegistry):
        self.registry = registry
        self._last_promotion: dict[str, PromotionReceipt] = {}

    def promote(
        self,
        *,
        artifact: CandidateEvaluationArtifact,
        candidate_version: str,
        approved_by: str,
        human_approved: bool,
    ) -> PromotionReceipt:
        if not human_approved or not approved_by.strip():
            raise PermissionError("explicit human approval is required")
        if artifact.decision.decision != GateDecision.RECOMMEND:
            raise ValueError("only a RECOMMEND artifact can be promoted")
        if artifact.decision.requires_human_approval is not True:
            raise ValueError("promotion artifact must retain the human-approval boundary")

        active = self.registry.get_active_skill(artifact.skill_id)
        if active is None:
            raise KeyError(f"active skill not found: {artifact.skill_id}")
        candidate = self.registry.get_skill_version(artifact.skill_id, candidate_version)
        if candidate is None:
            raise KeyError(f"candidate version not found: {artifact.skill_id} {candidate_version}")
        if candidate.status != SkillStatus.CANDIDATE:
            raise ValueError("target version is not a candidate")

        previous_version = active.version
        if not self.registry.promote_candidate(artifact.skill_id, candidate_version, approved_by):
            raise RuntimeError("registry promotion failed")

        receipt = PromotionReceipt(
            skill_id=artifact.skill_id,
            previous_version=previous_version,
            promoted_version=candidate_version,
            approved_by=approved_by,
        )
        self._last_promotion[artifact.skill_id] = receipt
        return receipt

    def rollback(self, *, skill_id: str, approved_by: str) -> RollbackReceipt:
        if not approved_by.strip():
            raise PermissionError("explicit human approval is required for rollback")
        receipt = self._last_promotion.get(skill_id)
        if receipt is None:
            raise KeyError(f"no promotion receipt for skill: {skill_id}")

        current = self.registry.get_active_skill(skill_id)
        previous = self.registry.get_skill_version(skill_id, receipt.previous_version)
        promoted = self.registry.get_skill_version(skill_id, receipt.promoted_version)
        if current is None or previous is None or promoted is None:
            raise RuntimeError("registry state is incomplete for rollback")
        if current.version != receipt.promoted_version:
            raise RuntimeError("active version changed after promotion; refusing unsafe rollback")

        promoted.deprecate()
        previous.activate(approved_by)
        rollback = RollbackReceipt(
            skill_id=skill_id,
            restored_version=previous.version,
            rolled_back_version=promoted.version,
            approved_by=approved_by,
        )
        del self._last_promotion[skill_id]
        return rollback


__all__ = ["ControlledSkillLifecycle", "PromotionReceipt", "RollbackReceipt"]
