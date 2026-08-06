from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SprintMetrics:
    """Metrics for a sprint"""
    sprint_id: str
    committed_effort: float
    completed_effort: float
    added_after_start_effort: float = 0
    carried_over_effort: float = 0
    throughput: int = 0
    blocked_count: int = 0
    unplanned_count: int = 0
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    @property
    def predictability(self) -> float:
        return self.completed_effort / self.committed_effort if self.committed_effort else 0.0

    @property
    def scope_change_rate(self) -> float:
        return self.added_after_start_effort / self.committed_effort if self.committed_effort else 0.0


@dataclass
class FlowMetrics:
    """Flow metrics for team analysis"""
    throughput: int
    avg_cycle_time: float
    avg_lead_time: float
    avg_wip: float
    flow_efficiency: float
    blocked_time: float = 0
    review_time: float = 0
    testing_time: float = 0


@dataclass
class ThroughputMetrics:
    """Throughput metrics for velocity analysis"""
    daily_throughput: list[int]
    weekly_throughput: list[int]
    monthly_throughput: list[int]
    avg_throughput: float
    throughput_std: float
    trend: str  # "increasing", "stable", "decreasing"


@dataclass
class MemberLoad:
    """Load metrics for a team member"""
    login: str
    full_name: str
    total_tasks: int
    completed_tasks: int
    wip: int
    blocked_tasks: int
    on_hold_tasks: int
    overdue_tasks: int


@dataclass
class TaskStatusCounts:
    """Counts of tasks by status"""
    todo: int
    in_progress: int
    done: int
    review: int = 0
    testing: int = 0
    blocked: int = 0
    on_hold: int = 0
