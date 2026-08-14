"""Tests for TaskQualityAnalysis."""

import asyncio
from datetime import datetime

import pytest

from po_agent.domain.models import (
    StatusCategory,
    Task,
    TaskPriority,
    TaskStatus,
)
from po_agent.llm.mock import MockLLMClient
from po_agent.analysis.task_quality import TaskQualityAnalysis


@pytest.fixture
def sample_task():
    """Create sample task for testing."""
    now = datetime.now()

    return Task(
        key="WMB-101",
        id="task-001",
        title="Implement user authentication",
        description="Add OAuth2 support for user login. This is a critical security feature.",
        status=TaskStatus.RESOLVED,
        status_category=StatusCategory.COMPLETED_PENDING,
        created_at=now,
        updated_at=now,
        assignee="Ivanov.I.I",
        priority=TaskPriority.HIGH,
        labels=["security", "authentication"],
        source="test",
    )


@pytest.fixture
def poor_quality_task():
    """Create poor quality task for testing."""
    now = datetime.now()

    return Task(
        key="WMB-102",
        id="task-002",
        title="Fix bug",
        description="Bug",
        status=TaskStatus.OPEN,
        status_category=StatusCategory.BACKLOG,
        created_at=now,
        updated_at=now,
        source="test",
    )


@pytest.fixture
def quality_service():
    """Create quality analysis service."""
    return TaskQualityAnalysis()


@pytest.fixture
def quality_service_with_llm():
    """Create quality analysis service with mock LLM."""
    return TaskQualityAnalysis(llm_client=MockLLMClient())


class TestAnalyzeDeterministic:
    """Tests for analyze_deterministic."""

    def test_good_quality_task(self, quality_service, sample_task):
        """Test analysis of good quality task."""
        result = quality_service.analyze_deterministic(sample_task)

        assert result["score"] >= 80
        assert result["quality_level"] == "good"
        assert len(result["issues"]) < 5

    def test_poor_quality_task(self, quality_service, poor_quality_task):
        """Test analysis of poor quality task."""
        result = quality_service.analyze_deterministic(poor_quality_task)

        assert result["score"] < 60
        assert result["quality_level"] in ["fair", "poor", "very poor"]
        assert len(result["issues"]) > 0

    def test_metrics_in_result(self, quality_service, sample_task):
        """Test that metrics are included in result."""
        result = quality_service.analyze_deterministic(sample_task)

        assert "metrics" in result
        assert "title_length" in result["metrics"]
        assert "description_length" in result["metrics"]
        assert result["metrics"]["has_title"] is True
        assert result["metrics"]["has_description"] is True

    def test_recommendations_in_result(self, quality_service, poor_quality_task):
        """Test that recommendations are included in result."""
        result = quality_service.analyze_deterministic(poor_quality_task)

        assert "recommendations" in result
        assert len(result["recommendations"]) >= 0


class TestAnalyzeWithLLM:
    """Tests for analyze_with_llm."""

    async def _test_llm_analysis(self, quality_service_with_llm, sample_task):
        """Test LLM-based analysis."""
        result = await quality_service_with_llm.analyze_with_llm(sample_task)

        assert "deterministic" in result
        assert "llm" in result
        assert result["llm"] is not None

    def test_llm_analysis(self, quality_service_with_llm, sample_task):
        """Test LLM-based analysis (async wrapper)."""
        asyncio.run(self._test_llm_analysis(quality_service_with_llm, sample_task))

    async def _test_llm_analysis_with_deterministic_result(
        self,
        quality_service_with_llm,
        sample_task,
    ):
        """Test LLM analysis with pre-computed deterministic result."""
        deterministic = quality_service_with_llm.analyze_deterministic(sample_task)
        result = await quality_service_with_llm.analyze_with_llm(sample_task, deterministic)

        assert "deterministic" in result
        assert "llm" in result

    def test_llm_analysis_with_deterministic_result(
        self,
        quality_service_with_llm,
        sample_task,
    ):
        """Test LLM analysis with pre-computed deterministic result (async wrapper)."""
        asyncio.run(self._test_llm_analysis_with_deterministic_result(quality_service_with_llm, sample_task))

    async def _test_llm_analysis_without_llm(self, quality_service, sample_task):
        """Test LLM analysis falls back when no LLM."""
        result = await quality_service.analyze_with_llm(sample_task)

        assert "deterministic" in result
        assert result["llm"] is None

    def test_llm_analysis_without_llm(self, quality_service, sample_task):
        """Test LLM analysis falls back when no LLM (async wrapper)."""
        asyncio.run(self._test_llm_analysis_without_llm(quality_service, sample_task))


