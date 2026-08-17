"""Bounded resource accounting for autonomous Harness evolution.

The budget object is intentionally deterministic and side-effect free apart from
its local counters.  It prevents unbounded repair loops, runaway LLM usage and
excessive candidate generation.  Exhaustion always fails closed.
"""
from __future__ import annotations

from dataclasses import dataclass
import time


@dataclass(frozen=True)
class EvolutionBudgetPolicy:
    max_clusters: int = 4
    max_candidates: int = 4
    max_attempts_per_candidate: int = 2
    max_llm_calls: int = 40
    max_elapsed_seconds: float = 900.0

    def __post_init__(self) -> None:
        if min(
            self.max_clusters,
            self.max_candidates,
            self.max_attempts_per_candidate,
            self.max_llm_calls,
        ) < 1:
            raise ValueError("evolution budget integer limits must be positive")
        if self.max_elapsed_seconds <= 0:
            raise ValueError("max_elapsed_seconds must be positive")


@dataclass(frozen=True)
class EvolutionBudgetSnapshot:
    clusters_seen: int
    candidates_created: int
    patch_attempts: int
    llm_calls: int
    elapsed_seconds: float


class EvolutionBudget:
    """Mutable counter set with fail-closed limit checks."""

    def __init__(
        self,
        policy: EvolutionBudgetPolicy | None = None,
        *,
        clock=time.monotonic,
    ) -> None:
        self.policy = policy or EvolutionBudgetPolicy()
        self._clock = clock
        self._started = float(clock())
        self._clusters_seen = 0
        self._candidates_created = 0
        self._patch_attempts = 0
        self._llm_calls = 0

    def claim_cluster(self) -> None:
        self._check_time()
        if self._clusters_seen >= self.policy.max_clusters:
            raise BudgetExceeded("cluster budget exhausted")
        self._clusters_seen += 1

    def claim_candidate(self) -> None:
        self._check_time()
        if self._candidates_created >= self.policy.max_candidates:
            raise BudgetExceeded("candidate budget exhausted")
        self._candidates_created += 1

    def claim_patch_attempt(self, attempts_for_candidate: int) -> None:
        self._check_time()
        if attempts_for_candidate >= self.policy.max_attempts_per_candidate:
            raise BudgetExceeded("candidate patch-attempt budget exhausted")
        self._patch_attempts += 1

    def claim_llm_calls(self, count: int = 1) -> None:
        if count < 0:
            raise ValueError("LLM call count cannot be negative")
        self._check_time()
        if self._llm_calls + count > self.policy.max_llm_calls:
            raise BudgetExceeded("LLM-call budget exhausted")
        self._llm_calls += count

    def snapshot(self) -> EvolutionBudgetSnapshot:
        now = float(self._clock())
        return EvolutionBudgetSnapshot(
            clusters_seen=self._clusters_seen,
            candidates_created=self._candidates_created,
            patch_attempts=self._patch_attempts,
            llm_calls=self._llm_calls,
            elapsed_seconds=max(0.0, now - self._started),
        )

    def _check_time(self) -> None:
        if float(self._clock()) - self._started > self.policy.max_elapsed_seconds:
            raise BudgetExceeded("evolution elapsed-time budget exhausted")


class BudgetExceeded(RuntimeError):
    """Raised when autonomous evolution reaches a configured hard limit."""
