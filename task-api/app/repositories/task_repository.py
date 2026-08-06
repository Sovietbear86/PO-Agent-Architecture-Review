"""In-memory task repository with file persistence."""
from typing import Optional, List
from uuid import UUID
from app.models.task import Task, Status
import json
import os

TASKS_FILE = os.path.join(os.path.expanduser('~'), '.task-tracker', 'tasks.json')


class TaskRepository:
    """In-memory repository for task operations (singleton) with file persistence."""

    _instance: Optional['TaskRepository'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tasks = {}
            cls._instance._load_tasks()
        return cls._instance

    def __init__(self):
        # Already initialized in __new__
        pass

    def _load_tasks(self):
        """Load tasks from file if exists."""
        if os.path.exists(TASKS_FILE):
            try:
                with open(TASKS_FILE, 'r') as f:
                    data = json.load(f)
                    for task_data in data:
                        task = Task.from_dict(task_data)
                        self._tasks[task.id] = task
            except Exception:
                pass

    def _save_tasks(self):
        """Save tasks to file."""
        os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)
        data = [task.to_dict() for task in self._tasks.values()]
        with open(TASKS_FILE, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def save(self, task: Task) -> Task:
        """Save or update a task."""
        self._tasks[task.id] = task
        self._save_tasks()
        return task
    
    def find_by_id(self, task_id: UUID) -> Optional[Task]:
        """Find task by ID."""
        return self._tasks.get(task_id)

    def find_by_source_id(self, source_id: str) -> Optional[Task]:
        """Find task by external source ID."""
        for task in self._tasks.values():
            if task.source_id == source_id:
                return task
        return None

    def find_all(self, status: Optional['Status'] = None,
                 assignee: Optional[str] = None,
                 source: Optional[str] = None,
                 limit: int = 10000,
                 offset: int = 0) -> List['Task']:
        """Find all tasks with optional filters."""
        tasks = list(self._tasks.values())

        if status is not None:
            tasks = [t for t in tasks if t.status == status]

        if assignee is not None:
            tasks = [t for t in tasks if t.assignee == assignee]

        if source is not None:
            tasks = [t for t in tasks if t.source == source]

        # Apply pagination after filtering
        total_filtered = len(tasks)
        start = min(offset, total_filtered)
        end = min(start + limit, total_filtered)

        return tasks[start:end]
    
    def update(self, task_id: UUID, task: Task) -> Optional[Task]:
        """Update a task by ID."""
        if task_id not in self._tasks:
            return None
        self._tasks[task_id] = task
        self._save_tasks()
        return task

    def delete(self, task_id: UUID) -> bool:
        """Delete a task by ID."""
        if task_id in self._tasks:
            del self._tasks[task_id]
            self._save_tasks()
            return True
        return False

    def clear(self) -> None:
        """Clear all tasks."""
        self._tasks.clear()
        self._save_tasks()
