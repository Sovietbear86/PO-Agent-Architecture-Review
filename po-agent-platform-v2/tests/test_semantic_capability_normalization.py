from po_agent.harness.dialogue_runtime import DialogueHarnessRuntime, SemanticFrame
from po_agent.harness.skill_catalog import (
    SKILL_CATALOG,
    canonical_semantic_intents,
    catalog_by_id,
    intent_to_skill_id,
)


def test_all_canonical_semantic_intents_round_trip_to_implemented_skills():
    expected = {
        entry.id
        for entry in SKILL_CATALOG
        if entry.status == "implemented"
    }
    resolved = {
        intent_to_skill_id(intent)
        for intent in canonical_semantic_intents()
    }
    assert None not in resolved
    assert resolved == expected


def test_real_e2e_task_lookup_semantic_variants_normalize_to_task_lookup():
    for intent in (
        "task_details",
        "task_detail",
        "task_by_id",
        "show_task",
        "task_info",
        "task_lookup",
        "task-lookup",
    ):
        assert intent_to_skill_id(intent) == "task-lookup"


def test_real_e2e_sprint_semantic_variants_normalize_to_sprint_health():
    for intent in (
        "sprint_details",
        "sprint_detail",
        "sprint_status",
        "sprint_info",
        "sprint_health",
        "sprint-health",
    ):
        assert intent_to_skill_id(intent) == "sprint-health"


def test_real_e2e_team_matching_variants_normalize_to_assignee_recommendation():
    for intent in (
        "team_matching",
        "team_match",
        "best_assignee",
        "assignee_recommendation",
        "recommend_assignee",
        "team_assignee_recommendation",
        "team-assignee-recommendation",
    ):
        skill_id = intent_to_skill_id(intent)
        assert skill_id == "team-assignee-recommendation"
        assert catalog_by_id()[skill_id].capability_id == "team.assignee_recommendation"


def test_unknown_or_near_miss_semantics_remain_fail_closed():
    for intent in (
        None,
        "",
        "task_detailz",
        "sprint_detailz",
        "team_match_magic",
        "do_whatever_seems_close",
    ):
        assert intent_to_skill_id(intent) is None


def test_entity_slot_normalization_is_separate_from_intent_normalization():
    frame = SemanticFrame(
        canonical_query="Кто лучше подходит для задачи OLP-3134?",
        intent_hint="team_matching",
        slots={"task_id": "OLP-3134"},
    )
    runtime = object.__new__(DialogueHarnessRuntime)
    args = runtime._build_capability_args(frame, skill_id="team-assignee-recommendation")
    assert intent_to_skill_id(frame.intent_hint) == "team-assignee-recommendation"
    assert args["task_key"] == "OLP-3134"


def test_task_lookup_slot_alias_is_normalized_without_parsing_natural_language():
    frame = SemanticFrame(
        canonical_query="Покажи задачу OLP-3134",
        intent_hint="task_details",
        slots={"issue_key": "OLP-3134"},
    )
    runtime = object.__new__(DialogueHarnessRuntime)
    args = runtime._build_capability_args(frame, skill_id="task-lookup")
    assert args["task_key"] == "OLP-3134"
