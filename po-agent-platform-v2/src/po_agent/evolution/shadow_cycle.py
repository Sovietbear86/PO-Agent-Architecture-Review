"""Learning Loop 013: failure -> proposal -> frozen shadow comparison.

The cycle deliberately stops before production mutation.  A caller supplies an
isolated candidate evaluator; this module verifies that baseline and candidate
were evaluated on the same frozen corpus and delegates promotion policy to the
012 LearningLoop gate.
"""
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Sequence

from po_agent.evaluation.failure import FailureStore
from po_agent.evaluation.miner import FailureMiner
from po_agent.evolution.improvement_synthesizer import ImprovementProposal, ImprovementSynthesizer
from po_agent.evolution.learning_loop import EvaluationSnapshot, PromotionDecision
from po_agent.evolution.learning_orchestrator import ControlledLearningOrchestrator
from po_agent.evolution.models import ImprovementType, SkillImprovementCandidate


@dataclass(frozen=True)
class ShadowCycleArtifact:
    skill_id: str
    proposal: ImprovementProposal
    candidate_id: str
    corpus_id: str
    baseline: EvaluationSnapshot
    candidate: EvaluationSnapshot
    decision: PromotionDecision
    failure_count: int
    production_mutations: int = 0


class LearningCycle013:
    """Create and shadow-evaluate a candidate from failure evidence."""

    def __init__(
        self,
        orchestrator: ControlledLearningOrchestrator,
        synthesizer: Optional[ImprovementSynthesizer] = None,
    ):
        self.orchestrator = orchestrator
        self.synthesizer = synthesizer or ImprovementSynthesizer()

    def build_proposal(
        self,
        *,
        skill_id: str,
        failures: Iterable[Mapping[str, Any]],
    ) -> ImprovementProposal:
        records = [dict(item) for item in failures]
        if not records:
            raise ValueError("failure evidence is required")
        report = FailureMiner(records).mine()
        if not report.clusters:
            cluster = {
                "cluster_id": "unclustered",
                "category": records[0].get("category", "UNKNOWN"),
                "count": len(records),
                "description": "Unclustered failure evidence",
                "recommendation": "manual review",
            }
        else:
            # Deterministic selection: largest cluster, then stable cluster_id.
            cluster = sorted(
                report.clusters,
                key=lambda item: (-int(item.get("count", 0)), str(item.get("cluster_id", ""))),
            )[0]
        return self.synthesizer.synthesize(
            skill_id=skill_id,
            failure_cluster=cluster,
            failure_records=records,
        )

    def run_shadow(
        self,
        *,
        skill_id: str,
        skill_version: str,
        failures: Iterable[Mapping[str, Any]],
        baseline: EvaluationSnapshot,
        candidate: EvaluationSnapshot,
        corpus_id: str,
    ) -> ShadowCycleArtifact:
        if not corpus_id.strip():
            raise ValueError("frozen corpus_id is required")
        proposal = self.build_proposal(skill_id=skill_id, failures=failures)
        candidate_record = SkillImprovementCandidate(
            candidate_id=proposal.proposal_id,
            skill_id=skill_id,
            skill_version=skill_version,
            improvement_type=self._improvement_type(proposal.failure_category),
            threshold_value=baseline.pass_rate,
            current_value=candidate.pass_rate,
            suggested_changes={
                "proposal_kind": proposal.kind.value,
                "target": proposal.target,
                "change": dict(proposal.change),
                "corpus_id": corpus_id,
            },
            feedback_samples=[],
            metric_samples=[{"failure_count": len(proposal.evidence_ids)}],
        )
        self.orchestrator.register_candidate(candidate_record)
        evidence = {
            "corpus_id": corpus_id,
            "proposal_id": proposal.proposal_id,
            "failure_evidence_ids": list(proposal.evidence_ids),
            "candidate_executable": proposal.executable,
            "candidate_requires_sandbox": proposal.requires_sandbox,
        }
        evaluated = self.orchestrator.evaluate_candidate(
            proposal.proposal_id,
            baseline,
            candidate,
            evidence=evidence,
        )
        return ShadowCycleArtifact(
            skill_id=skill_id,
            proposal=proposal,
            candidate_id=proposal.proposal_id,
            corpus_id=corpus_id,
            baseline=baseline,
            candidate=candidate,
            decision=evaluated.decision,
            failure_count=len(proposal.evidence_ids),
            production_mutations=0,
        )

    @staticmethod
    def _improvement_type(category: str) -> ImprovementType:
        mapping = {
            "ROUTING_ERROR": ImprovementType.LOW_ACCURACY,
            "ENTITY_EXTRACTION_ERROR": ImprovementType.LOW_ACCURACY,
            "PROMPT_FAILURE": ImprovementType.LOW_ACCURACY,
            "LLM_SCHEMA_ERROR": ImprovementType.HIGH_ERROR_RATE,
            "LLM_HALLUCINATION": ImprovementType.HIGH_ERROR_RATE,
            "METRIC_ERROR": ImprovementType.HIGH_ERROR_RATE,
            "ADAPTER_ERROR": ImprovementType.HIGH_ERROR_RATE,
            "DATA_MAPPING_ERROR": ImprovementType.HIGH_ERROR_RATE,
            "MISSING_EVIDENCE": ImprovementType.HIGH_CLARIFICATION_RATE,
        }
        return mapping.get(category, ImprovementType.HIGH_ERROR_RATE)


__all__ = ["LearningCycle013", "ShadowCycleArtifact"]
