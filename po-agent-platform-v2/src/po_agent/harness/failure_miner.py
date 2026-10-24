"""Deterministic failure mining over candidate evaluation seeds.

Mining groups repeated failure evidence. It proposes what deserves attention but
never edits prompts, routing rules or capabilities.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .eval_store import EvalSeed


@dataclass(frozen=True)
class FailureCluster:
    key: str
    category: str
    count: int
    eval_ids: tuple[str, ...]
    queries: tuple[str, ...]
    expected_intents: tuple[str, ...]
    affected_skill_ids: tuple[str, ...]
    recommendation: str


class FailureMiner:
    """Groups evidence into bounded, explainable clusters."""

    def mine(self, seeds: list[EvalSeed], min_occurrences: int = 1) -> list[FailureCluster]:
        buckets: dict[tuple[str, str], list[EvalSeed]] = defaultdict(list)
        for seed in seeds:
            category, target = self._classification(seed)
            buckets[(category, target)].append(seed)

        clusters: list[FailureCluster] = []
        for (category, target), items in buckets.items():
            if len(items) < min_occurrences:
                continue
            skills = sorted({str(i.source_versions.get("skill_id")) for i in items if i.source_versions.get("skill_id")})
            intents = sorted({i.expected_intent for i in items if i.expected_intent})
            clusters.append(
                FailureCluster(
                    key=f"{category}:{target}",
                    category=category,
                    count=len(items),
                    eval_ids=tuple(i.eval_id for i in items),
                    queries=tuple(i.query for i in items),
                    expected_intents=tuple(intents),
                    affected_skill_ids=tuple(skills),
                    recommendation=self._recommendation(category, target, len(items)),
                )
            )
        return sorted(clusters, key=lambda c: (-c.count, c.key))

    @staticmethod
    def _classification(seed: EvalSeed) -> tuple[str, str]:
        if seed.expected_intent:
            actual = str(seed.source_versions.get("skill_id") or "unknown")
            return "intent_mismatch", f"{actual}->{seed.expected_intent}"
        if seed.expected_entity:
            return "entity_resolution", seed.expected_entity
        if seed.expected_facts:
            return "answer_fact", seed.expected_facts[0][:80]
        return "uncategorized", "manual_review"

    @staticmethod
    def _recommendation(category: str, target: str, count: int) -> str:
        if category == "intent_mismatch":
            return f"Review deterministic routing for {target}; reproduce against {count} eval seed(s) before proposing a rule change."
        if category == "entity_resolution":
            return f"Review entity/context resolution for {target}; add regression coverage before any resolver change."
        if category == "answer_fact":
            return "Review capability evidence/synthesis; do not patch the answer without a source-backed regression case."
        return "Manual triage required before creating an improvement candidate."
