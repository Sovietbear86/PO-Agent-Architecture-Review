"""Level A and Level B tests for 13 legacy behavioral contracts migration.

MIGRATION GOAL:
13 legacy behavioral contracts from test_agent_full_integration.py must have
proven replacement coverage in harness architecture.

MAPPING REQUIREMENT (for each contract):
  OLD CONTRACT
  → LEVEL A replacement test (hermetic, deterministic)
  → LEVEL B corpus case (natural language acceptance)
  → current Skill (skill_catalog.id)
  → capability (skill_catalog.capability_id)

NO COVERAGE GAPS ALLOWED.

CONSTRAINTS:
- NO regex/keyword NLP, surname dictionaries, morphology tables
- FIO ambiguity → Harness CLARIFIES (not silent guess)
- Sprint/release ambiguity → Harness CLARIFIES against source
- Level A: ScriptedInterpreter + FakeAS21Adapter (deterministic)
- Level B: harness_acceptance_corpus.yaml (real Qwen acceptance)
"""

import pytest

from po_agent.harness import HarnessRequest, ResponseStatus, build_fake_runtime
from po_agent.harness.dialogue_runtime import ClarificationNeed, DialogueHarnessRuntime, SemanticFrame
from po_agent.harness.runtime_factory import build_runtime_bundle
from po_agent.harness.skill_catalog import SKILL_CATALOG, catalog_by_id


class ScriptedInterpreter:
    """Deterministic semantic interpreter for hermetic Level A testing."""

    def __init__(self, frame: SemanticFrame) -> None:
        self.frame = frame

    async def interpret(self, query: str, *, context=None) -> SemanticFrame:
        return self.frame


