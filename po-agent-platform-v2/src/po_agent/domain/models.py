"""Canonical domain models for PO Agent Platform v2.

Transport-independent domain entities. AS21-specific parsing belongs in adapters;
canonical fields contain only facts that deterministic capabilities may consume.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field

class TaskKey(str): pass
class SprintId(str): pass
class ReleaseId(str): pass
class MemberId(str): pass

def task_key_schema(): return {"type":"string","pattern":r"^[A-Z]+-\d+$"}
def sprint_id_schema(): return {"type":"string","pattern":r"^[A-Z]+-SPRNT-\d+$"}
def release_id_schema(): return {"type":"string","pattern":r"^[A-Z]+-\d{4}-[A-Z]+\d*$"}
def member_id_schema(): return {"type":"string","pattern":r"^[A-Z]+\.[A-Z]+\.[A-Z]+$"}

class Timestamp(BaseModel):
    value: datetime
    timezone: Optional[str]=None

class StatusCategory(str,Enum):
    BACKLOG="backlog"; WAITING="waiting"; ACTIVE_WORK="active_work"; REVIEW_QUEUE="review_queue"; REVIEW="review"; QA_QUEUE="qa_queue"; TESTING="testing"; COMPLETED_PENDING="completed_pending"; COMPLETED="completed"; CANCELLED="cancelled"; UNKNOWN="unknown"
class TaskStatus(str,Enum):
    UNKNOWN="Unknown"; OPEN="Open"; NEED_INFO="Need info"; IN_PROGRESS="In progress"; READY_FOR_REVIEW="Ready for review"; IN_REVIEW="In review"; READY_FOR_QA="Ready for QA"; QA="QA"; REOPENED="Reopened"; RESOLVED="Resolved"; CLOSED="Closed"; CANCELLED="Cancelled"
class StatusTransition(BaseModel):
    from_status: TaskStatus; to_status: TaskStatus; timestamp: datetime; author: Optional[str]=None; transition_type: Optional[str]=None
class AttachmentType(str,Enum):
    EXCEL="excel"; WORD="word"; PDF="pdf"; MSG="msg"; IMAGE="image"; TEXT="text"; OTHER="other"
class Attachment(BaseModel):
    id:str; name:str; type:AttachmentType; size_bytes:int; created_at:datetime; url:Optional[str]=None; description:Optional[str]=None
class TaskPriority(str,Enum):
    LOW="Low"; MEDIUM="Medium"; HIGH="High"; URGENT="Urgent"; CRITICAL="Critical"

class Task(BaseModel):
    key:str=Field(...,pattern=r"^[A-Z]+-\d+$"); id:str
    title:str=Field(...,min_length=1,max_length=200); description:Optional[str]=None
    status:TaskStatus; status_category:StatusCategory; status_raw:Optional[str]=None; status_transitions:list[StatusTransition]=[]
    assignee:Optional[str]=None; assignee_id:Optional[str]=None; assignee_login:Optional[str]=None
    created_at:datetime; updated_at:datetime; due_date:Optional[datetime]=None; resolved_at:Optional[datetime]=None; closed_at:Optional[datetime]=None
    priority:Optional[TaskPriority]=None; estimate_hours:Optional[float]=None; time_spent_hours:Optional[float]=None
    project_space:Optional[str]=None; sprint_id:Optional[str]=None; release_id:Optional[str]=None; parent_key:Optional[str]=None; depends_on:list[str]=[]
    labels:list[str]=[]; components:list[str]=[]; attachments:list[Attachment]=[]
    source:str="swtr"; source_url:Optional[str]=None; source_data:dict[str,Any]=Field(default_factory=dict,repr=False)
    @property
    def is_completed(self): return self.status in (TaskStatus.RESOLVED,TaskStatus.CLOSED,TaskStatus.CANCELLED)
    @property
    def is_blocked(self): return self.status==TaskStatus.NEED_INFO
    @property
    def age_days(self): return (datetime.now()-self.created_at).days
    @property
    def time_in_current_status_hours(self): return 0.0 if not self.status_transitions else (datetime.now()-self.status_transitions[-1].timestamp).total_seconds()/3600
    @property
    def cycle_time_hours(self):
        start=next((t.timestamp for t in self.status_transitions if t.to_status==TaskStatus.IN_PROGRESS),self.created_at); end=self.resolved_at or self.closed_at or datetime.now(); return (end-start).total_seconds()/3600
    @property
    def lead_time_hours(self):
        end=self.resolved_at or self.closed_at or datetime.now(); return (end-self.created_at).total_seconds()/3600

class SprintState(str,Enum): FUTURE="future"; ACTIVE="active"; CLOSED="closed"
class Sprint(BaseModel):
    id:str=Field(...,pattern=r"^[A-Z]+-SPRNT-\d+$"); name:str; space:str; start_date:datetime; end_date:datetime; created_at:datetime; closed_at:Optional[datetime]=None; state:SprintState; committed_tasks:list[str]=[]; completed_tasks:list[str]=[]; description:Optional[str]=None; goal:Optional[str]=None; velocity_target:Optional[int]=None
    @property
    def duration_days(self): return (self.end_date-self.start_date).days
    @property
    def is_current(self):
        now=datetime.now(); return self.start_date<=now<=self.end_date and self.state==SprintState.ACTIVE
    @property
    def is_past(self): return self.state==SprintState.CLOSED
    @property
    def is_upcoming(self): return datetime.now()<self.start_date and self.state==SprintState.FUTURE

class ReleaseState(str,Enum): PLANNED="planned"; IN_PROGRESS="in_progress"; READY_FOR_TESTING="ready_for_testing"; RELEASED="released"; CANCELLED="cancelled"
class Release(BaseModel):
    id:str=Field(...,pattern=r"^[A-Z]+-\d{4}-[A-Z]+\d*$"); name:str; space:str; target_date:Optional[datetime]=None; created_at:datetime; released_at:Optional[datetime]=None; state:ReleaseState; scheduled_tasks:list[str]=[]; completed_tasks:list[str]=[]; blocked_tasks:list[str]=[]; linked_sprints:list[str]=[]; description:Optional[str]=None; version:Optional[str]=None; epic:Optional[str]=None
    @property
    def completion_ratio(self): return 1.0 if not self.scheduled_tasks else len(self.completed_tasks)/len(self.scheduled_tasks)
    @property
    def is_on_track(self): return False if self.state==ReleaseState.CANCELLED else True if self.state==ReleaseState.RELEASED else self.completion_ratio>=0.8

class TeamRole(str,Enum):
    PRODUCT_OWNER="Владелец продукта"; TECH_LEAD="Лидер продукта"; DEVELOPER="Участник команды"; QA="Участник команды"; ANALYST="Участник команды"; ARCHITECT="Участник команды"; OTHER="Участник команды"
class Competency(BaseModel):
    name:str; level:int=Field(ge=1,le=10); years_experience:Optional[int]=None; evidence:Optional[str]=None
class TeamMember(BaseModel):
    id:str; full_name:str; email:Optional[str]=None; grade:Optional[int]=None; team_role:TeamRole; products:list[str]=[]; competencies:dict[str,Competency]={}; allocation_percent:Optional[float]=Field(None,ge=0,le=100); recommended_max_wip:Optional[int]=None; is_active:bool=True; planned_absences:list[datetime]=[]
    @property
    def primary_product(self): return self.products[0] if self.products else None
    @property
    def total_competency_level(self): return sum(c.level for c in self.competencies.values())

class DependencyType(str,Enum): BLOCKING="blocking"; BLOCKED_BY="blocked_by"; RELATED="related"; DUPLICATE="duplicate"
class Dependency(BaseModel):
    task_key:str=Field(...,pattern=r"^[A-Z]+-\d+$"); depends_on:str=Field(...,pattern=r"^[A-Z]+-\d+$"); type:DependencyType; description:Optional[str]=None; resolved_at:Optional[datetime]=None
    @property
    def is_blocking(self): return self.type==DependencyType.BLOCKING

def normalize_task_status(raw_status:str)->TaskStatus:
    status_map={
        "open":TaskStatus.OPEN,"открыта":TaskStatus.OPEN,
        "todo":TaskStatus.OPEN,"backlog":TaskStatus.OPEN,
        "need info":TaskStatus.NEED_INFO,"требуется информация":TaskStatus.NEED_INFO,
        "in progress":TaskStatus.IN_PROGRESS,"in_progress":TaskStatus.IN_PROGRESS,"в работе":TaskStatus.IN_PROGRESS,
        "ready for review":TaskStatus.READY_FOR_REVIEW,"готово к ревью":TaskStatus.READY_FOR_REVIEW,
        "in review":TaskStatus.IN_REVIEW,"на ревью":TaskStatus.IN_REVIEW,
        "ready for qa":TaskStatus.READY_FOR_QA,"готово к qa":TaskStatus.READY_FOR_QA,
        "qa":TaskStatus.QA,"тестирование":TaskStatus.QA,
        "reopened":TaskStatus.REOPENED,"переоткрыта":TaskStatus.REOPENED,
        "resolved":TaskStatus.RESOLVED,"решена":TaskStatus.RESOLVED,
        "closed":TaskStatus.CLOSED,"закрыта":TaskStatus.CLOSED,
        "done":TaskStatus.CLOSED,"completed":TaskStatus.CLOSED,"finished":TaskStatus.CLOSED,
        "cancelled":TaskStatus.CANCELLED,"отменена":TaskStatus.CANCELLED,
    }
    return status_map.get((raw_status or "").lower().strip(),TaskStatus.UNKNOWN)

def get_status_category(status:TaskStatus)->StatusCategory:
    return {TaskStatus.OPEN:StatusCategory.BACKLOG,TaskStatus.NEED_INFO:StatusCategory.WAITING,TaskStatus.IN_PROGRESS:StatusCategory.ACTIVE_WORK,TaskStatus.READY_FOR_REVIEW:StatusCategory.REVIEW_QUEUE,TaskStatus.IN_REVIEW:StatusCategory.REVIEW,TaskStatus.READY_FOR_QA:StatusCategory.QA_QUEUE,TaskStatus.QA:StatusCategory.TESTING,TaskStatus.REOPENED:StatusCategory.ACTIVE_WORK,TaskStatus.RESOLVED:StatusCategory.COMPLETED_PENDING,TaskStatus.CLOSED:StatusCategory.COMPLETED,TaskStatus.CANCELLED:StatusCategory.CANCELLED,TaskStatus.UNKNOWN:StatusCategory.UNKNOWN}.get(status,StatusCategory.UNKNOWN)