"""Модели данных для Team Performance Agent"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class TeamMember(BaseModel):
    """Модель участника команды"""
    id: str
    full_name: str
    login: str
    email: str
    products: List[str]
    team_role: str
    professional_profile: str
    grade: Optional[int] = None
    competencies: Dict[str, int] = Field(default_factory=dict)
    competency_evidence_file: Optional[str] = None
    allocation_percent: Optional[int] = None
    recommended_max_wip: Optional[int] = None
    regular_non_sprint_load_percent: Optional[int] = None
    planned_absences: List[str] = Field(default_factory=list)


class SprintMetrics(BaseModel):
    """Метрики спринта"""
    sprint_id: str
    committed_effort: float = 0
    completed_effort: float = 0
    added_after_start_effort: float = 0
    carried_over_effort: float = 0
    throughput: int = 0
    blocked_count: int = 0
    unplanned_count: int = 0
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class CompetencyMatchResult(BaseModel):
    """Результат сопоставления компетенций"""
    member_id: str
    member_name: str
    score: float
    competencies: Dict[str, int]
    current_wip: int
    allocation: float
    warning: Optional[str] = None
    recommendation: str


class AnalysisResult(BaseModel):
    """Результат анализа"""
    status: str  # green, yellow, red
    findings: List[str]
    risks: List[str]
    recommendations: List[str]
    sources: List[str]
    constraints: List[str]
    confidence: float = 0.0
    team_members: List[str] = Field(default_factory=list)
    products: List[str] = Field(default_factory=list)
    # Sprint list for user selection
    sprints: List[Dict[str, Any]] = Field(default_factory=list)
    default_sprint: str = ""
    sprint_id: Optional[str] = None
    # Tasks for display
    tasks: List[Dict[str, Any]] = Field(default_factory=list)


class TeamAnalysisRequest(BaseModel):
    """Запрос анализа команды"""
    skill: str
    params: Dict[str, Any] = Field(default_factory=dict)


class SprintHealthRequest(BaseModel):
    """Запрос анализа здоровья спринта"""
    sprint_id: str
    team_members: List[str] = Field(default_factory=list)
    products: List[str] = Field(default_factory=list)


class VelocityRequest(BaseModel):
    """Запрос velocity анализа"""
    period_sprints: int = Field(default=6, ge=1, le=12)
    team_members: List[str] = Field(default_factory=list)
    products: List[str] = Field(default_factory=list)


class FlowRequest(BaseModel):
    """Запрос flow метрик"""
    period_days: int = Field(default=30, ge=7, le=365)
    team_members: List[str] = Field(default_factory=list)
    products: List[str] = Field(default_factory=list)


class WorkloadRequest(BaseModel):
    """Запрос анализа загрузки"""
    period_days: int = Field(default=30, ge=7, le=365)
    team_members: List[str] = Field(default_factory=list)
    products: List[str] = Field(default_factory=list)


class CompetencyMatchRequest(BaseModel):
    """Запрос сопоставления компетенций"""
    task_requirements: Dict[str, int]
    exclude_members: List[str] = Field(default_factory=list)
    max_candidates: int = Field(default=3, ge=1, le=5)


class BottlenecksRequest(BaseModel):
    """Запрос анализа узких мест"""
    period_days: int = Field(default=30, ge=7, le=365)
    team_members: List[str] = Field(default_factory=list)
    products: List[str] = Field(default_factory=list)


class ForecastRequest(BaseModel):
    """Запрос прогноза"""
    sprint_id: str
    remaining_effort: float = 0
    team_members: List[str] = Field(default_factory=list)
    products: List[str] = Field(default_factory=list)


class ReleaseLinkageRequest(BaseModel):
    """Запрос анализа связи с релизом"""
    release_id: str
    team_members: List[str] = Field(default_factory=list)
    products: List[str] = Field(default_factory=list)