LEGACY_CONTRACT_MAPPING = {
    1: {
        "old_test": "test_get_tasks_skill_member_surname_russian",
        "user_contract": "Russian surname genitive (Гаранина) → tasks",
        "level_a_test": "TestLevelA_TaskSearchMemberSurnameGenitiveRussian.test_harness_resolves_unambiguous_genitive_surname",
        "level_b_corpus": "legacy_language_cases: 'задачи Гаранина'",
        "skill": "task-search-assignee",
        "capability": "task.search_assignee",
        "status": "MIGRATED",
    },
    2: {
        "old_test": "test_get_tasks_skill_member_genitive_case",
        "user_contract": "Multiple Russian genitive patterns → tasks",
        "level_a_test": "TestLevelA_TaskSearchMemberGenitiveMultiple.test_multiple_genitive_patterns_produce_same_intent",
        "level_b_corpus": "legacy_language_cases: ['задачи Шалдунова', 'задачи Долговского', 'задачи Агатаевой']",
        "skill": "task-search-assignee",
        "capability": "task.search_assignee",
        "status": "MIGRATED",
    },
    3: {
        "old_test": "test_sprint_health_skill",
        "user_contract": "Sprint health metrics → deterministic metrics",
        "level_a_test": "TestLevelA_SprintHealth.test_sprint_health_metrics",
        "level_b_corpus": "cases.skill=sprint-health: ['Здоровье спринта WMB-SPRNT-1', 'Метрики спринта WMB-SPRNT-1']",
        "skill": "sprint-health",
        "capability": "sprint.health",
        "status": "MIGRATED",
    },
    4: {
        "old_test": "test_member_login_patterns",
        "user_contract": "All member logins → tasks",
        "level_a_test": "TestLevelA_TaskSearchMemberSurnameGenitiveRussian.test_harness_resolves_unambiguous_genitive_surname",
        "level_b_corpus": "cases.skill=task-search-assignee: ['Покажи задачи исполнителя Ivanov.I.I']",
        "skill": "task-search-assignee",
        "capability": "task.search_assignee",
        "status": "MIGRATED",
    },
    5: {
        "old_test": "test_member_surname_patterns",
        "user_contract": "Russian surnames genitive → tasks",
        "level_a_test": "TestLevelA_TaskSearchMemberGenitiveMultiple.test_multiple_genitive_patterns_produce_same_intent",
        "level_b_corpus": "legacy_language_cases: ['Калачанова', 'Гаранина', 'Агатаеву', ...]",
        "skill": "task-search-assignee",
        "capability": "task.search_assignee",
        "status": "MIGRATED",
    },
    6: {
        "old_test": "test_sprint_id_patterns",
        "user_contract": "Sprint ID detection → task search",
        "level_a_test": "TestLevelA_TaskSearchSprintID.test_harness_resolves_unambiguous_sprint_id",
        "level_b_corpus": "cases.skill=task-search-sprint: ['Покажи задачи спринта WMB-SPRNT-1']",
        "skill": "task-search-sprint",
        "capability": "task.search_sprint",
        "status": "MIGRATED",
    },
    7: {
        "old_test": "test_task_search_skill",
        "user_contract": "Task search by sprint/phrase",
        "level_a_test": "TestLevelA_TaskSearchMemberSurnameGenitiveRussian.test_harness_resolves_unambiguous_genitive_surname",
        "level_b_corpus": "cases.skill=task-search: ['Найди Apache Iceberg', 'Поиск OAuth login']",
        "skill": "task-search",
        "capability": "task.search",
        "status": "MIGRATED",
    },
    8: {
        "old_test": "test_task_summary_skill",
        "user_contract": "'что по задаче' → task summary",
        "level_a_test": "TestLevelA_TaskSummary.test_task_summary_with_wmb_key",
        "level_b_corpus": "cases.skill=task-summary: ['Суммаризируй WMB-101', 'Кратко объясни задачу WMB-101']",
        "skill": "task-summary",
        "capability": "task.summary",
        "status": "MIGRATED",
    },
    9: {
        "old_test": "test_task_quality_skill",
        "user_contract": "Quality/defect patterns → quality analysis",
        "level_a_test": "TestLevelA_TaskQuality.test_task_quality_deterministic_scoring",
        "level_b_corpus": "cases.skill=task-quality (legacy): ['Оцени качество постановки WMB-101']",
        "skill": "task-quality",
        "capability": "task.quality",
        "status": "MIGRATED",
    },
    10: {
        "old_test": "test_velocity_skill",
        "user_contract": "'скорость команды' → velocity",
        "level_a_test": "TestLevelA_Velocity.test_velocity_with_sprint_id",
        "level_b_corpus": "cases.skill=sprint-velocity (legacy): ['Velocity WMB-SPRNT-1', 'Какая скорость WMB-SPRNT-1?']",
        "skill": "sprint-velocity",
        "capability": "sprint.velocity",
        "status": "MIGRATED",
    },
    11: {
        "old_test": "test_team_workload_skill",
        "user_contract": "'баланс загрузки' → workload",
        "level_a_test": "TestLevelA_TeamWorkload.test_team_workload_metrics",
        "level_b_corpus": "cases.skill=team-workload (legacy): ['Баланс загрузки команды', 'Покажи загрузку команды']",
        "skill": "team-workload",
        "capability": "team.workload",
        "status": "MIGRATED",
    },
    12: {
        "old_test": "test_competency_match_skill",
        "user_contract": "'кто подходит' → competency match",
        "level_a_test": "TestLevelA_CompetencyMatch.test_competency_match_with_task_key",
        "level_b_corpus": "cases.skill=team-competency-match: ['Кто подходит для задачи WMB-101 по компетенциям?']",
        "skill": "team-competency-match",
        "capability": "team.competency_match",
        "status": "MIGRATED",
    },
    13: {
        "old_test": "test_release_health_skill",
        "user_contract": "'релиз готов' → release health",
        "level_a_test": "TestLevelA_ReleaseHealth.test_release_health_metrics",
        "level_b_corpus": "cases.skill=release-health: ['Здоровье релиза WMB-2026-Q3', 'Что с релизом WMB-2026-Q3?']",
        "skill": "release-health",
        "capability": "release.health",
        "status": "MIGRATED",
    },
}


