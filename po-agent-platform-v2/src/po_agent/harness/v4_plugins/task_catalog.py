"""Canonical V4 task-skill wave (#1-20) beyond the A191 core plugin.

The user-facing task catalog stays declarative and plugin-owned. Source-specific
handlers are built at the plugin seam; Agent Core, planner strategy and runtime
trajectory orchestration remain unchanged.
"""
from __future__ import annotations

from ..agent_core_v4 import CapabilitySpecV4, SkillSpecV4
from ..agent_core_v4_completion import CompletionRequirement
from ..v4_plugin_registry import CapabilityBindingV4, UIContractV4, V4SkillPlugin
from ._task_live_handlers import (
    build_task_search_assignee,
    build_task_search_attachments,
    build_task_search_status,
    build_task_search_text,
    build_task_aging,
    build_task_similar,
)

CANONICAL_TASK_SKILL_IDS = (
    "task.search_text", "task.search_attachments", "task.search_excel", "task.search_pdf",
    "task.search_msg", "task.search_assignee", "task.search_status", "task.search_sprint",
    "task.search_release", "task.missing_requirements", "task.dependencies", "task.history",
    "task.time_in_status", "task.aging", "task.similar",
)

CAPABILITIES = (
    CapabilitySpecV4(
        "task.search_text",
        "Search REAL AS21 tasks by a user-supplied phrase in task key/title/description using the live source only.",
        {"phrase": "required user-supplied phrase", "space": "optional grounded product space", "reference": "optional natural person reference"},
    ),
    CapabilitySpecV4(
        "task.search_attachments",
        "Find REAL AS21 tasks with attachments using live task/file routes only.",
        {"task_key": "optional grounded task key", "space": "optional grounded product space", "reference": "optional natural person reference"},
    ),
    CapabilitySpecV4(
        "task.search_excel",
        "Find REAL AS21 tasks with Excel attachments; attachment_type=excel is fixed by the plugin binding.",
        {"task_key": "optional grounded task key", "space": "optional grounded product space", "reference": "optional natural person reference"},
    ),
    CapabilitySpecV4(
        "task.search_pdf",
        "Find REAL AS21 tasks with PDF attachments; attachment_type=pdf is fixed by the plugin binding.",
        {"task_key": "optional grounded task key", "space": "optional grounded product space", "reference": "optional natural person reference"},
    ),
    CapabilitySpecV4(
        "task.search_msg",
        "Find REAL AS21 tasks with MSG mail attachments; attachment_type=msg is fixed by the plugin binding.",
        {"task_key": "optional grounded task key", "space": "optional grounded product space", "reference": "optional natural person reference"},
    ),
    CapabilitySpecV4(
        "task.search_assignee",
        "Resolve a natural person reference against REAL AS21 and return that person's live tasks.",
        {"reference": "required user-grounded person reference", "space": "optional grounded product space", "status": "optional requested task status/open-completed semantic state"},
    ),
    CapabilitySpecV4(
        "task.search_status",
        "Return live REAL AS21 tasks for a requested semantic/open/completed status.",
        {"status": "required status or safe semantic state", "space": "optional grounded product space", "reference": "optional natural person reference", "assignee": "optional source-derived canonical assignee"},
    ),
    CapabilitySpecV4("task.search_release", "Return the complete REAL AS21 task collection for a canonical release id.", {"release_id": "required canonical release id"}),
    CapabilitySpecV4("task.missing_requirements", "Deterministically identify missing/weak task-definition elements from source task content.", {"task_key": "required task key"}),
    CapabilitySpecV4("task.dependencies", "Inspect source-backed task dependency/link relationships.", {"task_key": "required task key"}),
    CapabilitySpecV4("task.history", "Read source-backed lifecycle/status history for one task when the authoritative history endpoint is available; otherwise fail SOURCE_CONDITIONAL.", {"task_key": "required task key"}),
    CapabilitySpecV4("task.time_in_status", "Calculate deterministic time intervals spent in task statuses only from authoritative source history; availability depends on the history endpoint.", {"task_key": "required task key"}),
    CapabilitySpecV4("task.aging", "Find active tasks at or above a deterministic age threshold inside a bounded live source scope.", {"threshold_days": "optional integer threshold", "space": "required/strongly preferred grounded product space", "reference": "optional grounded person reference"}),
    CapabilitySpecV4("task.similar", "Find bounded similar/duplicate task candidates from the source-backed task corpus.", {"task_key": "required task key"}),
)

