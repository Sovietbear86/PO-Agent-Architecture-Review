from po_agent.harness.learned_semantics import LearnedSemanticsStore


def test_explicit_non_conflicting_definition_auto_promotes(tmp_path):
    store = LearnedSemanticsStore(tmp_path / "learned.json")
    rule = store.learn_explicit_definition(
        term="open_tasks",
        meaning="all unresolved tasks",
        source_trace_id="trace-1",
    )
    assert rule.status == "active"
    assert rule.version == 1
    assert store.context()["open_tasks"] == "all unresolved tasks"


def test_repeated_same_definition_is_idempotent(tmp_path):
    store = LearnedSemanticsStore(tmp_path / "learned.json")
    first = store.learn_explicit_definition(term="open_tasks", meaning="In Progress", source_trace_id="t1")
    second = store.learn_explicit_definition(term="open_tasks", meaning="In Progress", source_trace_id="t2")
    assert first.rule_id == second.rule_id
    assert second.version == 1


def test_conflicting_definition_stays_pending_and_does_not_change_active_behavior(tmp_path):
    store = LearnedSemanticsStore(tmp_path / "learned.json")
    active = store.learn_explicit_definition(term="open_tasks", meaning="In Progress", source_trace_id="t1")
    conflict = store.learn_explicit_definition(term="open_tasks", meaning="Open", source_trace_id="t2")
    assert active.status == "active"
    assert conflict.status == "pending"
    assert conflict.version == 2
    assert store.context()["open_tasks"] == "In Progress"
