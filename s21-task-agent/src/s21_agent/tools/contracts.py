from typing import Any
from pydantic import BaseModel, Field


class SearchTasksInput(BaseModel):
    query: str = ""
    project: list[str] = Field(default_factory=list)
    status: list[str] = Field(default_factory=list)
    author: list[str] = Field(default_factory=list)
    assignee: list[str] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    components: list[str] = Field(default_factory=list)
    attachment_types: list[str] = Field(default_factory=list)
    limit: int = 50


class GetTaskInput(BaseModel):
    task_id: str
    include_comments: bool = True
    include_history: bool = True
    include_links: bool = True
    include_attachments: bool = True


class ToolResult(BaseModel):
    ok: bool
    data: Any = None
    error: str | None = None
