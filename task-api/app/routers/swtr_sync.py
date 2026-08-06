"""SWTR sync router for importing tasks from SberWorks Task Tracker."""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel

from app.services.swtr_sync_service import SWTRSyncService

router = APIRouter(prefix="/api/v1/swtr", tags=["swtr-sync"])


class SyncRequest(BaseModel):
    """Request model for sync operation."""
    space: str = Query("WMB", description="SWTR space to sync from")
    max_results: int = Query(100, ge=1, le=500, description="Maximum number of tasks to sync")


class SyncResponse(BaseModel):
    """Response model for sync operation."""
    imported: int
    tasks: List[Dict[str, Any]]
    source: str
    space: str
    error: Optional[str] = None


class SingleSyncResponse(BaseModel):
    """Response model for single task sync."""
    task: Optional[Dict[str, Any]]
    error: Optional[str] = None


class FilteredSyncResponse(BaseModel):
    """Response model for filtered sync operation."""
    imported: int
    tasks: List[Dict[str, Any]]
    source: str
    assignee: Optional[str] = None
    sprint_id: Optional[str] = None


class SyncMyResponse(BaseModel):
    """Response model for sync-my operation."""
    imported: int
    tasks: List[Dict[str, Any]]
    space: str


@router.get("/health")
async def swtr_health():
    """Check SWTR connection health."""
    service = SWTRSyncService()
    token = service._get_token()
    if token:
        return {
            "status": "connected",
            "token_present": True,
            "token_length": len(token),
        }
    return {
        "status": "disconnected",
        "token_present": False,
        "message": "Get token from https://portal.works.prod.sbt/ssd/privileges",
    }


@router.post("/sync", response_model=SyncResponse)
async def sync_swtr_tasks(request: SyncRequest = None):
    """Sync tasks from SWTR to local task tracker."""
    if request is None:
        request = SyncRequest()

    service = SWTRSyncService()
    result = service.sync_tasks(space=request.space, max_results=request.max_results)

    if 'error' in result:
        return SyncResponse(
            imported=0,
            tasks=[],
            source='swtr',
            space=request.space,
            error=result['error']
        )

    return SyncResponse(
        imported=result.get('imported', 0),
        tasks=result.get('tasks', []),
        source=result.get('source', 'swtr'),
        space=result.get('space', request.space)
    )


@router.post("/sync-user", response_model=SyncMyResponse)
async def sync_my_swtr_tasks_post():
    """Sync tasks assigned to current user from SWTR."""
    service = SWTRSyncService()
    result = service.sync_my_tasks()

    return SyncMyResponse(
        imported=result.get('imported', 0),
        tasks=result.get('tasks', []),
        space=result.get('space', 'WMB')
    )


@router.get("/sync-user", response_model=List[Dict[str, Any]])
async def sync_my_swtr_tasks_get(space: str = Query("WMB", description="SWTR space")):
    """Get tasks assigned to current user from SWTR (read-only)."""
    service = SWTRSyncService()
    return service.get_my_tasks(space=space)


@router.get("/tasks/{task_code}")
async def sync_single_task(task_code: str):
    """Sync a single task from SWTR by its code."""
    service = SWTRSyncService()
    task = service.sync_single_task(task_code)

    if task is None:
        return SingleSyncResponse(task=None, error="Task not found or sync failed")

    return SingleSyncResponse(task=task.to_dict(), error=None)


@router.get("/spaces")
async def list_spaces():
    """List available SWTR spaces."""
    service = SWTRSyncService()
    return {
        "spaces": [
            {"code": "WMB", "name": "Управленческие задачи"},
            {"code": "WMB2", "name": "Управленческие задачи 2"},
            {"code": "CONVSUPP", "name": "Конвент Саппорт"},
        ],
        "default": "WMB"
    }


@router.get("/sprints")
async def list_sprints(space: str = Query("WMB", description="SWTR space")):
    """List active sprints for a space."""
    service = SWTRSyncService(api_port=8003)
    result = service.get_active_sprints(space=space)
    return result


@router.get("/sprint-tasks")
async def get_sprint_tasks(
    sprint_id: str = Query(..., description="Sprint ID (e.g., WMB-SPRNT-2)"),
    space: str = Query("WMB", description="SWTR space")
):
    """Get tasks from a specific sprint."""
    service = SWTRSyncService(api_port=8003)
    result = service.get_sprint_tasks(sprint_id=sprint_id, space=space)
    return result


@router.post("/sync-filtered", response_model=FilteredSyncResponse)
async def sync_filtered_tasks(
    assignee: str = Query(None, description="Filter by assignee name (partial match)"),
    sprint_id: str = Query(None, description="Filter by sprint ID (e.g., OLP-SPRNT-2)")
):
    """Sync tasks filtered by assignee and/or sprint_id.
    
    Uses client-side filtering on tasks already in the local repository.
    This provides fast filtering without re-syncing from SWTR.
    """
    service = SWTRSyncService()
    result = service.sync_tasks_filtered(assignee=assignee, sprint_id=sprint_id)
    
    return FilteredSyncResponse(
        imported=result.get('imported', 0),
        tasks=result.get('tasks', []),
        source=result.get('source', 'swtr'),
        assignee=result.get('assignee'),
        sprint_id=result.get('sprint_id')
    )
