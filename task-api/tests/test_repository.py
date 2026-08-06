"""Tests for task repository."""
import pytest
from uuid import uuid4
from app.models.task import Task, Status
from app.repositories.task_repository import TaskRepository


@pytest.fixture
def repository():
    """Create a fresh repository for each test."""
    return TaskRepository()


@pytest.fixture
def sample_task():
    """Create a sample task."""
    return Task(
        title="Test Task",
        description="Test Description",
        assignee="John Doe",
        status=Status.TODO,
    )


class TestTaskRepository:
    """Tests for TaskRepository."""
    
    def test_save_task(self, repository, sample_task):
        """Test saving a task."""
        saved_task = repository.save(sample_task)
        assert saved_task.id is not None
        assert saved_task.title == "Test Task"
    
    def test_find_by_id(self, repository, sample_task):
        """Test finding a task by ID."""
        saved_task = repository.save(sample_task)
        found_task = repository.find_by_id(saved_task.id)
        assert found_task is not None
        assert found_task.title == "Test Task"
    
    def test_find_by_id_not_found(self, repository):
        """Test finding a non-existent task."""
        found_task = repository.find_by_id(uuid4())
        assert found_task is None
    
    def test_find_all(self, repository):
        """Test finding all tasks."""
        task1 = repository.save(Task(title="Task 1"))
        task2 = repository.save(Task(title="Task 2"))
        task3 = repository.save(Task(title="Task 3"))
        
        all_tasks = repository.find_all()
        assert len(all_tasks) == 3
        assert task1 in all_tasks
        assert task2 in all_tasks
        assert task3 in all_tasks
    
    def test_find_all_with_status_filter(self, repository):
        """Test finding tasks with status filter."""
        task1 = repository.save(Task(title="Task 1", status=Status.TODO))
        task2 = repository.save(Task(title="Task 2", status=Status.IN_PROGRESS))
        task3 = repository.save(Task(title="Task 3", status=Status.TODO))
        
        todo_tasks = repository.find_all(status=Status.TODO)
        assert len(todo_tasks) == 2
        assert task1 in todo_tasks
        assert task3 in todo_tasks
        assert task2 not in todo_tasks
    
    def test_find_all_with_assignee_filter(self, repository):
        """Test finding tasks with assignee filter."""
        task1 = repository.save(Task(title="Task 1", assignee="John"))
        task2 = repository.save(Task(title="Task 2", assignee="Jane"))
        task3 = repository.save(Task(title="Task 3", assignee="John"))
        
        john_tasks = repository.find_all(assignee="John")
        assert len(john_tasks) == 2
        assert task1 in john_tasks
        assert task3 in john_tasks
        assert task2 not in john_tasks
    
    def test_find_all_with_pagination(self, repository):
        """Test finding tasks with pagination."""
        for i in range(5):
            repository.save(Task(title=f"Task {i}"))
        
        tasks_page1 = repository.find_all(limit=2, offset=0)
        tasks_page2 = repository.find_all(limit=2, offset=2)
        
        assert len(tasks_page1) == 2
        assert len(tasks_page2) == 2
    
    def test_update_task(self, repository):
        """Test updating a task."""
        task = repository.save(Task(title="Original Title"))
        task.update(title="Updated Title")
        updated_task = repository.update(task.id, task)
        
        assert updated_task is not None
        assert updated_task.title == "Updated Title"
    
    def test_update_task_not_found(self, repository):
        """Test updating a non-existent task."""
        task = Task(title="Test")
        result = repository.update(uuid4(), task)
        assert result is None
    
    def test_delete_task(self, repository):
        """Test deleting a task."""
        task = repository.save(Task(title="Test"))
        result = repository.delete(task.id)
        
        assert result is True
        assert repository.find_by_id(task.id) is None
    
    def test_delete_task_not_found(self, repository):
        """Test deleting a non-existent task."""
        result = repository.delete(uuid4())
        assert result is False
    
    def test_clear_tasks(self, repository):
        """Test clearing all tasks."""
        repository.save(Task(title="Task 1"))
        repository.save(Task(title="Task 2"))
        
        repository.clear()
        all_tasks = repository.find_all()
        assert len(all_tasks) == 0
