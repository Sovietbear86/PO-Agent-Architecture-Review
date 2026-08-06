"""Task router with CRUD endpoints."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Query, Body
from pydantic import BaseModel, Field
from app.models.task import Status
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, task_to_response
from app.services.task_service import TaskService

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


def get_task_service() -> TaskService:
    """Get task service instance."""
    from app.repositories.task_repository import TaskRepository
    return TaskService(TaskRepository())


class GetByUrlRequest(BaseModel):
    """Request for getting task by URL."""
    url: str = Field(..., description="SWTR task URL")


class StatusUpdate(BaseModel):
    """Schema for status update."""
    status: Status


@router.get("/", response_model=List[TaskResponse])
def list_tasks(
    status: Status | None = Query(None, description="Filter by status"),
    assignee: str | None = Query(None, description="Filter by assignee"),
    source: str | None = Query(None, description="Filter by source (e.g., 'swtr')"),
    limit: int = Query(10000, ge=1, le=10000, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """List tasks with optional filters."""
    service = get_task_service()
    tasks = service.get_tasks(status=status, assignee=assignee, source=source, limit=limit, offset=offset)
    return [task_to_response(task) for task in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: UUID):
    """Get task by ID."""
    service = get_task_service()
    task = service.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task_to_response(task)


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task_data: TaskCreate):
    """Create a new task."""
    service = get_task_service()
    task = service.create_task(task_data)
    return task_to_response(task)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: UUID, task_data: TaskUpdate):
    """Update a task."""
    service = get_task_service()
    task = service.update_task(task_id, task_data)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task_to_response(task)


@router.patch("/{task_id}/status", response_model=TaskResponse)
def update_task_status(task_id: UUID, status_update: StatusUpdate):
    """Update only the status of a task."""
    service = get_task_service()
    task = service.update_task_status(task_id, status_update.status)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task_to_response(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: UUID):
    """Delete a task."""
    service = get_task_service()
    if not service.delete_task(task_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")


@router.post("/get_by_url", response_model=TaskResponse)
def get_task_by_url(request: GetByUrlRequest):
    """Get task by SWTR URL."""
    import re
    service = get_task_service()

    # Extract task code from URL
    # Format: https://portal.works.prod.sbt/swtr/units/all/unit/WMB-12345?...
    match = re.search(r"/unit/([A-Z0-9-]+)", request.url)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL: could not extract task ID"
        )

    task_code = match.group(1)

    # Find task by source_id (which is the task code like WMB-12345)
    task = service.get_task_by_source_id(task_code)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_code} not found"
        )

    return task_to_response(task)
