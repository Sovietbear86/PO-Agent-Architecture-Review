from __future__ import annotations

import pytest

from po_agent.harness.evolution_budget import (
    BudgetExceeded,
    EvolutionBudget,
    EvolutionBudgetPolicy,
)


def test_budget_counts_are_bounded() -> None:
    budget = EvolutionBudget(
        EvolutionBudgetPolicy(
            max_clusters=1,
            max_candidates=1,
            max_attempts_per_candidate=1,
            max_llm_calls=2,
            max_elapsed_seconds=100,
        )
    )
    budget.claim_cluster()
    budget.claim_candidate()
    budget.claim_patch_attempt(0)
    budget.claim_llm_calls(2)
    snap = budget.snapshot()
    assert snap.clusters_seen == 1
    assert snap.candidates_created == 1
    assert snap.patch_attempts == 1
    assert snap.llm_calls == 2
    with pytest.raises(BudgetExceeded):
        budget.claim_cluster()
    with pytest.raises(BudgetExceeded):
        budget.claim_candidate()
    with pytest.raises(BudgetExceeded):
        budget.claim_patch_attempt(1)
    with pytest.raises(BudgetExceeded):
        budget.claim_llm_calls(1)


def test_budget_elapsed_time_fails_closed() -> None:
    now = [0.0]
    budget = EvolutionBudget(
        EvolutionBudgetPolicy(max_elapsed_seconds=1.0),
        clock=lambda: now[0],
    )
    now[0] = 2.0
    with pytest.raises(BudgetExceeded):
        budget.claim_cluster()


def test_negative_llm_claim_rejected() -> None:
    budget = EvolutionBudget()
    with pytest.raises(ValueError):
        budget.claim_llm_calls(-1)