SKILLS = (
    SkillSpecV4(
        "task.search_text", "Search tasks by a phrase or fragment supplied by the user.",
        ("Call task.search_text with the literal phrase from the request and any grounded space/person constraints; never use a local task store.", "Return exact source-backed keys/count."),
        ("task.search_text",), completion=(CompletionRequirement("task.search_text", data_keys=("count",)),),
    ),
    SkillSpecV4(
        "task.search_attachments", "Find tasks that contain any attachments, including a single explicitly named task.",
        ("Call task.search_attachments with any grounded task_key, space and/or person reference from the request. The capability owns live source resolution; never infer empty from a local corpus.",),
        ("task.search_attachments",), completion=(CompletionRequirement("task.search_attachments", data_keys=("count",)),),
    ),
    SkillSpecV4(
        "task.search_excel", "Find tasks that contain Excel attachments.",
        ("Call task.search_excel with grounded task/space/person constraints when present; attachment_type=excel is fixed by the plugin contract.",),
        ("task.search_excel",), completion=(CompletionRequirement("task.search_excel", data_keys=("count", "attachment_type")),),
    ),
    SkillSpecV4(
        "task.search_pdf", "Find tasks that contain PDF attachments.",
        ("Call task.search_pdf with grounded task/space/person constraints when present; attachment_type=pdf is fixed by the plugin contract.",),
        ("task.search_pdf",), completion=(CompletionRequirement("task.search_pdf", data_keys=("count", "attachment_type")),),
    ),
    SkillSpecV4(
        "task.search_msg", "Find tasks that contain MSG mail attachments.",
        ("Call task.search_msg with grounded task/space/person constraints when present; attachment_type=msg is fixed by the plugin contract.",),
        ("task.search_msg",), completion=(CompletionRequirement("task.search_msg", data_keys=("count", "attachment_type")),),
    ),
    SkillSpecV4(
        "task.search_assignee", "Find tasks assigned to a named person/source identity.",
        ("Call task.search_assignee with the natural person reference exactly as grounded in the user request and optional grounded space. If the user also requested a task status/open-completed state, pass it in the status argument; never drop that constraint. Identity resolution is source-backed inside the capability; never invent a login.",),
        ("task.search_assignee",), completion=(CompletionRequirement("task.search_assignee", data_keys=("count",)),),
    ),
    SkillSpecV4(
        "task.search_status", "Find tasks by a requested task status/open-completed semantic state.",
        ("Call task.search_status with the requested status and any grounded space/person constraint. Natural person references are resolved source-backed inside the capability. Safe semantic enums such as not_completed may be normalized by the planner.",),
        ("task.search_status",), completion=(CompletionRequirement("task.search_status", data_keys=("count",)),),
    ),
    SkillSpecV4(
        "task.search_sprint", "Find all tasks in a specific sprint.",
        ("Resolve/validate the sprint with sprint.resolve when an explicit sprint id is supplied.", "Call task.search with sprint_id bound to the canonical sprint observation."),
        ("sprint.resolve", "task.search"), completion=(CompletionRequirement("task.search", data_keys=("count",), covers_resolved_constraints=True),),
    ),
    SkillSpecV4(
        "task.search_release", "Find all tasks in a specific release/fix version.",
        ("Resolve/validate the release with release.resolve.", "Call task.search_release with the canonical release_id from that observation."),
        ("release.resolve", "task.search_release"), completion=(CompletionRequirement("task.search_release", data_keys=("count",), covers_resolved_constraints=True),),
    ),
    SkillSpecV4("task.missing_requirements", "Identify missing or weak requirement elements in one task definition.", ("Call task.missing_requirements with the literal task key.",), ("task.missing_requirements",), completion=(CompletionRequirement("task.missing_requirements", data_keys=("task_key",), data_absent_keys=("found",)),)),
    SkillSpecV4("task.dependencies", "Inspect dependencies/links of one task and whether dependencies are unresolved.", ("Call task.dependencies with the literal task key.",), ("task.dependencies",), completion=(CompletionRequirement("task.dependencies", data_keys=("task_key",), data_absent_keys=("found",)),)),
    SkillSpecV4("task.history", "Show lifecycle/status history of one task when the authoritative source exposes history; defined capability does not imply the live history endpoint is currently available.", ("Call task.history with the literal task key; if source history is unavailable, fail closed rather than invent a timeline or claiming an empty history.",), ("task.history",), completion=(CompletionRequirement("task.history", data_keys=("task_key",), data_absent_keys=("found",)),)),
    SkillSpecV4("task.time_in_status", "Calculate time spent in task statuses from authoritative history when that source is available.", ("Call task.time_in_status with the literal task key; never infer durations without source timestamps. If history is unavailable, fail closed/source-conditional.",), ("task.time_in_status",), completion=(CompletionRequirement("task.time_in_status", data_keys=("task_key",), data_absent_keys=("found",)),)),
    SkillSpecV4("task.aging", "Find aging active tasks using a deterministic day threshold.", ("Call task.aging with a grounded space or natural person scope; the capability resolves person identity against REAL AS21. Pass threshold_days only when supplied by the user. Never request an unscoped tenant scan.",), ("task.aging",), completion=(CompletionRequirement("task.aging", data_keys=("count", "threshold_days")),)),
    SkillSpecV4("task.similar", "Find bounded similar/duplicate candidates for one task.", ("Call task.similar with the literal task key and keep the declared deterministic similarity method visible.",), ("task.similar",), completion=(CompletionRequirement("task.similar", data_keys=("task_key", "method"), data_absent_keys=("found",)),)),
)

