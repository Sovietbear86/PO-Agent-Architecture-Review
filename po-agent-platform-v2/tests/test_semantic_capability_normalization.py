from po_agent.harness.dialogue_runtime import DialogueHarnessRuntime, SemanticFrame
from po_agent.harness.skill_catalog import (
    SKILL_CATALOG,
    canonical_semantic_intents,
    catalog_by_id,
    intent_to_skill_id,
)


def test_all_canonical_semantic_intents_round_trip_to_implemented_skills():
    expected = {entry.id for entry in SKILL_CATALOG if entry.status == "implemented"}
    resolved = {intent_to_skill_id(intent) for intent in canonical_semantic_intents()}
    assert None not in resolved
    assert resolved == expected


def test_real_e2e_task_lookup_semantic_variants_normalize_to_task_lookup():
    for intent in ("task_details", "task_by_id", "task_lookup", "task-lookup"):
        assert intent_to_skill_id(intent) == "task-lookup"


def test_real_e2e_team_assignee_match_semantic_variant_normalizes_to_assignee_recommendation():
    """New test: task_assignee_match maps to team-assignee-recommendation"""
    assert intent_to_skill_id("task_assignee_match") == "team-assignee-recommendation"
    assert catalog_by_id()["team-assignee-recommendation"].capability_id == "team.assignee_recommendation"


def test_real_e2e_sprint_semantic_variant_normalizes_to_sprint_health():
    for intent in ("sprint_details", "sprint_health", "sprint-health", "sprint_readiness"):
        assert intent_to_skill_id(intent) == "sprint-health"


def test_real_e2e_team_matching_semantics_normalize_to_assignee_recommendation():
    for intent in ("team_matching", "assignee_recommendation", "team_assignee_recommendation", "team-assignee-recommendation"):
        skill_id = intent_to_skill_id(intent)
        assert skill_id == "team-assignee-recommendation"
        assert catalog_by_id()[skill_id].capability_id == "team.assignee_recommendation"


def test_unreviewed_semantic_variants_do_not_become_hidden_phrase_dictionary():
    for intent in (None, "", "task_detailz", "task_info", "sprint_info", "best_assignee", "team_match_magic", "do_whatever_seems_close"):
        assert intent_to_skill_id(intent) is None


def test_entity_slot_normalization_is_separate_from_intent_normalization():
    frame = SemanticFrame(
        canonical_query="Кто лучше подходит для задачи OLP-3134?",
        intent_hint="team_matching",
        slots={"task_id": "OLP-3134"},
    )
    args = DialogueHarnessRuntime._build_capability_args(frame)
    assert intent_to_skill_id(frame.intent_hint) == "team-assignee-recommendation"
    assert args["task_key"] == "OLP-3134"


def test_task_lookup_slot_alias_is_normalized_without_parsing_natural_language():
    frame = SemanticFrame(
        canonical_query="Покажи задачу OLP-3134",
        intent_hint="task_details",
        slots={"issue_key": "OLP-3134"},
    )
    args = DialogueHarnessRuntime._build_capability_args(frame)
    assert args["task_key"] == "OLP-3134"


def test_explicit_task_key_is_preserved_for_lookup_and_team_matching():
    for intent in ("task_details", "team_matching", "task_assignee_match"):
        frame = SemanticFrame(
            canonical_query="OLP-3134",
            intent_hint=intent,
            slots={"task_key": "OLP-3134"},
        )
        args = DialogueHarnessRuntime._build_capability_args(frame)
        assert args["task_key"] == "OLP-3134"


def test_team_assignee_recommendation_requires_task_key():
    runtime = object.__new__(DialogueHarnessRuntime)
    ok, message = runtime._validate_required_args("team.assignee_recommendation", {})
    assert ok is False
    assert message == "Missing required slot: task_key"
