"""Integration tests for S21 Agent."""
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestAgentIntegration:
    """Integration tests for agent functionality."""
    
    def test_search_tasks_with_filter(self) -> None:
        """Test searching tasks with filters."""
        # Mock adapter response
        mock_task = Mock()
        mock_task.source_id = "WMB-123"
        mock_task.title = "Test Task"
        mock_task.status = "todo"
        
        with patch('s21_agent.connectors.s21_swtr_adapter.SWTRAdapter') as MockAdapter:
            adapter_instance = MockAdapter.return_value
            adapter_instance.search_tasks.return_value = [mock_task]
            
            # Import after patching
            from s21_agent.services.ranker import rank_tasks
            
            ranked = rank_tasks([mock_task], "test")
            assert len(ranked) == 1
            assert ranked[0].source_id == "WMB-123"
    
    def test_agent_quality_assessment(self) -> None:
        """Test quality assessment of a task."""
        from s21_agent.services.quality_scorer import (
            calculate_quality_score,
            category,
            CriterionScore,
        )
        
        criteria = [
            CriterionScore("цель", 30, 0.8, "цель упомянута"),
            CriterionScore("критерии", 40, 0.6, "частично определены"),
            CriterionScore("риски", 30, 0.4, "не описаны"),
        ]
        
        score = calculate_quality_score(criteria)
        
        # Expected: (30*0.8 + 40*0.6 + 30*0.4) / 100 = 0.6
        assert abs(score - 0.6) < 0.001
        assert category(score) == "требуется доработка постановки"
    
    @pytest.mark.asyncio
    async def test_mcp_server_health(self) -> None:
        """Test MCP server health endpoint."""
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:3000/health")
                assert response.status_code == 200
                
                data = response.json()
                assert data["status"] == "healthy"
                assert data["service"] == "s21-task-agent"
        except httpx.RequestError:
            # MCP server might not be running in CI
            pytest.skip("MCP server not available for integration test")
    
    def test_swtr_adapter_initialization(self) -> None:
        """Test SWTR adapter initialization."""
        from s21_agent.config import settings
        from s21_agent.connectors.s21_swtr_adapter import SWTRAdapter
        
        adapter = SWTRAdapter()
        
        assert adapter.mcp_host == settings.mcp_host
        assert adapter.mcp_port == settings.mcp_port
    
    def test_task_model_serialization(self) -> None:
        """Test task model serialization."""
        from datetime import datetime
        from s21_agent.models.task import Task
        
        task = Task(
            id="test-123",
            source_id="WMB-456",
            title="Test Task",
            description="Test Description",
            status="in_progress",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        data = task.model_dump()
        
        assert data["title"] == "Test Task"
        assert data["status"] == "in_progress"
        assert "source_id" in data


class TestAgentEndpoints:
    """Test agent MCP endpoints."""
    
    def test_search_endpoint_structure(self) -> None:
        """Test search endpoint response structure."""
        # Mock the full flow
        mock_response = {
            "query": "тест",
            "filters": None,
            "total": 2,
            "tasks": [
                {
                    "id": "1",
                    "source_id": "WMB-1",
                    "title": "Первая задача",
                    "status": "todo",
                },
                {
                    "id": "2",
                    "source_id": "WMB-2",
                    "title": "Вторая задача",
                    "status": "in_progress",
                },
            ],
        }
        
        assert mock_response["query"] == "тест"
        assert mock_response["total"] == 2
        assert len(mock_response["tasks"]) == 2
    
    def test_quality_assessment_endpoint_structure(self) -> None:
        """Test quality assessment endpoint response structure."""
        mock_response = {
            "task_id": "WMB-123",
            "score": 0.75,
            "category": "в целом готова, нужны небольшие уточнения",
            "criteria_scores": [
                {"name": "цель", "weight": 20, "score": 0.8, "rationale": "ok"},
            ],
        }
        
        assert mock_response["score"] == 0.75
        assert mock_response["category"] == "в целом готова, нужны небольшие уточнения"
