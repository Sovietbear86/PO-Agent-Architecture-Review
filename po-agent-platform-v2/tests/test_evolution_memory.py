import copy
import pickle

import pytest

from po_agent.harness.evolution_memory import (
    EvolutionMemory,
    EvolutionMemoryEntry,
    EvolutionMemoryOutcome,
    EvolutionMemoryPolicy,
    EvolutionMemoryWriteAuthority,
    SQLiteEvolutionMemoryStore,
    evolution_fingerprint,
)


def _entry(outcome: EvolutionMemoryOutcome) -> EvolutionMemoryEntry:
    return EvolutionMemoryEntry.create(
        failure_key="intent_mismatch:x->y",
        candidate_id="c1",
        proposal_id="p1",
        target_files=("a.py",),
        proposal_material="same change",
        outcome=outcome,
    )


def _memory(policy: EvolutionMemoryPolicy | None = None):
    authority = EvolutionMemoryWriteAuthority()
    return EvolutionMemory(policy, write_authority=authority), authority


def test_fingerprint_is_deterministic_and_order_independent_for_targets():
    a = evolution_fingerprint(failure_key="f", target_files=("b.py", "a.py"), proposal_material="x")
    b = evolution_fingerprint(failure_key="f", target_files=("a.py", "b.py"), proposal_material="x")
    assert a == b


def test_known_bad_fingerprint_is_bounded_and_blocked_counts_as_failure():
    memory, authority = _memory(EvolutionMemoryPolicy(max_same_fingerprint_failures=2))
    first = _entry(EvolutionMemoryOutcome.REJECTED)
    second = EvolutionMemoryEntry.create(
        failure_key=first.failure_key,
        candidate_id="c2",
        proposal_id="p2",
        target_files=("a.py",),
        proposal_material="same change",
        outcome=EvolutionMemoryOutcome.BLOCKED,
    )
    memory.append(first, authority=authority)
    assert memory.should_attempt(first.fingerprint) == (True, ())
    memory.append(second, authority=authority)
    allowed, reasons = memory.should_attempt(first.fingerprint)
    assert allowed is False
    assert "known_bad_fingerprint_failure_limit" in reasons


def test_rolled_back_fingerprint_is_blocked():
    memory, authority = _memory()
    entry = _entry(EvolutionMemoryOutcome.ROLLED_BACK)
    memory.append(entry, authority=authority)
    allowed, reasons = memory.should_attempt(entry.fingerprint)
    assert allowed is False
    assert reasons == ("fingerprint_was_rolled_back",)


def test_promoted_fingerprint_is_remembered_but_not_implicitly_approved():
    memory, authority = _memory()
    entry = _entry(EvolutionMemoryOutcome.PROMOTED)
    memory.append(entry, authority=authority)
    assert entry.fingerprint in memory.promoted_fingerprints()
    assert memory.should_attempt(entry.fingerprint) == (True, ())


def test_memory_rejects_untrusted_writes():
    authority = EvolutionMemoryWriteAuthority()
    wrong_authority = EvolutionMemoryWriteAuthority()
    memory = EvolutionMemory(write_authority=authority)
    entry = _entry(EvolutionMemoryOutcome.ERROR)
    with pytest.raises(PermissionError):
        memory.append(entry)
    with pytest.raises(PermissionError):
        memory.append(entry, authority=wrong_authority)
    memory.append(entry, authority=authority)


def test_write_authority_is_not_copyable_or_serializable():
    authority = EvolutionMemoryWriteAuthority()
    with pytest.raises(TypeError):
        pickle.dumps(authority)
    with pytest.raises(TypeError):
        copy.copy(authority)
    with pytest.raises(TypeError):
        copy.deepcopy(authority)


def test_memory_is_append_only_and_rejects_duplicate_id():
    memory, authority = _memory()
    entry = _entry(EvolutionMemoryOutcome.ERROR)
    memory.append(entry, authority=authority)
    with pytest.raises(ValueError):
        memory.append(entry, authority=authority)


def test_sqlite_memory_round_trip_and_untrusted_write_rejected():
    authority = EvolutionMemoryWriteAuthority()
    store = SQLiteEvolutionMemoryStore(write_authority=authority)
    entry = _entry(EvolutionMemoryOutcome.REJECTED)
    with pytest.raises(PermissionError):
        store.append(entry)
    store.append(entry, authority=authority)
    rows = store.by_fingerprint(entry.fingerprint)
    assert rows == (entry,)
    with pytest.raises(ValueError):
        store.append(entry, authority=authority)
