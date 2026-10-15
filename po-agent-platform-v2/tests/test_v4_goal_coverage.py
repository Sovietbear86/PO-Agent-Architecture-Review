"""A229M2.1 offline replay: semantic goal anchors and source-evidence coverage.

All synthetic rows are taken from the A229M1 shape matrix; these tests do not
use a fake factual source to claim live AS21 parity.
"""
from copy import deepcopy

from po_agent.api.v1.goal_coverage import (
    check_goal_coverage,
    detect_goals,
    guard_completed_goal_coverage,
)


def result(cap, args, data=None):
    return {"capability_id": cap, "arguments": args, "data": data or {"source": "REAL_AS21"}}


def response(*rows):
    return {
        "status": "COMPLETED",
        "answer": "The model may have incorrectly said there is no parent.",
        "data": {"results": list(rows), "_agent_core_v4": {}},
        "evidence": [{"id": "unsafe-claim"}],
        "warnings": [],
    }


M1 = "Покажи задачи Калачанова в WMB и задачи Семавина в DMS"
M2 = "Покажи задачу DMS-267 и её иерархию"
M3 = "Покажи задачи Калачанова в WMB и иерархию DMS-267"
M4 = "Покажи задачу DMS-267, её иерархию и задачи Калачанова в WMB"
C5 = "Покажи задачу DMS-267 и связанные с ней задачи"


def test_goal_counts_from_a229m1_offline_matrix():
    expected = {
        M1: ["person_tasks", "person_tasks"],
        M2: ["task_lookup", "task_hierarchy"],
        M3: ["person_tasks", "task_hierarchy"],
        M4: ["task_lookup", "task_hierarchy", "person_tasks"],
        C5: ["task_lookup", "task_relations"],
    }
    for query, kinds in expected.items():
        assert sorted(g.kind for g in detect_goals(query)) == sorted(kinds)


def test_composed_filter_queries_never_split():
    queries = (
        "Открытые задачи Семавина с типом дефект в DMS за последние 2 дня",
        "Задачи Калачанова в WMB с вложениями",
        "Покажи открытые дефекты Семавина в последнем спринте OLP",
        "Задачи в работе и с вложениями у Калачанова в WMB",
        "Сравни незавершённые задачи в DMS и OLP",
        "Сравни DMS и OLP",
    )
    assert all(len(detect_goals(query)) <= 1 for query in queries)


def test_one_terminal_cannot_prove_other_persons_collection():
    goals = detect_goals(M1)
    output = response(result("task.search_assignee", {"reference": "Калачанов", "space": "WMB"}))
    coverage = check_goal_coverage(output, goals)
    assert coverage.proven == ("g1",)
    assert coverage.unproven == ("g2",)
    guarded = guard_completed_goal_coverage(output, M1)
    assert guarded["status"] == "NEEDS_CLARIFICATION"
    assert guarded["answer"] is None
    assert guarded["evidence"] == []
    assert "results" not in guarded["data"]


def test_lookup_only_cannot_prove_hierarchy_or_links_and_removes_false_prose():
    for query in (M2, C5):
        output = response(result("task.lookup", {"task_key": "DMS-267"}))
        guarded = guard_completed_goal_coverage(output, query)
        assert guarded["status"] == "NEEDS_CLARIFICATION"
        assert guarded["answer"] is None
        assert "unsafe-claim" not in str(guarded)
        assert len(guarded["data"]["_agent_core_v4"]["goal_coverage"]["unproven"]) == 1


def test_two_matching_terminals_complete_with_exact_binding():
    output = response(
        result("task.lookup", {"task_key": "DMS-267"}),
        result("task.hierarchy", {"task_key": "DMS-267"}),
    )
    assert check_goal_coverage(output, detect_goals(M2)).unproven == ()
    guarded = guard_completed_goal_coverage(output, M2)
    assert guarded["status"] == "COMPLETED"


def test_wrong_task_key_does_not_prove_hierarchy():
    output = response(
        result("task.lookup", {"task_key": "DMS-267"}),
        result("task.hierarchy", {"task_key": "DMS-999"}),
    )
    coverage = check_goal_coverage(output, detect_goals(M2))
    assert {g.kind for g in coverage.goals if g.goal_id in coverage.unproven} == {"task_hierarchy"}


def test_infrastructure_and_existing_clarification_status_are_preserved():
    for status in ("FAILED", "NEEDS_CLARIFICATION", "PARTIAL"):
        original = response(result("task.lookup", {"task_key": "DMS-267"}))
        original["status"] = status
        assert guard_completed_goal_coverage(original, M2)["status"] == status


def test_no_legacy_guard_mutation_when_single_goal_or_unknown():
    for query in (
        "Покажи задачу DMS-267",
        "Задачи Калачанова в WMB",
        "Сравни DMS и OLP",
    ):
        original = response(result("task.lookup", {"task_key": "DMS-267"}))
        prior = deepcopy(original)
        assert guard_completed_goal_coverage(original, query) == prior