class TestCalculateQualityScore:
    """Tests for calculate_quality_score."""

    def test_score_range(self, quality_service, sample_task):
        """Test that score is in valid range."""
        score = quality_service.calculate_quality_score(sample_task)

        assert 0 <= score <= 100

    def test_score_consistency(self, quality_service, sample_task):
        """Test that score is consistent."""
        score1 = quality_service.calculate_quality_score(sample_task)
        score2 = quality_service.calculate_quality_score(sample_task)

        assert score1 == score2


class TestGetQualityLevel:
    """Tests for get_quality_level."""

    def test_good_level(self, quality_service):
        """Test getting good quality level."""
        assert quality_service.get_quality_level(85) == "good"
        assert quality_service.get_quality_level(90) == "good"

    def test_fair_level(self, quality_service):
        """Test getting fair quality level."""
        assert quality_service.get_quality_level(65) == "fair"
        assert quality_service.get_quality_level(75) == "fair"

    def test_poor_level(self, quality_service):
        """Test getting poor quality level."""
        assert quality_service.get_quality_level(45) == "poor"
        assert quality_service.get_quality_level(55) == "poor"

    def test_very_poor_level(self, quality_service):
        """Test getting very poor quality level."""
        assert quality_service.get_quality_level(10) == "very poor"
        assert quality_service.get_quality_level(0) == "very poor"


class TestGenerateQualityReport:
    """Tests for generate_quality_report."""

    def test_report_structure(self, quality_service, sample_task):
        """Test report structure."""
        report = quality_service.generate_quality_report(sample_task)

        assert "task_key" in report
        assert "task_title" in report
        assert "analysis_timestamp" in report
        assert "deterministic_analysis" in report
        assert "quality_level" in report
        assert "score" in report
        assert "summary" in report

    def test_report_summary(self, quality_service, poor_quality_task):
        """Test report summary generation."""
        report = quality_service.generate_quality_report(poor_quality_task)

        assert "issue" in report["summary"].lower() or "issues" in report["summary"].lower()


class TestGenerateQualityReportWithLLM:
    """Tests for generate_quality_report_with_llm."""

    async def _test_report_with_llm(self, quality_service_with_llm, sample_task):
        """Test report generation with LLM."""
        report = await quality_service_with_llm.generate_quality_report_with_llm(sample_task)

        assert "llm_analysis" in report
        assert "deterministic_analysis" in report

    def test_report_with_llm(self, quality_service_with_llm, sample_task):
        """Test report generation with LLM (async wrapper)."""
        asyncio.run(self._test_report_with_llm(quality_service_with_llm, sample_task))

    async def _test_report_with_llm_without_llm(self, quality_service, sample_task):
        """Test report generation with LLM when no LLM provided."""
        report = await quality_service.generate_quality_report_with_llm(sample_task)

        assert "llm_analysis" in report
        assert report["llm_analysis"] is None

    def test_report_with_llm_without_llm(self, quality_service, sample_task):
        """Test report generation with LLM when no LLM provided (async wrapper)."""
        asyncio.run(self._test_report_with_llm_without_llm(quality_service, sample_task))


class TestTaskQualityAnalysisLifecycle:
    """Tests for TaskQualityAnalysis lifecycle."""

    def test_service_initialization(self):
        """Test service initialization."""
        service = TaskQualityAnalysis()
        assert service is not None

    def test_service_initialization_with_llm(self):
        """Test service initialization with LLM."""
        service = TaskQualityAnalysis(llm_client=MockLLMClient())
        assert service is not None