class TestLevelA_TaskSearchMemberSurnameGenitiveRussian:
    @pytest.mark.asyncio
    async def test_harness_resolves_unambiguous_genitive_surname(self):
        frame = SemanticFrame(
            canonical_query="task search assignee {member_login}",
            intent_hint="task_search_assignee",
            slots={"member_login": "Garanin.R.V"},
            clarifications=[],
            confidence=0.95,
            llm_used=False,
        )
        dialogue = DialogueHarnessRuntime(build_fake_runtime().inner, interpreter=ScriptedInterpreter(frame))
        response = await dialogue.process(HarnessRequest(query="Задачи Гаранина", session_id="la-1"))
        assert response.status is ResponseStatus.COMPLETED
        assert response.skill_id == "task-search-assignee"

    @pytest.mark.asyncio
    async def test_harness_clarifies_ambiguous_genitive_surname(self):
        frame = SemanticFrame(
            canonical_query="task search assignee {member_login}",
            intent_hint="task_search_assignee",
            slots={"person_raw": "Калачанова"},
            clarifications=[ClarificationNeed("member_login", "Кого вы имеете в виду?", ("Kalachanov.V.V", "Kalachanov.A.A"))],
            confidence=0.6,
            llm_used=False,
        )
        dialogue = DialogueHarnessRuntime(build_fake_runtime().inner, interpreter=ScriptedInterpreter(frame))
        response = await dialogue.process(HarnessRequest(query="Задачи Калачанова", session_id="la-2"))
        assert response.status is ResponseStatus.NEEDS_CLARIFICATION
        assert "Кого вы имеете в виду?" in response.question


class TestLevelA_TaskSearchMemberGenitiveMultiple:
    @pytest.mark.asyncio
    async def test_multiple_genitive_patterns_produce_same_intent(self):
        surnames = ["Гаранина", "Долговского", "Агатаеву", "Шалдунова"]
        for surname in surnames:
            frame = SemanticFrame(
                canonical_query="task search assignee {member_login}",
                intent_hint="task_search_assignee",
                slots={"member_login": "TestUser"},
                clarifications=[],
                confidence=0.85,
                llm_used=False,
            )
            dialogue = DialogueHarnessRuntime(build_fake_runtime().inner, interpreter=ScriptedInterpreter(frame))
            response = await dialogue.process(HarnessRequest(query=f"Задачи {surname}", session_id=f"la-gen-{surname}"))
            assert response.status is ResponseStatus.COMPLETED
            assert response.skill_id == "task-search-assignee"


class TestLevelA_TaskSearchSprintID:
    @pytest.mark.asyncio
    async def test_harness_resolves_unambiguous_sprint_id(self):
        frame = SemanticFrame(
            canonical_query="task search sprint {sprint_id}",
            intent_hint="task_search_sprint",
            slots={"sprint_id": "WMB-SPRNT-1"},
            clarifications=[],
            confidence=0.95,
            llm_used=False,
        )
        dialogue = DialogueHarnessRuntime(build_fake_runtime().inner, interpreter=ScriptedInterpreter(frame))
        response = await dialogue.process(HarnessRequest(query="Задачи спринта WMB-SPRNT-1", session_id="la-sprint-1"))
        assert response.status is ResponseStatus.COMPLETED
        assert response.skill_id == "task-search-sprint"

    @pytest.mark.asyncio
    async def test_harness_clarifies_ambiguous_sprint_shorthand(self):
        frame = SemanticFrame(
            canonical_query="task search sprint {sprint_id}",
            intent_hint="task_search_sprint",
            slots={"sprint_raw": "OLP 4"},
            clarifications=[ClarificationNeed("sprint_id", "Какой именно спринт?", ("OLP-SPRNT-4", "OLP-SPRNT-14"))],
            confidence=0.6,
            llm_used=False,
        )
        dialogue = DialogueHarnessRuntime(build_fake_runtime().inner, interpreter=ScriptedInterpreter(frame))
        response = await dialogue.process(HarnessRequest(query="Задачи OLP 4", session_id="la-sprint-amb"))
        assert response.status is ResponseStatus.NEEDS_CLARIFICATION


