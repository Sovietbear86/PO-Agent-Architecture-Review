"""Jira router with endpoints for Jira task operations."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query, BackgroundTasks
from pydantic import BaseModel
from app.services.jira_client import JiraClient
from app.config import settings

router = APIRouter(prefix="/api/v1/jira", tags=["jira"])


class JiraSearchQuery(BaseModel):
    """Query model for Jira search."""
    jql: str = "assignee = currentUser()"
    max_results: int = 50
    start: int = 0
    fields: Optional[List[str]] = None


class JiraTaskCreate(BaseModel):
    """Model for creating a Jira task."""
    summary: str
    description: Optional[str] = None
    project: Optional[str] = None
    issue_type: str = "Task"
    assignee: Optional[str] = None


class JiraStatusUpdate(BaseModel):
    """Model for updating task status."""
    status: str


def get_jira_client() -> JiraClient:
    """Get Jira client instance."""
    return JiraClient(
        url=settings.JIRA_URL,
        api_token=settings.JIRA_API_TOKEN,
        username=settings.JIRA_USERNAME,
    )


@router.get("/health")
async def jira_health():
    """Check Jira connection health."""
    client = get_jira_client()
    try:
        # Try to get current user to verify connection
        client.search_tasks(max_results=1)
        return {"status": "connected", "jira_url": settings.JIRA_URL}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Jira connection failed: {str(e)}",
        )


@router.get("/tasks")
async def list_jira_tasks(
    jql: str = Query("assignee = currentUser()", description="JQL query"),
    max_results: int = Query(50, ge=1, le=100, description="Maximum results"),
    fields: Optional[str] = Query(None, description="Comma-separated fields"),
):
    """List Jira tasks using JQL query."""
    client = get_jira_client()
    try:
        field_list = fields.split(",") if fields else None
        tasks = client.search_tasks(
            jql=jql,
            max_results=max_results,
            fields=field_list,
        )
        return {
            "tasks": tasks,
            "total": len(tasks),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch tasks: {str(e)}",
        )


@router.get("/tasks/{task_key}")
async def get_jira_task(task_key: str):
    """Get a single Jira task by key."""
    client = get_jira_client()
    try:
        task = client.get_task(task_key)
        return {"task": task}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch task: {str(e)}",
        )


@router.get("/tasks/my")
async def get_my_jira_tasks(
    max_results: int = Query(50, ge=1, le=100, description="Maximum results"),
):
    """Get tasks assigned to current user."""
    client = get_jira_client()
    try:
        tasks = client.get_my_tasks(max_results=max_results)
        return {
            "tasks": tasks,
            "total": len(tasks),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch my tasks: {str(e)}",
        )


@router.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_jira_task(
    task_data: JiraTaskCreate,
    background_tasks: BackgroundTasks = None,
):
    """Create a new Jira task."""
    client = get_jira_client()
    try:
        task = client.create_task(
            summary=task_data.summary,
            description=task_data.description,
            project=task_data.project,
            issue_type=task_data.issue_type,
            assignee=task_data.assignee,
        )
        return {"message": "Task created successfully", "task": task}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to create task: {str(e)}",
        )


@router.patch("/tasks/{task_key}/status")
async def update_jira_task_status(
    task_key: str,
    status_update: JiraStatusUpdate,
):
    """Update Jira task status."""
    client = get_jira_client()
    try:
        task = client.update_task_status(task_key, status_update.status)
        return {"message": "Status updated successfully", "task": task}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to update status: {str(e)}",
        )


@router.get("/projects")
async def list_projects(max_results: int = Query(50, ge=1, le=100)):
    """List available Jira projects."""
    client = get_jira_client()
    try:
        response = client._get_client().get(
            "/rest/api/2/project",
            params={"maxResults": max_results},
        )
        response.raise_for_status()
        projects = response.json()
        return {
            "projects": projects,
            "total": len(projects),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch projects: {str(e)}",
        )
