import pytest

from po_agent.harness.evolution_memory import (
    EvolutionMemory,
    EvolutionMemoryEntry,
    EvolutionMemoryOutcome,
    EvolutionMemoryPolicy,
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


def test_fingerprint_is_deterministic_and_order_independent_for_targets():
    a = evolution_fingerprint(failure_key="f", target_files=("b.py", "a.py"), proposal_material="x")
    b = evolution_fingerprint(failure_key="f", target_files=("a.py", "b.py"), proposal_material="x")
    assert a == b


def test_known_bad_fingerprint_is_bounded():
    memory = EvolutionMemory(EvolutionMemoryPolicy(max_same_fingerprint_failures=2))
    first = _entry(EvolutionMemoryOutcome.REJECTED)
    second = EvolutionMemoryEntry.create(
        failure_key=first.failure_key,
        candidate_id="c2",
        proposal_id="p2",
        target_files=("a.py",),
        proposal_material="same change",
        outcome=EvolutionMemoryOutcome.BLOCKED,
    )
    memory.append(first)
    assert memory.should_attempt(first.fingerprint) == (True, ())
    memory.append(second)
    allowed, reasons = memory.should_attempt(first.fingerprint)
    assert allowed is False
    assert "known_bad_fingerprint_failure_limit" in reasons


def test_rolled_back_fingerprint_is_blocked():
    memory = EvolutionMemory()
    entry = _entry(EvolutionMemoryOutcome.ROLLED_BACK)
    memory.append(entry)
    allowed, reasons = memory.should_attempt(entry.fingerprint)
    assert allowed is False
    assert reasons == ("fingerprint_was_rolled_back",)


def test_promoted_fingerprint_is_remembered_but_not_implicitly_approved():
    memory = EvolutionMemory()
    entry = _entry(EvolutionMemoryOutcome.PROMOTED)
    memory.append(entry)
    assert entry.fingerprint in memory.promoted_fingerprints()
    assert memory.should_attempt(entry.fingerprint) == (True, ())


def test_memory_is_append_only_and_rejects_duplicate_id():
    memory = EvolutionMemory()
    entry = _entry(EvolutionMemoryOutcome.ERROR)
    memory.append(entry)
    with pytest.raises(ValueError):
        memory.append(entry)


def test_sqlite_memory_round_trip():
    store = SQLiteEvolutionMemoryStore()
    entry = _entry(EvolutionMemoryOutcome.REJECTED)
    store.append(entry)
    rows = store.by_fingerprint(entry.fingerprint)
    assert rows == (entry,)
    with pytest.raises(ValueError):
        store.append(entry)