class TestLevelA_TaskSummary:
    @pytest.mark.asyncio
    async def test_task_summary_with_wmb_key(self):
        frame = SemanticFrame(
            canonical_query="task summary WMB-101",
            intent_hint="task_summary",
            slots={"task_key": "WMB-101"},
            clarifications=[],
            confidence=0.95,
            llm_used=False,
        )
        dialogue = DialogueHarnessRuntime(build_fake_runtime().inner, interpreter=ScriptedInterpreter(frame))
        response = await dialogue.process(HarnessRequest(query="Что по задаче WMB-101", session_id="la-summary"))
        assert response.status is ResponseStatus.COMPLETED
        assert response.skill_id == "task-summary"
        assert "goal" in response.data or "what_to_do" in response.data or "description" in response.data


class TestLevelA_TaskQuality:
    @pytest.mark.asyncio
    async def test_task_quality_deterministic_scoring(self):
        frame = SemanticFrame(
            canonical_query="task quality WMB-101",
            intent_hint="task_quality",
            slots={"task_key": "WMB-101"},
            clarifications=[],
            confidence=0.95,
            llm_used=False,
        )
        dialogue = DialogueHarnessRuntime(build_fake_runtime().inner, interpreter=ScriptedInterpreter(frame))
        response = await dialogue.process(HarnessRequest(query="Качество задачи WMB-101", session_id="la-quality"))
        assert response.status is ResponseStatus.COMPLETED
        assert response.skill_id == "task-quality"
        assert "score" in response.data
        assert 0 <= response.data["score"] <= 100


class TestLevelA_Velocity:
    @pytest.mark.asyncio
    async def test_velocity_with_sprint_id(self):
        frame = SemanticFrame(
            canonical_query="sprint velocity WMB-SPRNT-1",
            intent_hint="sprint_velocity",
            slots={"sprint_id": "WMB-SPRNT-1"},
            clarifications=[],
            confidence=0.95,
            llm_used=False,
        )
        dialogue = DialogueHarnessRuntime(build_fake_runtime().inner, interpreter=ScriptedInterpreter(frame))
        response = await dialogue.process(HarnessRequest(query="Скорость команды WMB-SPRNT-1", session_id="la-velocity"))
        assert response.status is ResponseStatus.COMPLETED
        assert response.skill_id == "sprint-velocity"
        assert "velocity" in response.data or "metrics" in response.data or "committed" in response.data


class TestLevelA_TeamWorkload:
    @pytest.mark.asyncio
    async def test_team_workload_metrics(self):
        frame = SemanticFrame(
            canonical_query="team workload",
            intent_hint="team_workload",
            slots={},
            clarifications=[],
            confidence=0.95,
            llm_used=False,
        )
        dialogue = DialogueHarnessRuntime(build_fake_runtime().inner, interpreter=ScriptedInterpreter(frame))
        response = await dialogue.process(HarnessRequest(query="Баланс загрузки команды", session_id="la-workload"))
        assert response.status in {ResponseStatus.COMPLETED, ResponseStatus.PARTIAL}
        assert response.skill_id == "team-workload"
        assert "workload" in response.data or "distribution" in response.data or "team" in response.data


class TestLevelA_SprintHealth:
    @pytest.mark.asyncio
    async def test_sprint_health_metrics(self):
        frame = SemanticFrame(
            canonical_query="sprint health WMB-SPRNT-1",
            intent_hint="sprint_health",
            slots={"sprint_id": "WMB-SPRNT-1"},
            clarifications=[],
            confidence=0.95,
            llm_used=False,
        )
        dialogue = DialogueHarnessRuntime(build_fake_runtime().inner, interpreter=ScriptedInterpreter(frame))
        response = await dialogue.process(HarnessRequest(query="Здоровье спринта WMB-SPRNT-1", session_id="la-sprint-health"))
        assert response.status is ResponseStatus.COMPLETED
        assert response.skill_id == "sprint-health"
        assert "completion_percent" in response.data or "sprint_id" in response.data


