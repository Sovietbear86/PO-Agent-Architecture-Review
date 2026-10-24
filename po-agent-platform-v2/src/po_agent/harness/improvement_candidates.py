"""Controlled improvement candidates generated from mined failure evidence.

Candidates are proposals only. They are never applied to production runtime by
this module and must pass offline/shadow evaluation plus human approval.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from .failure_miner import FailureCluster


@dataclass(frozen=True)
class ImprovementCandidate:
    candidate_id: str
    created_at: str
    kind: str
    title: str
    rationale: str
    source_failure_key: str
    source_eval_ids: tuple[str, ...]
    proposed_change: dict[str, object]
    status: str = "draft"
    requires_human_approval: bool = True


class ImprovementCandidateGenerator:
    """Turns evidence clusters into bounded proposals, not executable patches."""

    def generate(self, cluster: FailureCluster) -> ImprovementCandidate:
        kind, change = self._proposal(cluster)
        return ImprovementCandidate(
            candidate_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc).isoformat(),
            kind=kind,
            title=f"Investigate {cluster.category}: {cluster.key}",
            rationale=(
                f"Observed {cluster.count} curated evaluation seed(s) in cluster "
                f"{cluster.key}. {cluster.recommendation}"
            ),
            source_failure_key=cluster.key,
            source_eval_ids=cluster.eval_ids,
            proposed_change=change,
        )

    @staticmethod
    def _proposal(cluster: FailureCluster) -> tuple[str, dict[str, object]]:
        if cluster.category == "intent_mismatch":
            return "routing_rule", {
                "action": "review_router_rule",
                "expected_intents": list(cluster.expected_intents),
                "affected_skills": list(cluster.affected_skill_ids),
                "examples": list(cluster.queries),
                "apply": False,
            }
        if cluster.category == "entity_resolution":
            return "context_rule", {
                "action": "review_entity_resolution",
                "examples": list(cluster.queries),
                "apply": False,
            }
        if cluster.category == "answer_fact":
            return "capability_or_synthesis", {
                "action": "review_evidence_or_synthesis",
                "examples": list(cluster.queries),
                "apply": False,
            }
        return "manual_triage", {
            "action": "manual_review",
            "examples": list(cluster.queries),
            "apply": False,
        }
