"""Append-only memory of governed evolution outcomes.

The memory helps future loops avoid repeatedly proposing known-bad changes. It
stores fingerprints and outcomes only; it cannot approve, execute, promote, or
mutate production state.

Trust model
-----------
``EvolutionMemory`` is a read-oriented facade. Mutable state and write
capabilities live in module-private registries and are deliberately absent from
the object graph handed to orchestration/runtime callers. This is a practical
Python trust boundary, not a claim that arbitrary code execution inside the
trusted interpreter can be made safe: code able to inspect/modify module globals
is outside the threat model and must already be isolated by the HARD_OS sandbox.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
import weakref
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


class EvolutionMemoryWriteAuthority:
    """Opaque process-local capability owned by a trusted lifecycle boundary.

    The capability is intentionally non-copyable and non-serializable. Production
    orchestration does not place it on ``EvolutionMemory``, loop objects, bound
    methods, closures, or callbacks reachable from untrusted runtime references.
    """

    __slots__ = ("_nonce",)

    def __init__(self) -> None:
        self._nonce = uuid.uuid4().hex

    def __getstate__(self):
        raise TypeError("EvolutionMemoryWriteAuthority cannot be serialized")

    def __reduce__(self):
        raise TypeError("EvolutionMemoryWriteAuthority cannot be serialized")

    def __reduce_ex__(self, protocol):
        raise TypeError("EvolutionMemoryWriteAuthority cannot be serialized")

    def __copy__(self):
        raise TypeError("EvolutionMemoryWriteAuthority cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("EvolutionMemoryWriteAuthority cannot be copied")


@dataclass(frozen=True)
class _MemoryState:
    entries: tuple[EvolutionMemoryEntry, ...] = ()
    ids: frozenset[str] = frozenset()


# Security-sensitive mutable state is intentionally outside EvolutionMemory's
# instance graph. Weak registries also avoid extending object lifetime.
_MEMORY_STATE = weakref.WeakKeyDictionary()
_MEMORY_AUTHORITIES = weakref.WeakKeyDictionary()
_TRUSTED_BOUND_MEMORIES = weakref.WeakSet()
_SQLITE_AUTHORITIES = weakref.WeakKeyDictionary()


def _state_for(memory: "EvolutionMemory") -> _MemoryState:
    state = _MEMORY_STATE.get(memory)
    if state is None:
        state = _MemoryState()
        _MEMORY_STATE[memory] = state
    return state


def _replace_state(memory: "EvolutionMemory", state: _MemoryState) -> None:
    _MEMORY_STATE[memory] = state


def _append_verified(memory: "EvolutionMemory", entry: EvolutionMemoryEntry) -> None:
    """Append to already-authorized memory without exposing a reusable capability."""
    state = _state_for(memory)
    if entry.memory_id in state.ids:
        raise ValueError("memory entry already exists")
    _replace_state(
        memory,
        _MemoryState(
            entries=(*state.entries, entry),
            ids=state.ids | frozenset((entry.memory_id,)),
        ),
    )


class EvolutionMemory:
    """Deterministic append-only memory and retry guard.

    The facade itself contains only policy. History is returned as immutable
    tuples and no mutable collection or write authority is reachable from this
    object. ``write_authority`` remains supported for explicit trusted adapters
    and tests, but the authority is registered externally rather than stored on
    the instance.
    """

    __slots__ = ("policy", "__weakref__")

    _FAILURE_OUTCOMES = {
        EvolutionMemoryOutcome.REJECTED,
        EvolutionMemoryOutcome.BLOCKED,
        EvolutionMemoryOutcome.ERROR,
    }

    def __init__(
        self,
        policy: EvolutionMemoryPolicy | None = None,
        *,
        write_authority: EvolutionMemoryWriteAuthority | None = None,
    ) -> None:
        self.policy = policy or EvolutionMemoryPolicy()
        _MEMORY_STATE[self] = _MemoryState()
        if write_authority is not None:
            _MEMORY_AUTHORITIES[self] = write_authority

    def append(
        self,
        entry: EvolutionMemoryEntry,
        *,
        authority: EvolutionMemoryWriteAuthority | None = None,
    ) -> None:
        expected = _MEMORY_AUTHORITIES.get(self)
        if expected is None or authority is not expected:
            raise PermissionError("trusted evolution memory write authority required")
        _append_verified(self, entry)

    def entries_for_failure(self, failure_key: str) -> tuple[EvolutionMemoryEntry, ...]:
        return tuple(item for item in _state_for(self).entries if item.failure_key == failure_key)

    def entries_for_fingerprint(self, fingerprint: str) -> tuple[EvolutionMemoryEntry, ...]:
        return tuple(item for item in _state_for(self).entries if item.fingerprint == fingerprint)

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
        return frozenset(
            item.fingerprint
            for item in _state_for(self).entries
            if item.outcome is EvolutionMemoryOutcome.PROMOTED
        )

    def snapshot(self) -> tuple[EvolutionMemoryEntry, ...]:
        return tuple(_state_for(self).entries)


class SQLiteEvolutionMemoryStore:
    """Durable append-only memory store with externally registered authority."""

    __slots__ = ("_conn", "__weakref__")

    def __init__(
        self,
        db_path: str = ":memory:",
        *,
        write_authority: EvolutionMemoryWriteAuthority | None = None,
    ) -> None:
        if write_authority is not None:
            _SQLITE_AUTHORITIES[self] = write_authority
        self._conn = sqlite3.connect(db_path, isolation_level=None)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS harness_evolution_memory (memory_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, failure_key TEXT NOT NULL, fingerprint TEXT NOT NULL, outcome TEXT NOT NULL, payload_json TEXT NOT NULL)"
        )
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_evolution_memory_failure ON harness_evolution_memory(failure_key)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_evolution_memory_fingerprint ON harness_evolution_memory(fingerprint)")

    def append(
        self,
        entry: EvolutionMemoryEntry,
        *,
        authority: EvolutionMemoryWriteAuthority | None = None,
    ) -> None:
        expected = _SQLITE_AUTHORITIES.get(self)
        if expected is None or authority is not expected:
            raise PermissionError("trusted evolution memory write authority required")
        payload = json.dumps(
            asdict(entry),
            ensure_ascii=False,
            sort_keys=True,
            default=lambda value: value.value if isinstance(value, Enum) else str(value),
        )
        try:
            self._conn.execute("BEGIN IMMEDIATE")
            self._conn.execute(
                "INSERT INTO harness_evolution_memory VALUES (?, ?, ?, ?, ?, ?)",
                (entry.memory_id, entry.created_at, entry.failure_key, entry.fingerprint, entry.outcome.value, payload),
            )
            self._conn.execute("COMMIT")
        except sqlite3.IntegrityError as exc:
            self._conn.execute("ROLLBACK")
            raise ValueError(f"memory entry already exists: {entry.memory_id}") from exc
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

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


def _bind_trusted_memory(memory: EvolutionMemory) -> None:
    """Bind production memory once without returning or exposing an authority.

    Rebinding a memory already owned by the production trust boundary is
    idempotent, which allows a later loop instance to reuse persisted/read
    history. A memory explicitly pre-bound by an external caller is rejected.
    """
    if memory in _TRUSTED_BOUND_MEMORIES:
        return
    if _MEMORY_AUTHORITIES.get(memory) is not None:
        raise ValueError("evolution_memory must not be pre-bound to an external write authority")
    _MEMORY_AUTHORITIES[memory] = EvolutionMemoryWriteAuthority()
    _TRUSTED_BOUND_MEMORIES.add(memory)


def _append_trusted_entry(memory: EvolutionMemory, entry: EvolutionMemoryEntry) -> None:
    """Internal production append path.

    This function intentionally carries no authority argument and captures no
    capability. It is an implementation primitive for the trusted orchestrator;
    importing/calling module-private helpers from arbitrary code running inside
    the trusted interpreter is outside the threat model.
    """
    if memory not in _TRUSTED_BOUND_MEMORIES:
        raise PermissionError("evolution memory is not bound to trusted orchestration")
    if _MEMORY_AUTHORITIES.get(memory) is None:
        raise PermissionError("trusted evolution memory binding is unavailable")
    _append_verified(memory, entry)
