"""Append-only memory of governed evolution outcomes.

The memory helps future loops avoid repeatedly proposing known-bad changes. It
stores fingerprints and outcomes only; it cannot approve, execute, promote, or
mutate production state.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable


class EvolutionMemoryOutcome(str, Enum):
    APPROVAL_REQUIRED = "approval_required"
    REJECTED = "rejected"
    BLOCKED = "blocked"
    PROMOTED = "promoted"
    ROLLED_BACK = "rolled_back"
    ERROR = "error"


@dataclass(frozen=True)
class EvolutionMemoryEntry:
    memory_id: str
    created_at: str
    failure_key: str
    candidate_id: str
    proposal_id: str | None
    fingerprint: str
    outcome: EvolutionMemoryOutcome
    reasons: tuple[str, ...] = ()
    evaluation_id: str | None = None
    release_ref: str | None = None

    @classmethod
    def create(
        cls,
        *,
        failure_key: str,
        candidate_id: str,
        outcome: EvolutionMemoryOutcome,
        proposal_id: str | None = None,
        target_files: Iterable[str] = (),
        proposal_material: str = "",
        reasons: Iterable[str] = (),
        evaluation_id: str | None = None,
        release_ref: str | None = None,
    ) -> "EvolutionMemoryEntry":
        if not failure_key.strip() or not candidate_id.strip():
            raise ValueError("failure_key and candidate_id are required")
        fingerprint = evolution_fingerprint(
            failure_key=failure_key,
            target_files=target_files,
            proposal_material=proposal_material,
        )
        return cls(
            memory_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc).isoformat(),
            failure_key=failure_key.strip(),
            candidate_id=candidate_id.strip(),
            proposal_id=proposal_id.strip() if proposal_id else None,
            fingerprint=fingerprint,
            outcome=outcome,
            reasons=tuple(str(reason) for reason in reasons),
            evaluation_id=evaluation_id.strip() if evaluation_id else None,
            release_ref=release_ref.strip() if release_ref else None,
        )


def evolution_fingerprint(*, failure_key: str, target_files: Iterable[str], proposal_material: str) -> str:
    canonical = json.dumps(
        {
            "failure_key": failure_key.strip(),
            "target_files": sorted(set(str(path) for path in target_files)),
            "proposal_material": proposal_material,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class EvolutionMemoryPolicy:
    max_same_fingerprint_failures: int = 2
    block_rolled_back_fingerprint: bool = True

    def __post_init__(self) -> None:
        if self.max_same_fingerprint_failures < 1:
            raise ValueError("max_same_fingerprint_failures must be positive")


class EvolutionMemory:
    """Deterministic append-only memory and retry guard."""

    _FAILURE_OUTCOMES = {
        EvolutionMemoryOutcome.REJECTED,
        EvolutionMemoryOutcome.BLOCKED,
        EvolutionMemoryOutcome.ERROR,
    }

    def __init__(self, policy: EvolutionMemoryPolicy | None = None) -> None:
        self.policy = policy or EvolutionMemoryPolicy()
        self._entries: list[EvolutionMemoryEntry] = []
        self._ids: set[str] = set()

    def append(self, entry: EvolutionMemoryEntry) -> None:
        if entry.memory_id in self._ids:
            raise ValueError("memory entry already exists")
        self._entries.append(entry)
        self._ids.add(entry.memory_id)

    def entries_for_failure(self, failure_key: str) -> tuple[EvolutionMemoryEntry, ...]:
        return tuple(item for item in self._entries if item.failure_key == failure_key)

    def entries_for_fingerprint(self, fingerprint: str) -> tuple[EvolutionMemoryEntry, ...]:
        return tuple(item for item in self._entries if item.fingerprint == fingerprint)

    def should_attempt(self, fingerprint: str) -> tuple[bool, tuple[str, ...]]:
        prior = self.entries_for_fingerprint(fingerprint)
        failures = sum(1 for item in prior if item.outcome in self._FAILURE_OUTCOMES)
        if failures >= self.policy.max_same_fingerprint_failures:
            return False, ("known_bad_fingerprint_failure_limit",)
        if self.policy.block_rolled_back_fingerprint and any(
            item.outcome is EvolutionMemoryOutcome.ROLLED_BACK for item in prior
        ):
            return False, ("fingerprint_was_rolled_back",)
        return True, ()

    def promoted_fingerprints(self) -> frozenset[str]:
        return frozenset(item.fingerprint for item in self._entries if item.outcome is EvolutionMemoryOutcome.PROMOTED)

    def snapshot(self) -> tuple[EvolutionMemoryEntry, ...]:
        return tuple(self._entries)


class SQLiteEvolutionMemoryStore:
    """Durable append-only memory store; no update/delete methods by design."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS harness_evolution_memory (memory_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, failure_key TEXT NOT NULL, fingerprint TEXT NOT NULL, outcome TEXT NOT NULL, payload_json TEXT NOT NULL)"
        )
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_evolution_memory_failure ON harness_evolution_memory(failure_key)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_evolution_memory_fingerprint ON harness_evolution_memory(fingerprint)")
        self._conn.commit()

    def append(self, entry: EvolutionMemoryEntry) -> None:
        payload = json.dumps(asdict(entry), ensure_ascii=False, sort_keys=True, default=lambda value: value.value if isinstance(value, Enum) else str(value))
        try:
            self._conn.execute(
                "INSERT INTO harness_evolution_memory VALUES (?, ?, ?, ?, ?, ?)",
                (entry.memory_id, entry.created_at, entry.failure_key, entry.fingerprint, entry.outcome.value, payload),
            )
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"memory entry already exists: {entry.memory_id}") from exc

    def by_fingerprint(self, fingerprint: str) -> tuple[EvolutionMemoryEntry, ...]:
        rows = self._conn.execute(
            "SELECT payload_json FROM harness_evolution_memory WHERE fingerprint = ? ORDER BY created_at ASC",
            (fingerprint,),
        ).fetchall()
        result: list[EvolutionMemoryEntry] = []
        for (payload,) in rows:
            raw = json.loads(str(payload))
            result.append(
                EvolutionMemoryEntry(
                    memory_id=raw["memory_id"],
                    created_at=raw["created_at"],
                    failure_key=raw["failure_key"],
                    candidate_id=raw["candidate_id"],
                    proposal_id=raw.get("proposal_id"),
                    fingerprint=raw["fingerprint"],
                    outcome=EvolutionMemoryOutcome(raw["outcome"]),
                    reasons=tuple(raw.get("reasons", ())),
                    evaluation_id=raw.get("evaluation_id"),
                    release_ref=raw.get("release_ref"),
                )
            )
        return tuple(result)
