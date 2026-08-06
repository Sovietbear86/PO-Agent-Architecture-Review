"""Task service layer."""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.models.task import Task, Status
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    """Service layer for task operations."""

    def __init__(self, repository: TaskRepository):
        self.repository = repository

    def create_task_from_dict(self, task_data: dict) -> Task:
        """Create a task from dictionary data (direct Task creation)."""
        # Extract fields from dict
        title = task_data.get('title', '')
        description = task_data.get('description')
        assignee = task_data.get('assignee')
        deadline = task_data.get('deadline')
        source_url = task_data.get('source_url')
        # Handle status - if it's a valid Status enum value, use it; otherwise use as string
        status_val = task_data.get('status', 'todo')
        if isinstance(status_val, str):
            # Try to create Status enum, fall back to string for external statuses
            try:
                status = Status(status_val)
            except ValueError:
                status = status_val
        else:
            status = Status(status_val)

        # Parse deadline if it's a string
        deadline_dt = None
        if deadline:
            try:
                deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                deadline_dt = None

        # Create Task directly
        task = Task(
            title=title,
            description=description,
            assignee=assignee,
            deadline=deadline_dt,
            source_url=source_url,
            status=status,
            source=task_data.get('source'),
            source_id=task_data.get('source_id'),
            source_data=task_data.get('source_data', {}),
        )
        # Set existing id and timestamps
        if 'id' in task_data and task_data['id']:
            try:
                task.id = UUID(task_data['id']) if isinstance(task_data['id'], str) else task_data['id']
            except ValueError:
                pass  # Keep auto-generated ID
        if 'created_at' in task_data and task_data['created_at']:
            # Handle datetime objects or strings
            created_at = task_data['created_at']
            if isinstance(created_at, str):
                task.created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                task.created_at = created_at
        if 'updated_at' in task_data and task_data['updated_at']:
            updated_at = task_data['updated_at']
            if isinstance(updated_at, str):
                task.updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            else:
                task.updated_at = updated_at

        return self.repository.save(task)
    
    def create_task(self, task_data: TaskCreate) -> Task:
        """Create a new task."""
        task = Task(
            title=task_data.title,
            description=task_data.description,
            assignee=task_data.assignee,
            status=task_data.status if hasattr(task_data, 'status') else Status.TODO,
            source_url=task_data.source_url,
            source_id=task_data.source_id,
            source=task_data.source,
            source_data=task_data.source_data,
        )
        return self.repository.save(task)
    
    def get_task_by_id(self, task_id: UUID) -> Optional[Task]:
        """Get task by ID."""
        return self.repository.find_by_id(task_id)

    def get_task_by_source_id(self, source_id: str) -> Optional[Task]:
        """Get task by external source ID (e.g., WMB-12345)."""
        return self.repository.find_by_source_id(source_id)

    def get_tasks(self, status: Optional[Status] = None,
                  assignee: Optional[str] = None,
                  source: Optional[str] = None,
                  limit: int = 10000,
                  offset: int = 0) -> List[Task]:
        """Get all tasks with optional filters."""
        # Ensure limit and offset are integers
        limit = int(limit) if not isinstance(limit, int) else limit
        offset = int(offset) if not isinstance(offset, int) else offset
        return self.repository.find_all(status=status, assignee=assignee, source=source, limit=limit, offset=offset)
    
    def update_task(self, task_id: UUID, task_data: TaskUpdate) -> Optional[Task]:
        """Update a task."""
        existing_task = self.repository.find_by_id(task_id)
        if existing_task is None:
            return None
        
        update_data = task_data.model_dump(exclude_unset=True)
        existing_task.update(**update_data)
        return self.repository.update(task_id, existing_task)
    
    def delete_task(self, task_id: UUID) -> bool:
        """Delete a task."""
        return self.repository.delete(task_id)
    
    def update_task_status(self, task_id: UUID, status: Status) -> Optional[Task]:
        """Update only the status of a task."""
        existing_task = self.repository.find_by_id(task_id)
        if existing_task is None:
            return None
        
        existing_task.update(status=status)
        return self.repository.update(task_id, existing_task)