BINDINGS = (
    CapabilityBindingV4("task.search_text", handler_builder=build_task_search_text),
    CapabilityBindingV4("task.search_attachments", handler_builder=build_task_search_attachments),
    CapabilityBindingV4("task.search_excel", handler_builder=build_task_search_attachments, fixed_arguments={"attachment_type": "excel"}),
    CapabilityBindingV4("task.search_pdf", handler_builder=build_task_search_attachments, fixed_arguments={"attachment_type": "pdf"}),
    CapabilityBindingV4("task.search_msg", handler_builder=build_task_search_attachments, fixed_arguments={"attachment_type": "msg"}),
    CapabilityBindingV4("task.search_assignee", handler_builder=build_task_search_assignee),
    CapabilityBindingV4("task.search_status", handler_builder=build_task_search_status),
    CapabilityBindingV4("task.search_release", legacy_capability_id="task.search_release"),
    CapabilityBindingV4("task.missing_requirements", legacy_capability_id="task.missing_requirements"),
    CapabilityBindingV4("task.dependencies", legacy_capability_id="task.dependencies"),
    CapabilityBindingV4("task.history", legacy_capability_id="task.history"),
    CapabilityBindingV4("task.time_in_status", legacy_capability_id="task.time_in_status"),
    CapabilityBindingV4("task.aging", handler_builder=build_task_aging),
    CapabilityBindingV4("task.similar", handler_builder=build_task_similar),
)

UI = {
    "task.search_text": UIContractV4("task_collection", preferred_widget="task_table", required_fields=("count", "tasks")),
    "task.search_attachments": UIContractV4("attachment_collection", preferred_widget="attachment_table", required_fields=("count", "results")),
    "task.search_excel": UIContractV4("attachment_collection", preferred_widget="attachment_table", required_fields=("count", "results", "attachment_type")),
    "task.search_pdf": UIContractV4("attachment_collection", preferred_widget="attachment_table", required_fields=("count", "results", "attachment_type")),
    "task.search_msg": UIContractV4("attachment_collection", preferred_widget="attachment_table", required_fields=("count", "results", "attachment_type")),
    "task.search_assignee": UIContractV4("task_collection", preferred_widget="task_table", required_fields=("count", "tasks")),
    "task.search_status": UIContractV4("task_collection", preferred_widget="task_table", required_fields=("count", "tasks")),
    "task.search_sprint": UIContractV4("task_collection", preferred_widget="task_table", required_fields=("count", "tasks")),
    "task.search_release": UIContractV4("task_collection", preferred_widget="task_table", required_fields=("count", "tasks")),
    "task.missing_requirements": UIContractV4("analysis", preferred_widget="task_analysis", required_fields=("task_key", "missing_elements")),
    "task.dependencies": UIContractV4("analysis", preferred_widget="task_dependencies", required_fields=("task_key", "dependencies")),
    "task.history": UIContractV4("timeline", preferred_widget="task_history", required_fields=("task_key", "timeline")),
    "task.time_in_status": UIContractV4("timeline", preferred_widget="task_status_timeline", required_fields=("task_key", "durations")),
    "task.aging": UIContractV4("task_collection", preferred_widget="task_table", required_fields=("count", "tasks", "threshold_days")),
    "task.similar": UIContractV4("similar_task_collection", preferred_widget="similar_task_list", required_fields=("task_key", "matches", "method")),
}

PLUGIN = V4SkillPlugin(plugin_id="builtin.catalog.tasks", skills=SKILLS, capabilities=CAPABILITIES, bindings=BINDINGS, ui=UI)
