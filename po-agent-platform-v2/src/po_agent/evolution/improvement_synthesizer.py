"""Bounded improvement proposal synthesis for Learning Loop 013.

This module turns failure/feedback evidence into a typed proposal.  A proposal is
DATA ONLY: it cannot edit source files, mutate SkillRegistry, call AS21, or change
an active skill.  Applying a proposal belongs to an isolated candidate sandbox.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional

from po_agent.evaluation.failure import FailureCategory


class ProposalKind(str, Enum):
    ROUTING_ALIAS = "routing_alias"
    ENTITY_RULE = "entity_rule"
    PROMPT_CONSTRAINT = "prompt_constraint"
    METRIC_GUARD = "metric_guard"
    SOURCE_CONTRACT = "source_contract"
    EVIDENCE_POLICY = "evidence_policy"
    MANUAL_REVIEW = "manual_review"


@dataclass(frozen=True)
class ImprovementProposal:
    proposal_id: str
    skill_id: str
    failure_category: str
    kind: ProposalKind
    target: str
    change: Mapping[str, Any]
    evidence_ids: tuple[str, ...] = ()
    rationale: str = ""
    executable: bool = False
    requires_sandbox: bool = True
    requires_human_approval: bool = True


class ImprovementSynthesizer:
    """Create conservative candidate proposals from deterministic evidence."""

    _CATEGORY_TO_KIND = {
        FailureCategory.ROUTING_ERROR.value: ProposalKind.ROUTING_ALIAS,
        FailureCategory.ENTITY_EXTRACTION_ERROR.value: ProposalKind.ENTITY_RULE,
        FailureCategory.PROMPT_FAILURE.value: ProposalKind.PROMPT_CONSTRAINT,
        FailureCategory.METRIC_ERROR.value: ProposalKind.METRIC_GUARD,
        FailureCategory.ADAPTER_ERROR.value: ProposalKind.SOURCE_CONTRACT,
        FailureCategory.DATA_MAPPING_ERROR.value: ProposalKind.SOURCE_CONTRACT,
        FailureCategory.MISSING_EVIDENCE.value: ProposalKind.EVIDENCE_POLICY,
        FailureCategory.LLM_SCHEMA_ERROR.value: ProposalKind.PROMPT_CONSTRAINT,
        FailureCategory.LLM_HALLUCINATION.value: ProposalKind.PROMPT_CONSTRAINT,
    }

    def synthesize(
        self,
        *,
        skill_id: str,
        failure_cluster: Mapping[str, Any],
        failure_records: Iterable[Mapping[str, Any]],
    ) -> ImprovementProposal:
        records = list(failure_records)
        category = str(failure_cluster.get("category") or self._dominant_category(records) or "UNKNOWN")
        # Miner may use compound category labels; normalize to the first known one.
        normalized = self._normalize_category(category)
        kind = self._CATEGORY_TO_KIND.get(normalized, ProposalKind.MANUAL_REVIEW)
        evidence_ids = tuple(
            str(r.get("trace_id") or r.get("failure_id") or "")
            for r in records
            if r.get("trace_id") or r.get("failure_id")
        )
        cluster_id = str(failure_cluster.get("cluster_id") or "unclustered")
        proposal_id = f"lp013-{skill_id}-{cluster_id}"
        target, change = self._bounded_change(kind, failure_cluster, records)
        return ImprovementProposal(
            proposal_id=proposal_id,
            skill_id=skill_id,
            failure_category=normalized,
            kind=kind,
            target=target,
            change=change,
            evidence_ids=evidence_ids,
            rationale=str(failure_cluster.get("recommendation") or failure_cluster.get("description") or ""),
        )

    @staticmethod
    def _dominant_category(records: List[Mapping[str, Any]]) -> Optional[str]:
        counts: Dict[str, int] = {}
        for record in records:
            category = str(record.get("category") or "")
            if category:
                counts[category] = counts.get(category, 0) + 1
        return max(counts, key=counts.get) if counts else None

    @classmethod
    def _normalize_category(cls, category: str) -> str:
        for known in cls._CATEGORY_TO_KIND:
            if known in category:
                return known
        return category

    @staticmethod
    def _bounded_change(
        kind: ProposalKind,
        cluster: Mapping[str, Any],
        records: List[Mapping[str, Any]],
    ) -> tuple[str, Mapping[str, Any]]:
        examples = [
            str(r.get("query") or r.get("error_message") or r.get("reason") or "")[:240]
            for r in records[:5]
        ]
        if kind == ProposalKind.ROUTING_ALIAS:
            return "intent_router", {"operation": "add_candidate_aliases", "examples": examples}
        if kind == ProposalKind.ENTITY_RULE:
            return "entity_extractor", {"operation": "add_candidate_entity_rule", "examples": examples}
        if kind == ProposalKind.PROMPT_CONSTRAINT:
            return "semantic_interpreter", {"operation": "tighten_candidate_contract", "examples": examples}
        if kind == ProposalKind.METRIC_GUARD:
            return "deterministic_metric", {"operation": "add_candidate_guard", "examples": examples}
        if kind == ProposalKind.SOURCE_CONTRACT:
            return "source_adapter", {"operation": "review_source_contract", "examples": examples}
        if kind == ProposalKind.EVIDENCE_POLICY:
            return "evidence_grounder", {"operation": "strengthen_candidate_evidence_policy", "examples": examples}
        return "manual_review", {
            "operation": "manual_review_only",
            "cluster": str(cluster.get("cluster_id") or "unclustered"),
            "examples": examples,
        }


__all__ = ["ImprovementProposal", "ImprovementSynthesizer", "ProposalKind"]
