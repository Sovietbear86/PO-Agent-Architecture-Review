"""Canonical PO Agent Skill Catalog.

`PO_AGENT_PLATFORM_V2_GIGACODE_MASTER_SPEC_V2_1.md` is the product acceptance
baseline. `implemented` means executable versioned Skill + allow-listed handler
+ source evidence + typed result + acceptance coverage.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

SkillStatus = Literal["implemented", "planned", "blocked"]

@dataclass(frozen=True)
class SkillCatalogEntry:
    id: str
    domain: str
    capability_id: str
    description: str
    status: SkillStatus = "planned"
    requires_llm: bool = False
    requires_history: bool = False
    requires_write: bool = False

SKILL_CATALOG: tuple[SkillCatalogEntry, ...] = (
    SkillCatalogEntry("task-lookup", "tasks", "task.lookup", "Find an exact task by key.", "implemented"),
    SkillCatalogEntry("task-search", "tasks", "task.search", "Search tasks by phrase/text.", "implemented"),
    SkillCatalogEntry("task-search-attachments", "tasks", "task.search_attachments", "Find tasks containing attachments.", "implemented"),
    SkillCatalogEntry("task-search-excel", "tasks", "task.search_attachment_excel", "Find tasks with XLS/XLSX attachments.", "implemented"),
    SkillCatalogEntry("task-search-pdf", "tasks", "task.search_attachment_pdf", "Find tasks with PDF attachments.", "implemented"),
    SkillCatalogEntry("task-search-msg", "tasks", "task.search_attachment_msg", "Find tasks with MSG attachments.", "implemented"),
    SkillCatalogEntry("task-search-assignee", "tasks", "task.search_assignee", "Find tasks assigned to a team member.", "implemented"),
    SkillCatalogEntry("task-search-status", "tasks", "task.search_status", "Find tasks by normalized workflow status.", "implemented"),
    SkillCatalogEntry("task-search-sprint", "tasks", "task.search_sprint", "Find tasks in a sprint.", "implemented"),
    SkillCatalogEntry("task-search-release", "tasks", "task.search_release", "Find tasks linked to a release.", "implemented"),
    SkillCatalogEntry("task-search-product", "tasks", "task.search_product", "Find tasks in a configured product/space.", "implemented"),
    SkillCatalogEntry("task-summary", "tasks", "task.summary", "Summarize what must be done in a task.", "implemented", requires_llm=True),
    SkillCatalogEntry("task-quality", "tasks", "task.quality", "Evaluate task statement quality deterministically.", "implemented"),
    SkillCatalogEntry("task-missing-requirements", "tasks", "task.missing_requirements", "Identify missing task-definition elements.", "implemented"),
    SkillCatalogEntry("task-acceptance-analysis", "tasks", "task.acceptance_analysis", "Analyze acceptance criteria and testability.", "implemented", requires_llm=True),
    SkillCatalogEntry("task-dependency-analysis", "tasks", "task.dependencies", "Analyze task links and dependencies.", "implemented"),
    SkillCatalogEntry("task-history", "tasks", "task.history", "Explain task lifecycle and status transitions.", "implemented", requires_history=True),
    SkillCatalogEntry("task-time-in-status", "tasks", "task.time_in_status", "Calculate time spent in workflow states.", "implemented", requires_history=True),
    SkillCatalogEntry("task-aging", "tasks", "task.aging", "Identify aging active tasks.", "implemented"),
    SkillCatalogEntry("task-blocker-analysis", "tasks", "task.blockers", "Explain blockers and blocked-task evidence.", "implemented", requires_llm=True),
    SkillCatalogEntry("task-similar", "tasks", "task.similar", "Find similar/duplicate tasks.", "implemented", requires_llm=True),
    SkillCatalogEntry("sprint-health", "sprints", "sprint.health", "Summarize deterministic sprint health.", "implemented"),
    SkillCatalogEntry("sprint-current", "sprints", "sprint.current", "Resolve current sprint for a product.", "implemented"),
    SkillCatalogEntry("sprint-scope", "sprints", "sprint.scope", "Show current sprint scope.", "implemented"),
    SkillCatalogEntry("sprint-velocity", "sprints", "sprint.velocity", "Calculate velocity using explicit effort units.", "implemented"),
    SkillCatalogEntry("sprint-throughput", "sprints", "sprint.throughput", "Calculate completed-task throughput.", "implemented"),
    SkillCatalogEntry("sprint-wip", "sprints", "sprint.wip", "Calculate work in progress.", "implemented"),
    SkillCatalogEntry("sprint-cycle-time", "sprints", "sprint.cycle_time", "Calculate cycle-time metrics.", "implemented", requires_history=True),
    SkillCatalogEntry("sprint-lead-time", "sprints", "sprint.lead_time", "Calculate lead-time metrics.", "implemented", requires_history=True),
    SkillCatalogEntry("sprint-carryover", "sprints", "sprint.carryover", "Measure carryover from committed scope.", requires_history=True),
    SkillCatalogEntry("sprint-scope-change", "sprints", "sprint.scope_change", "Measure scope change after sprint start.", requires_history=True),
    SkillCatalogEntry("sprint-predictability", "sprints", "sprint.predictability", "Calculate sprint predictability.", "implemented"),
    SkillCatalogEntry("sprint-risk-queue", "sprints", "sprint.risk_queue", "Identify sprint tasks requiring PO attention.", "implemented"),
    SkillCatalogEntry("team-workload", "team", "team.workload", "Analyze workload distribution.", "implemented"),
    SkillCatalogEntry("team-wip", "team", "team.wip", "Show WIP by team member.", "implemented"),
    SkillCatalogEntry("team-blocked", "team", "team.blocked", "Show blocked work by team member.", "implemented"),
    SkillCatalogEntry("team-capacity", "team", "team.capacity", "Compare workload with configured capacity.", "implemented"),
    SkillCatalogEntry("team-competency-match", "team", "team.competency_match", "Match task requirements to declared competencies.", requires_llm=True),
    SkillCatalogEntry("team-assignee-recommendation", "team", "team.assignee_recommendation", "Recommend assignee using competencies and load.", requires_llm=True),
    SkillCatalogEntry("team-bottlenecks", "team", "team.bottlenecks", "Detect concentration/bottleneck patterns.", "implemented"),
    SkillCatalogEntry("team-distribution", "team", "team.distribution", "Explain task distribution across competencies.", "implemented"),
    SkillCatalogEntry("release-health", "releases", "release.health", "Summarize release readiness and risks.", "implemented"),
    SkillCatalogEntry("release-scope", "releases", "release.scope", "Show release task scope.", "implemented"),
    SkillCatalogEntry("release-progress", "releases", "release.progress", "Calculate release completion.", "implemented"),
    SkillCatalogEntry("release-blockers", "releases", "release.blockers", "Identify release blockers.", "implemented"),
    SkillCatalogEntry("release-dependencies", "releases", "release.dependencies", "Analyze release dependencies.", "implemented"),
    SkillCatalogEntry("release-risk-queue", "releases", "release.risk_queue", "Prioritize release risks for PO attention.", "implemented"),
    SkillCatalogEntry("release-forecast", "releases", "release.forecast", "Provide deterministic forecast inputs and bounded forecast output."),
    SkillCatalogEntry("portfolio-overview", "portfolio", "portfolio.overview", "Provide portfolio overview and attention queue.", "implemented"),
    SkillCatalogEntry("po-attention-queue", "po", "po.attention_queue", "Rank items requiring PO intervention."),
    SkillCatalogEntry("po-daily-brief", "po", "po.daily_brief", "Generate a grounded daily PO brief.", requires_llm=True),
    SkillCatalogEntry("po-status-report", "po", "po.status_report", "Generate product/sprint/release status report.", requires_llm=True),
    SkillCatalogEntry("po-reminder-draft", "po", "po.reminder_draft", "Draft a contextual reminder/action message.", requires_llm=True),
    SkillCatalogEntry("po-local-task-draft", "po", "po.local_task_draft", "Prepare a local task draft; external write requires explicit approval.", requires_llm=True),
)

def catalog_by_id() -> dict[str, SkillCatalogEntry]: return {entry.id: entry for entry in SKILL_CATALOG}

def catalog_summary() -> dict[str, object]:
    by_domain: dict[str, int] = {}
    statuses: dict[str, int] = {"implemented": 0, "planned": 0, "blocked": 0}
    for entry in SKILL_CATALOG:
        by_domain[entry.domain] = by_domain.get(entry.domain, 0) + 1
        statuses[entry.status] += 1
    return {"total": len(SKILL_CATALOG), "by_domain": by_domain, "statuses": statuses}