def test_missing_source_evidence_must_not_count_as_proof():
    output = response(
        result("task.lookup", {"task_key": "DMS-267"}, {"source_complete": False}),
        result("task.hierarchy", {"task_key": "DMS-267"}, {"source_unavailable": True}),
    )
    assert len(check_goal_coverage(output, detect_goals(M2)).unproven) == 2


def test_two_persons_with_inflected_queries_stay_completed():
    output = response(
        result("task.search_assignee", {"reference": "Калачанов", "space": "WMB"}),
        result("task.search_assignee", {"reference": "Семавин", "space": "DMS"}),
    )
    coverage = check_goal_coverage(output, detect_goals(M1))
    assert coverage.unproven == ()
    assert guard_completed_goal_coverage(output, M1)["status"] == "COMPLETED"


def test_resolver_proven_logins_bind_to_original_person_goal():
    output = response(
        result("member.resolve", {"reference": "Калачанов"}, {"member_login": "Kalachanov.V.V", "source": "REAL_AS21"}),
        result("task.search", {"reference": "Kalachanov.V.V", "space": "WMB"}),
        result("member.resolve", {"reference": "Семавин"}, {"member_login": "Semavin.M.M", "source": "REAL_AS21"}),
        result("task.search", {"reference": "Semavin.M.M", "space": "DMS"}),
    )
    coverage = check_goal_coverage(output, detect_goals(M1))
    assert coverage.unproven == ()
    assert guard_completed_goal_coverage(output, M1)["status"] == "COMPLETED"


def test_unproven_login_and_similar_names_never_prove_goal():
    output = response(
        result("task.search", {"reference": "Kalachanov.V.V", "space": "WMB"}),
        result("task.search_assignee", {"reference": "Семёнов", "space": "DMS"}),
    )
    assert len(check_goal_coverage(output, detect_goals(M1)).unproven) == 2


def test_preservation_carries_only_source_backed_proven_goal():
    from po_agent.api.v1 import _remember_clarification, _pending_clarifications
    original = response(
        result("member.resolve", {"reference": "Калачанов"},
               {"source": "REAL_AS21", "member_login": "Kalachanov.V.V"}),
        result("task.search", {"reference": "Kalachanov.V.V", "space": "WMB"},
               {"source": "REAL_AS21", "count": 1, "tasks": [{"key": "WMB-6"}]}),
    )
    original["data"]["_agent_core_v4"]["loaded_skills"] = ["task.search"]
    try:
        guarded = guard_completed_goal_coverage(original, M1, preserve_state=True)
        state = guarded["data"]["_agent_core_v4"]
        assert guarded["status"] == "NEEDS_CLARIFICATION"
        assert len(state["continuation_observations"]) == 2
        assert {o["capability_id"] for o in state["continuation_observations"]} == {
            "member.resolve", "task.search"
        }
        assert all(o["data"]["source"] == "REAL_AS21" for o in state["continuation_observations"])
        assert "results" not in guarded["data"]
        remembered = _remember_clarification(guarded, "goal-test", M1)
        pending = _pending_clarifications["goal-test"]
        assert len(pending.resume_observations) == 2
        assert not pending.required_completion_skills
        assert "continuation_observations" not in remembered["data"]["_agent_core_v4"]
    finally:
        _pending_clarifications.pop("goal-test", None)


def test_preservation_disabled_and_unproven_source_fail_closed():
    disabled = response(result("task.lookup", {"task_key": "DMS-267"}))
    guarded = guard_completed_goal_coverage(disabled, M2)
    assert "continuation_observations" not in guarded["data"]["_agent_core_v4"]

    unproven = response(result("task.lookup", {"task_key": "DMS-267"},
                                {"source": "LOCAL", "task_key": "DMS-267"}))
    guarded = guard_completed_goal_coverage(unproven, M2, preserve_state=True)
    assert "continuation_observations" not in guarded["data"]["_agent_core_v4"]
    assert "v4_goal_continuation_state_unavailable" in guarded["warnings"]


def test_preservation_fails_closed_for_large_or_partial_source_data():
    huge = response(result("task.lookup", {"task_key": "DMS-267"},
                           {"source": "REAL_AS21", "task_key": "DMS-267",
                            "related_keys": [f"DMS-{i}" for i in range(2000)]}))
    guarded = guard_completed_goal_coverage(huge, M2, preserve_state=True)
    assert "continuation_observations" not in guarded["data"]["_agent_core_v4"]

    partial = response(result("task.lookup", {"task_key": "DMS-267"},
                              {"source": "REAL_AS21", "source_complete": False}))
    guarded = guard_completed_goal_coverage(partial, M2, preserve_state=True)
    assert "continuation_observations" not in guarded["data"]["_agent_core_v4"]


