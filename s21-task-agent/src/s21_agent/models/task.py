from datetime import datetime
from pydantic import BaseModel, Field


class Attachment(BaseModel):
    id: str
    name: str
    content_type: str | None = None
    size_bytes: int | None = None
    author: str | None = None
    created_at:4 datetime | None = None
    download_url: str | None = None


class Comment(BaseModel):
    id: str
    author: str | None = None
    body: str
    created_at: datetime | None = None


class Task(BaseModel):
    id: str
    title: str
    description: str = ""
    status: str | None = None
    project: str | None = None
    author: str | None = None
    assignee: str | None = None
    labels: list[str] = Field(default_factory=list)
    components: list[str] = Field(default_factory=list)
    comments: list[Comment] = Field(default_factory=list)
    attachments: list[Attachment] = Field(default_factory=list)
    url: str | None = None
