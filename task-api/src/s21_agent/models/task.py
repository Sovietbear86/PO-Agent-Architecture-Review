"""Task models for S21 Agent."""
from datetime import datetime
from pydantic import BaseModel, Field


class Attachment(BaseModel):
    """Task attachment model."""
    id: str
    name: str
    content_type: str | None = None
    size_bytes: int | None = None
    author: str | None = None
    created_at: datetime | None = None
    download_url: str | None = None


class Comment(BaseModel):
    """Task comment model."""
    id: str
    author: str | None = None
    body: str
    created_at: datetime | None = None


class Task(BaseModel):
    """Task model matching TaskTracker schema."""
    id: str
    source_id: str
    title: str
    description: str = ""
    status: str
    assignee: str | None = None
    deadline: datetime | None = None
    source_url: str | None = None
    source: str | None = None
    created_at: datetime
    updated_at: datetime
    comments: list[Comment] = Field(default_factory=list)
    attachments: list[Attachment] = Field(default_factory=list)
    url: str | None = None
