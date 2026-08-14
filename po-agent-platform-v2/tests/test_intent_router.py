"""Tests for Intent Router."""

import pytest

from po_agent.orchestration.router import DeterministicIntentRouter, IntentClassification


@pytest.fixture
def router():
    """Create intent router."""
    return DeterministicIntentRouter()


class TestDeterministicIntentRouter:
    """Tests for DeterministicIntentRouter."""

    def test_task_search_intent(self, router):
        """Test task search intent classification."""
        result = router.classify("покажи задачи по фразе")

        assert result.intent == "task_search"
        assert result.confidence >= 0.5

    def test_sprint_health_intent(self, router):
        """Test sprint health intent classification."""
        result = router.classify("здоровье спринта")

        assert result.intent == "sprint_health"
        assert result.confidence >= 0.5

    def test_velocity_intent(self, router):
        """Test velocity intent classification."""
        result = router.classify("скорость команды")

        assert result.intent == "velocity"
        assert result.confidence >= 0.5

    def test_release_health_intent(self, router):
        """Test release health intent classification."""
        result = router.classify("здоровье релиза")

        assert result.intent == "release_health"
        assert result.confidence >= 0.5

    def test_help_intent(self, router):
        """Test help intent classification."""
        result = router.classify("что умеешь")

        assert result.intent == "help"
        assert result.confidence >= 0.5

    def test_entity_extraction_sprint(self, router):
        """Test sprint entity extraction."""
        result = router.classify("здоровье спринта DMS-SPRNT-1")

        assert result.intent == "sprint_health"
        sprint_entities = [e for e in result.entities if e.type == "sprint"]
        assert len(sprint_entities) >= 1

    def test_entity_extraction_release(self, router):
        """Test release entity extraction."""
        result = router.classify("статус релиза 2024-Q3")

        assert result.intent == "release_health"

    def test_router_version(self, router):
        """Test router version."""
        result = router.classify("помощь")

        assert result.router_version == "1.0.0"


class TestIntentRouterEdgeCases:
    """Tests for edge cases."""

    def test_empty_query(self, router):
        """Test empty query handling."""
        result = router.classify("")

        assert result.intent == "help"

    def test_unknown_query(self, router):
        """Test unknown query handling."""
        result = router.classify("неизвестный запрос")

        assert result.intent == "help"

    def test_case_insensitive(self, router):
        """Test case insensitive matching."""
        result1 = router.classify("ПОКАЖИ ЗАДАЧИ")
        result2 = router.classify("покажи задачи")

        assert result1.intent == result2.intent
