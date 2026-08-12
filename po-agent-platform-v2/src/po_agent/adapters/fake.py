"""Fake AS21 adapter for testing purposes."""

from datetime import datetime, timedelta
from typing import Optional

from po_agent.adapters.as21 import AS21Adapter
from po_agent.domain.models import (
    Attachment,
    AttachmentType,
    StatusCategory,
    StatusTransition,
    Task,
    TaskPriority,
    TaskStatus,
)


class FakeAS21Adapter(AS21Adapter):
    """Deterministic AS21 adapter used for harness acceptance without SWTR."""

    def __init__(self):
        self._tasks: dict[str, Task] = {}
        self._sprints: dict[str, list[str]] = {}
        self._releases: dict[str, list[str]] = {}
        self._attachments: dict[str, list[Attachment]] = {}
        self._init_fixtures()

    def _init_fixtures(self) -> None:
        now = datetime.now()
        task1 = Task(key="WMB-101",id="task-001",title="Implement user authentication",description="Add OAuth2 support for user login",status=TaskStatus.RESOLVED,status_category=StatusCategory.COMPLETED_PENDING,status_transitions=[StatusTransition(from_status=TaskStatus.OPEN,to_status=TaskStatus.IN_PROGRESS,timestamp=now-timedelta(days=10),author="Ivanov.I.I"),StatusTransition(from_status=TaskStatus.IN_PROGRESS,to_status=TaskStatus.RESOLVED,timestamp=now-timedelta(days=3),author="Petrov.P.P")],created_at=now-timedelta(days=12),updated_at=now-timedelta(days=3),assignee="Ivanov.I.I",priority=TaskPriority.HIGH,estimate_hours=8,sprint_id="WMB-SPRNT-1",release_id="WMB-2024-Q3",source="test")
        task2 = Task(key="WMB-102",id="task-002",title="Fix login bug",description="Users cannot log in on mobile devices",status=TaskStatus.IN_PROGRESS,status_category=StatusCategory.ACTIVE_WORK,status_transitions=[StatusTransition(from_status=TaskStatus.OPEN,to_status=TaskStatus.IN_PROGRESS,timestamp=now-timedelta(days=5),author="Sidorov.S.S")],created_at=now-timedelta(days=7),updated_at=now-timedelta(days=2),assignee="Sidorov.S.S",priority=TaskPriority.CRITICAL,estimate_hours=5,sprint_id="WMB-SPRNT-1",release_id="WMB-2024-Q3",source="test")
        task3 = Task(key="WMB-103",id="task-003",title="Add analytics dashboard",description="Create dashboard for team metrics",status=TaskStatus.OPEN,status_category=StatusCategory.BACKLOG,created_at=now-timedelta(days=20),updated_at=now-timedelta(days=20),priority=TaskPriority.LOW,estimate_hours=13,sprint_id="WMB-SPRNT-2",release_id="WMB-2024-Q3",source="test")
        task4 = Task(key="DMS-201",id="task-004",title="Data migration script",description="Migrate old data to new schema",status=TaskStatus.CLOSED,status_category=StatusCategory.COMPLETED,status_transitions=[StatusTransition(from_status=TaskStatus.OPEN,to_status=TaskStatus.IN_PROGRESS,timestamp=now-timedelta(days=15)),StatusTransition(from_status=TaskStatus.IN_PROGRESS,to_status=TaskStatus.CLOSED,timestamp=now-timedelta(days=5))],created_at=now-timedelta(days=18),updated_at=now-timedelta(days=5),estimate_hours=16,sprint_id="DMS-SPRNT-1",release_id="DMS-2024-Q3",source="test")
        task5 = Task(key="DMS-202",id="task-005",title="API endpoint for reports",description="Create REST endpoint for report generation",status=TaskStatus.NEED_INFO,status_category=StatusCategory.WAITING,created_at=now-timedelta(days=8),updated_at=now-timedelta(days=1),estimate_hours=8,sprint_id="DMS-SPRNT-1",release_id="DMS-2024-Q3",source="test")
        self._tasks={t.key:t for t in (task1,task2,task3,task4,task5)}
        self._sprints={"WMB-SPRNT-1":["WMB-101","WMB-102"],"WMB-SPRNT-2":["WMB-103"],"DMS-SPRNT-1":["DMS-201","DMS-202"]}
        self._releases={"WMB-2024-Q3":["WMB-101","WMB-102","WMB-103"],"DMS-2024-Q3":["DMS-201","DMS-202"]}
        self._attachments={
            "WMB-101":[Attachment(id="att-001",name="requirements.xlsx",type=AttachmentType.EXCEL,size_bytes=102400,created_at=now-timedelta(days=12),description="Initial requirements")],
            "WMB-102":[Attachment(id="att-002",name="screenshot.png",type=AttachmentType.IMAGE,size_bytes=51200,created_at=now-timedelta(days=6),description="Bug screenshot")],
            "WMB-103":[Attachment(id="att-004",name="customer-request.msg",type=AttachmentType.MSG,size_bytes=64000,created_at=now-timedelta(days=7),description="Customer email")],
            "DMS-201":[Attachment(id="att-003",name="migration-plan.pdf",type=AttachmentType.PDF,size_bytes=82000,created_at=now-timedelta(days=16),description="Migration plan")],
        }

    async def get_task(self, task_key: str) -> Optional[Task]: return self._tasks.get(task_key)
    async def search_tasks(self,jql: str,max_results: int=50,fields: Optional[list[str]]=None) -> list[Task]:
        results=[]; q=jql.lower()
        if "project" in q:
            parts=q.split("project"); rest=parts[1].strip() if len(parts)>1 else ""; code=rest.split("=")[-1].strip().split()[0].upper() if "=" in rest else ""
            results=[t for t in self._tasks.values() if t.key.startswith(code)]
        elif "assignee" in q:
            assignee=jql.split("=")[-1].strip(); results=[t for t in self._tasks.values() if t.assignee and assignee.lower() in t.assignee.lower()]
        elif "sprint" in q:
            sid=jql.split("=")[-1].strip(); results=[self._tasks[k] for k in self._sprints.get(sid,[]) if k in self._tasks]
        elif "key" in q:
            key=jql.split("=")[-1].strip(); results=[self._tasks[key]] if key in self._tasks else []
        else: results=list(self._tasks.values())
        return results[:max_results]
    async def get_task_history(self,task_key:str) -> list[StatusTransition]: return self._tasks.get(task_key).status_transitions if task_key in self._tasks else []
    async def get_sprint_tasks(self,sprint_id:str,space:Optional[str]=None) -> list[Task]: return [self._tasks[k] for k in self._sprints.get(sprint_id,[]) if k in self._tasks]
    async def get_release_tasks(self,release_id:str,space:Optional[str]=None) -> list[Task]: return [self._tasks[k] for k in self._releases.get(release_id,[]) if k in self._tasks]
    async def get_attachment_metadata(self,task_key:str,attachment_id:Optional[str]=None) -> list[Attachment]:
        items=self._attachments.get(task_key,[])
        return [a for a in items if a.id==attachment_id] if attachment_id else items
    async def close(self) -> None: pass
    def get_all_tasks(self) -> list[Task]: return list(self._tasks.values())
    def get_task_count(self) -> int: return len(self._tasks.values())
