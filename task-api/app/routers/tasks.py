"""Task router with CRUD endpoints."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field
from app.models.task import Status
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, task_to_response
from app.services.task_service import TaskService

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


def get_task_service() -> TaskService:
    from app.repositories.task_repository import TaskRepository
    return TaskService(TaskRepository())


class GetByUrlRequest(BaseModel):
    url: str = Field(..., description="SWTR task URL")


class StatusUpdate(BaseModel):
    status: Status


def _raw_status_matches(task, requested: str) -> bool:
    wanted = requested.casefold().strip()
    source_data = task.source_data or {}
    candidates = [
        task.status.value if hasattr(task.status, 'value') else str(task.status),
        source_data.get('workflow_status'),
        source_data.get('workflow_status_name'),
    ]
    return any(isinstance(value, str) and value.casefold().strip() == wanted for value in candidates)


@router.get("", response_model=List[TaskResponse])
def list_tasks(
    status_filter: str | None = Query(None, alias="status", description="Local or raw AS21 status"),
    assignee: str | None = Query(None, description="Filter by assignee"),
    source: str | None = Query(None, description="Filter by source (e.g., 'swtr')"),
    limit: int = Query(10000, ge=1, le=10000, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """List tasks. Unknown AS21 statuses are filtered locally, never rejected as 422."""
    service = get_task_service()
    local_status = None
    if status_filter:
        normalized = status_filter.casefold().strip()
        direct = {item.value: item for item in Status}
        local_status = direct.get(normalized)
    # For raw source statuses read the bounded source set and filter here.
    fetch_limit = 10000 if status_filter and local_status is None else limit
    fetch_offset = 0 if status_filter and local_status is None else offset
    tasks = service.get_tasks(status=local_status, assignee=assignee, source=source, limit=fetch_limit, offset=fetch_offset)
    if status_filter and local_status is None:
        tasks = [task for task in tasks if _raw_status_matches(task, status_filter)][offset:offset + limit]
    return [task_to_response(task) for task in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: UUID):
    service = get_task_service()
    task = service.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task_to_response(task)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task_data: TaskCreate):
    service = get_task_service()
    task = service.create_task(task_data)
    return task_to_response(task)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: UUID, task_data: TaskUpdate):
    service = get_task_service()
    task = service.update_task(task_id, task_data)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task_to_response(task)


@router.patch("/{task_id}/status", response_model=TaskResponse)
def update_task_status(task_id: UUID, status_update: StatusUpdate):
    service = get_task_service()
    task = service.update_task_status(task_id, status_update.status)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task_to_response(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: UUID):
    service = get_task_service()
    if not service.delete_task(task_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")


@router.post("/get_by_url", response_model=TaskResponse)
def get_task_by_url(request: GetByUrlRequest):
    import re
    service = get_task_service()
    match = re.search(r"/unit/([A-Z0-9-]+)", request.url)
    if not match:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid URL: could not extract task ID")
    task_code = match.group(1)
    task = service.get_task_by_source_id(task_code)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_code} not found")
    return task_to_response(task)
