"""Integration tests for PO Agent Platform v2 with real services.

Tests real:
- SWTR adapter (via FastAPI on port 8003)
- Real LLM (QwenCoder via SBT Hub AI)
"""

import asyncio

import pytest

from po_agent.adapters.legacy_bridge import LegacyAS21Bridge
from po_agent.analysis.task_quality import TaskQualityAnalysis
from po_agent.llm.client import LLMMessage
from po_agent.llm.real import RealLLMClient
from po_agent.summary.task_summary import TaskSummaryService
from po_agent.search.intelligence import TaskIntelligenceSearch


@pytest.fixture
def real_llm_client():
    """Create real LLM client (QwenCoder)."""
    return RealLLMClient()


class TestSWTRIntegration:
    """Integration tests with real SWTR via FastAPI."""

    async def _test_swtr_fetch_tasks(self):
        """Test fetching tasks from real SWTR."""
        bridge = LegacyAS21Bridge()

        tasks = await bridge.search_tasks("limit=50")

        assert tasks is not None
        assert len(tasks) > 0

        # Verify we got some tasks with expected fields
        first_task = tasks[0]
        assert first_task.key is not None
        assert first_task.title is not None
        assert first_task.status is not None

    def test_swtr_fetch_tasks(self):
        """Test fetching tasks from real SWTR (async wrapper)."""
        asyncio.run(self._test_swtr_fetch_tasks())


class TestRealLLMIntegration:
    """Integration tests with real LLM (QwenCoder)."""

    async def _test_llm_complete_real(self, real_llm_client):
        """Test real LLM completion with QwenCoder."""
        messages = [
            LLMMessage(
                role="system",
                content="You are a helpful assistant. Always respond in English.",
            ),
            LLMMessage(
                role="user",
                content="What is the capital of France?",
            ),
        ]

        response = await real_llm_client.complete(messages)

        assert response.choices is not None
        assert len(response.choices) > 0
        assert "Paris" in response.choices[0].message.content

    def test_llm_complete_real(self, real_llm_client):
        """Test real LLM completion with QwenCoder (async wrapper)."""
        asyncio.run(self._test_llm_complete_real(real_llm_client))

    async def _test_llm_usage_tracking(self, real_llm_client):
        """Test that real LLM tracks token usage."""
        messages = [
            LLMMessage(
                role="user",
                content="Count to 3 in English.",
            ),
        ]

        response = await real_llm_client.complete(messages)

        assert response.usage is not None
        assert response.usage.prompt_tokens >= 0
        assert response.usage.completion_tokens >= 0

    def test_llm_usage_tracking(self, real_llm_client):
        """Test that real LLM tracks token usage (async wrapper)."""
        asyncio.run(self._test_llm_usage_tracking(real_llm_client))

    async def _test_llm_stream_real(self, real_llm_client):
        """Test real LLM streaming."""
        messages = [
            LLMMessage(
                role="user",
                content="Say hello in one word.",
            ),
        ]

        chunks = []
        async for chunk in real_llm_client.stream(messages):
            chunks.append(chunk)

        assert len(chunks) > 0

    def test_llm_stream_real(self, real_llm_client):
        """Test real LLM streaming (async wrapper)."""
        asyncio.run(self._test_llm_stream_real(real_llm_client))


class TestFullPipelineIntegration:
    """Integration tests for full pipelines."""

    async def _test_task_summary_with_real_llm(self, real_llm_client):
        """Test TaskSummaryService with real LLM."""
        bridge = LegacyAS21Bridge()
        tasks = await bridge.search_tasks("limit=50")

        # Get first task
        task = tasks[0]

        # Create service with real LLM
        service = TaskSummaryService(llm_client=real_llm_client)

        # Test LLM summary
        summary = await service.generate_llm_summary(task)

        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_task_summary_with_real_llm(self, real_llm_client):
        """Test TaskSummaryService with real LLM (async wrapper)."""
        asyncio.run(self._test_task_summary_with_real_llm(real_llm_client))

    async def _test_task_quality_with_real_llm(self, real_llm_client):
        """Test TaskQualityAnalysis with real LLM."""
        bridge = LegacyAS21Bridge()
        tasks = await bridge.search_tasks("limit=50")

        # Get first task
        task = tasks[0]

        # Create service with real LLM
        service = TaskQualityAnalysis(llm_client=real_llm_client)

        # Test LLM analysis
        result = await service.analyze_with_llm(task)

        assert "deterministic" in result
        assert "llm" in result
        assert result["llm"] is not None
        assert "analysis" in result["llm"]

    def test_task_quality_with_real_llm(self, real_llm_client):
        """Test TaskQualityAnalysis with real LLM (async wrapper)."""
        asyncio.run(self._test_task_quality_with_real_llm(real_llm_client))

    async def _test_task_search_integration(self, real_llm_client):
        """Test TaskIntelligenceSearch with real data."""
        bridge = LegacyAS21Bridge()
        tasks = await bridge.search_tasks("limit=50")

        search = TaskIntelligenceSearch()

        # Search by phrase
        results = search.search_by_phrase(tasks, "authentication", max_results=10)

        # Search by assignee
        if tasks:
            assignee = tasks[0].assignee
            if assignee:
                results = search.search_by_assignee(tasks, assignee)

        assert results is not None

    def test_task_search_integration(self, real_llm_client):
        """Test TaskIntelligenceSearch with real data (async wrapper)."""
        asyncio.run(self._test_task_search_integration(real_llm_client))


class TestTaskQualityReportIntegration:
    """Integration tests for quality reports."""

    async def _test_full_quality_report(self, real_llm_client):
        """Test full quality report generation with real LLM."""
        bridge = LegacyAS21Bridge()
        tasks = await bridge.search_tasks("limit=50")

        task = tasks[0]

        service = TaskQualityAnalysis(llm_client=real_llm_client)

        # Generate report with LLM
        report = await service.generate_quality_report_with_llm(task)

        assert report["task_key"] == task.key
        assert "score" in report
        assert report["score"] >= 0 and report["score"] <= 100
        assert "llm_analysis" in report
        assert "summary" in report

    def test_full_quality_report(self, real_llm_client):
        """Test full quality report generation with real LLM (async wrapper)."""
        asyncio.run(self._test_full_quality_report(real_llm_client))
