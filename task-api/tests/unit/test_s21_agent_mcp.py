"""Unit tests for S21 Agent MCP."""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from s21_agent.models.task import Task, Comment, Attachment
from s21_agent.services.quality_scorer import calculate_quality_score, category, CriterionScore
from s21_agent.services.ranker import rank_tasks


class TestQualityScorer:
    """Tests for quality scoring service."""
    
    def test_calculate_quality_score(self) -> None:
        """Test weighted quality score calculation."""
        criteria = [
            CriterionScore("goal", 20, 1.0, "ok"),
            CriterionScore("criteria", 30, 0.5, "partial"),
            CriterionScore("dependencies", 20, 0.0, "missing"),
        ]
        
        score = calculate_quality_score(criteria)
        expected = (20 * 1.0 + 30 * 0.5 + 20 * 0.0) / 70
        assert abs(score - expected) < 0.001
    
    def test_calculate_quality_score_zero_weight(self) -> None:
        """Test score with zero total weight."""
        criteria = [
            CriterionScore("a", 0, 1.0, "ok"),
            CriterionScore("b", 0, 0.5, "ok"),
        ]
        
        score = calculate_quality_score(criteria)
        assert score == 0.0
    
    def test_category(self) -> None:
        """Test quality category classification."""
        assert category(95) == "готова к разработке"
        assert category(90) == "готова к разработке"
        assert category(85) == "в целом готова, нужны небольшие уточнения"
        assert category(75) == "в целом готова, нужны небольшие уточнения"
        assert category(70) == "требуется доработка постановки"
        assert category(50) == "требуется доработка постановки"
        assert category(49) == "не готова к реализации"
        assert category(0) == "не готова к реализации"


class TestRanker:
    """Tests for task ranking service."""
    
    def test_rank_tasks_by_query(self) -> None:
        """Test ranking tasks by relevance to query."""
        now = datetime.utcnow()
        tasks = [
            Task(
                id="1",
                source_id="TASK-1",
                title="Баг в модуле аутентификации",
                description="При входе система выдает ошибку 500",
                status="todo",
                created_at=now,
                updated_at=now,
            ),
            Task(
                id="2",
                source_id="TASK-2",
                title="Добавить фильтр по статусу",
                description="Добавить фильтр в UI",
                status="in_progress",
                created_at=now,
                updated_at=now,
            ),
            Task(
                id="3",
                source_id="TASK-3",
                title="Аутентификация: оптимизация JWT",
                description="Ускорить проверку токенов",
                status="done",
                created_at=now,
                updated_at=now,
            ),
        ]
        
        ranked = rank_tasks(tasks, "аутентификация")
        
        # First and third tasks should be ranked higher (contain "аутентификация")
        assert ranked[0].source_id in ("TASK-1", "TASK-3")
        assert ranked[1].source_id in ("TASK-1", "TASK-3")
        assert ranked[2].source_id == "TASK-2"
    
    def test_rank_tasks_no_query(self) -> None:
        """Test ranking without query returns original order."""
        now = datetime.utcnow()
        tasks = [
            Task(
                id="1",
                source_id="A",
                title="Task A",
                description="",
                status="todo",
                created_at=now,
                updated_at=now,
            ),
            Task(
                id="2",
                source_id="B",
                title="Task B",
                description="",
                status="todo",
                created_at=now,
                updated_at=now,
            ),
        ]
        
        ranked = rank_tasks(tasks, "")
        assert [t.source_id for t in ranked] == ["A", "B"]


class TestModels:
    """Tests for task models."""
    
    def test_task_creation(self) -> None:
        """Test task model creation."""
        now = datetime.utcnow()
        task = Task(
            id="test-id",
            source_id="SWTR-123",
            title="Test Task",
            description="Test Description",
            status="todo",
            created_at=now,
            updated_at=now,
        )
        
        assert task.title == "Test Task"
        assert task.status == "todo"
    
    def test_comment_creation(self) -> None:
        """Test comment model creation."""
        comment = Comment(
            id="comment-1",
            author="John Doe",
            body="This is a comment",
        )
        
        assert comment.author == "John Doe"
        assert "comment" in comment.body.lower()
    
    def test_attachment_creation(self) -> None:
        """Test attachment model creation."""
        attachment = Attachment(
            id="attach-1",
            name="document.pdf",
            content_type="application/pdf",
            size_bytes=102400,
        )
        
        assert attachment.name == "document.pdf"
        assert attachment.size_bytes == 102400