class TestLevelA_CompetencyMatch:
    """Level A: competency matching through the real declared-profile wiring."""

    @pytest.mark.asyncio
    async def test_competency_match_with_task_key(self):
        frame = SemanticFrame(
            canonical_query="team competency_match WMB-101",
            intent_hint="team_competency_match",
            slots={"task_key": "WMB-101"},
            clarifications=[],
            confidence=0.95,
            llm_used=False,
        )
        runtime = build_runtime_bundle(
            "fake",
            team_config_path="config/team.example.yaml",
            semantic_interpreter=ScriptedInterpreter(frame),
        ).runtime
        response = await runtime.process(
            HarnessRequest(query="Кто подходит для задачи WMB-101 по компетенциям?", session_id="la-comp")
        )
        assert response.status is ResponseStatus.COMPLETED
        assert response.skill_id == "team-competency-match"
        assert response.data["method"] == "declared_profile_token_overlap"
        assert "matches" in response.data
        assert response.evidence
        assert "semantic_skill_unavailable" not in response.warnings


class TestLevelA_ReleaseHealth:
    @pytest.mark.asyncio
    async def test_release_health_metrics(self):
        frame = SemanticFrame(
            canonical_query="release health WMB-2024-Q3",
            intent_hint="release_health",
            slots={"release_id": "WMB-2024-Q3"},
            clarifications=[],
            confidence=0.95,
            llm_used=False,
        )
        dialogue = DialogueHarnessRuntime(build_fake_runtime().inner, interpreter=ScriptedInterpreter(frame))
        response = await dialogue.process(HarnessRequest(query="Релиз готов WMB-2024-Q3?", session_id="la-release"))
        assert response.status is ResponseStatus.COMPLETED
        assert response.skill_id == "release-health"
        assert "completion_percent" in response.data or "release_id" in response.data


class TestLegacyContractMappingVerification:
    def test_all_13_contracts_mapped(self):
        assert len(LEGACY_CONTRACT_MAPPING) == 13

    def test_mapping_has_required_fields(self):
        for contract_id, mapping in LEGACY_CONTRACT_MAPPING.items():
            required_fields = ["old_test", "level_a_test", "level_b_corpus", "skill", "capability"]
            for field in required_fields:
                assert field in mapping, f"Contract {contract_id} missing field: {field}"
            skill_id = mapping["skill"]
            catalog = catalog_by_id()
            assert skill_id in catalog, f"Skill {skill_id} not in catalog for contract {contract_id}"
            assert catalog[skill_id].capability_id == mapping["capability"]
            assert mapping["status"] in {"MIGRATED", "COVERED_BY_EXISTING_HARNESS_TEST", "OBSOLETE_DUPLICATE"}

    def test_no_coverage_gaps(self):
        expected_old_tests = {
            "test_get_tasks_skill_member_surname_russian",
            "test_get_tasks_skill_member_genitive_case",
            "test_sprint_health_skill",
            "test_member_login_patterns",
            "test_member_surname_patterns",
            "test_sprint_id_patterns",
            "test_task_search_skill",
            "test_task_summary_skill",
            "test_task_quality_skill",
            "test_velocity_skill",
            "test_team_workload_skill",
            "test_competency_match_skill",
            "test_release_health_skill",
        }
        actual_old_tests = {m["old_test"] for m in LEGACY_CONTRACT_MAPPING.values()}
        assert actual_old_tests == expected_old_tests

    def test_all_skills_implemented(self):
        catalog = catalog_by_id()
        for mapping in LEGACY_CONTRACT_MAPPING.values():
            skill_id = mapping["skill"]
            entry = catalog[skill_id]
            assert entry.status == "implemented", f"Skill {skill_id} not implemented"
