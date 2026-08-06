"""Tests for task service."""
import pytest
from app.models.task import Task, Status
from app.repositories.task_repository import TaskRepository
from app.services.task_service import TaskService


@pytest.fixture
def service():
    """Create a fresh service instance for each test."""
    repository = TaskRepository()
    return TaskService(repository)


class TestTaskService:
    """Tests for TaskService."""
    
    def test_create_task(self, service):
        """Test creating a task."""
        from app.schemas.task import TaskCreate
        
        task_data = TaskCreate(
            title="Test Task",
            description="Test Description",
            assignee="John Doe",
        )
        
        task = service.create_task(task_data)
        assert task.id is not None
        assert task.title == "Test Task"
        assert task.description == "Test Description"
        assert task.assignee == "John Doe"
        assert task.status == Status.TODO
    
    def test_get_task_by_id(self, service):
        """Test getting a task by ID."""
        from app.schemas.task import TaskCreate
        
        task_data = TaskCreate(title="Test Task")
        created_task = service.create_task(task_data)
        
        found_task = service.get_task_by_id(created_task.id)
        assert found_task is not None
        assert found_task.title == "Test Task"
    
    def test_get_task_by_id_not_found(self, service):
        """Test getting a non-existent task."""
        from uuid import uuid4
        
        task = service.get_task_by_id(uuid4())
        assert task is None
    
    def test_get_tasks(self, service):
        """Test getting all tasks."""
        from app.schemas.task import TaskCreate
        
        service.create_task(TaskCreate(title="Task 1"))
        service.create_task(TaskCreate(title="Task 2"))
        service.create_task(TaskCreate(title="Task 3"))
        
        tasks = service.get_tasks()
        assert len(tasks) == 3
    
    def test_get_tasks_with_status_filter(self, service):
        """Test getting tasks with status filter."""
        from app.schemas.task import TaskCreate
        
        service.create_task(TaskCreate(title="Task 1"))
        service.create_task(TaskCreate(title="Task 2"))
        
        task2 = service.get_tasks()[1]
        service.update_task_status(task2.id, Status.IN_PROGRESS)
        
        todo_tasks = service.get_tasks(status=Status.TODO)
        assert len(todo_tasks) == 1
    
    def test_update_task(self, service):
        """Test updating a task."""
        from app.schemas.task import TaskCreate, TaskUpdate
        
        task_data = TaskCreate(title="Original Title")
        created_task = service.create_task(task_data)
        
        update_data = TaskUpdate(title="Updated Title", assignee="Jane Doe")
        updated_task = service.update_task(created_task.id, update_data)
        
        assert updated_task is not None
        assert updated_task.title == "Updated Title"
        assert updated_task.assignee == "Jane Doe"
    
    def test_update_task_not_found(self, service):
        """Test updating a non-existent task."""
        from app.schemas.task import TaskUpdate
        from uuid import uuid4
        
        update_data = TaskUpdate(title="Updated Title")
        result = service.update_task(uuid4(), update_data)
        assert result is None
    
    def test_delete_task(self, service):
        """Test deleting a task."""
        from app.schemas.task import TaskCreate
        
        task_data = TaskCreate(title="Test Task")
        created_task = service.create_task(task_data)
        
        result = service.delete_task(created_task.id)
        assert result is True
        
        found_task = service.get_task_by_id(created_task.id)
        assert found_task is None
    
    def test_delete_task_not_found(self, service):
        """Test deleting a non-existent task."""
        from uuid import uuid4
        
        result = service.delete_task(uuid4())
        assert result is False
    
    def test_update_task_status(self, service):
        """Test updating task status."""
        from app.schemas.task import TaskCreate
        
        task_data = TaskCreate(title="Test Task")
        created_task = service.create_task(task_data)
        
        updated_task = service.update_task_status(created_task.id, Status.IN_PROGRESS)
        
        assert updated_task is not None
        assert updated_task.status == Status.IN_PROGRESS
    
    def test_update_task_status_not_found(self, service):
        """Test updating status of a non-existent task."""
        from uuid import uuid4
        
        result = service.update_task_status(uuid4(), Status.IN_PROGRESS)
        assert result is None