def test_realistic_dms_lookup_raw_source_card_is_stripped_and_lookup_retained():
    # Mirrors the live A229M2.2A failing payload shape: nested source_data
    # carries SWTR attribute cards. Live capture/oracle remains QA's job.
    original = response(result("task.lookup", {"task_key": "DMS-267"}, {
        "source": "REAL_AS21", "task_key": "DMS-267",
        "task": {
            "key": "DMS-267", "title": "Задача DMS-267", "status": "В работе",
            "source_data": {
                "swtr_attributes": [{"code": f"attr_{i}", "value": "x" * 240}
                                    for i in range(36)],
                "owner_private_card": "not for continuation",
            },
        },
    }))
    guarded = guard_completed_goal_coverage(original, M2, preserve_state=True)
    assert guarded["status"] == "NEEDS_CLARIFICATION"
    carried = guarded["data"]["_agent_core_v4"]["continuation_observations"]
    assert len(carried) == 1
    assert carried[0]["data"]["source"] == "REAL_AS21"
    assert carried[0]["data"]["task_key"] == "DMS-267"
    assert carried[0]["data"]["task"]["key"] == "DMS-267"
    assert carried[0]["data"]["task"]["status"] == "В работе"
    assert "source_data" not in str(carried)
    assert "swtr_attributes" not in str(carried)
    assert len(__import__("json").dumps(carried, ensure_ascii=False).encode()) < 8192
    assert "results" not in guarded["data"]


def test_unknown_raw_cards_not_carried_even_when_under_8kb():
    original = response(result("task.lookup", {"task_key": "DMS-267"}, {
        "source": "REAL_AS21", "task_key": "DMS-267",
        "source_data": {"swtr_attributes": [{"secret": "NEVER_CARRY"}]},
        "task": {"key": "DMS-267", "description": "NEVER_CARRY",
                 "source_data": {"raw": "NEVER_CARRY"}},
    }))
    guarded = guard_completed_goal_coverage(original, M2, preserve_state=True)
    carried = guarded["data"]["_agent_core_v4"]["continuation_observations"]
    assert "NEVER_CARRY" not in str(carried)
    assert carried[0]["data"]["task"]["key"] == "DMS-267"


def test_two_turn_credit_is_private_and_does_not_repeat_lookup():
    # T1: source-proven lookup, hierarchy not executed.
    first = response(result("task.lookup", {"task_key": "DMS-267"}, {
        "source": "REAL_AS21", "task_key": "DMS-267",
        "task": {"key": "DMS-267", "status": "Resolved",
                 "source_data": {"swtr_attributes": [{"value": "PRIVATE"}]}},
    }))
    guarded = guard_completed_goal_coverage(first, M2, preserve_state=True)
    assert guarded["status"] == "NEEDS_CLARIFICATION"
    prior = tuple(guarded["data"]["_agent_core_v4"]["continuation_observations"])
    assert len(prior) == 1
    assert "PRIVATE" not in str(prior)

    # T2: Core gets the prior observation for planning, but executes ONLY
    # the missing task.hierarchy. Guard must credit the prior lookup.
    second = response(result("task.hierarchy", {"task_key": "DMS-267"}, {
        "source": "REAL_AS21", "task_key": "DMS-267",
        "parent_chain": [{"key": "DMS-253", "relation": "parent"}],
    }))
    verified = guard_completed_goal_coverage(
        second, M2, preserve_state=True, trusted_prior_observations=prior,
    )
    assert verified["status"] == "COMPLETED"
    assert len(verified["data"]["results"]) == 1
    assert verified["data"]["results"][0]["capability_id"] == "task.hierarchy"
    assert "continuation_observations" not in verified["data"]["_agent_core_v4"]


def test_prior_observation_with_unknown_source_cannot_gain_credit():
    untrusted = ({
        "step": 1, "capability_id": "task.lookup",
        "arguments": {"task_key": "DMS-267"},
        "answer": "invented",
        "data": {"source": "LOCAL", "task_key": "DMS-267"},
    },)
    second = response(result("task.hierarchy", {"task_key": "DMS-267"}, {
        "source": "REAL_AS21", "task_key": "DMS-267",
    }))
    verified = guard_completed_goal_coverage(
        second, M2, preserve_state=True, trusted_prior_observations=untrusted,
    )
    assert verified["status"] == "NEEDS_CLARIFICATION"
    assert "task_lookup" in verified["question"]


def test_second_turn_still_fails_closed_if_hierarchy_not_executed():
    original = response(result("task.lookup", {"task_key": "DMS-267"}, {
        "source": "REAL_AS21", "task_key": "DMS-267",
    }))
    first = guard_completed_goal_coverage(original, M2, preserve_state=True)
    prior = tuple(first["data"]["_agent_core_v4"]["continuation_observations"])
    second = response()
    verified = guard_completed_goal_coverage(
        second, M2, preserve_state=True, trusted_prior_observations=prior,
    )
    assert verified["status"] == "NEEDS_CLARIFICATION"
    assert "task_hierarchy" in verified["question"]
    assert verified["data"]["_agent_core_v4"]["continuation_observations"]
