"""A188-certified V4 catalog expressed as a declarative built-in plugin.

Business behavior intentionally mirrors the pre-plugin runtime. Source handlers
are attached through the plugin registry so task/source evolution does not require
editing Agent Core or planner/runtime orchestration.
"""
from __future__ import annotations

from ..agent_core_v4 import CapabilitySpecV4, SkillSpecV4
from ..agent_core_v4_completion import CompletionRequirement
from ..v4_plugin_registry import CapabilityBindingV4, UIContractV4, V4SkillPlugin
from ._task_live_handlers import build_task_lookup

CAPABILITIES = (
    CapabilitySpecV4("member.resolve", "Resolve a human reference against REAL AS21, optionally inside a source-backed sprint/space context when global identity search is ambiguous.", {"reference": "required raw human reference", "sprint_id": "optional sprint id or prior sprint.resolve observation", "space": "optional approved product space"}),
    CapabilitySpecV4("space.resolve", "Validate an approved product space.", {"reference": "required space text"}),
    CapabilitySpecV4("sprint.resolve", "Validate a sprint id against REAL AS21 and return canonical id/space.", {"reference": "required sprint id", "space": "optional canonical space"}),
    CapabilitySpecV4("sprint.search", "Resolve a human period reference (month/year/period) to source-backed sprint(s) in a space; typed ambiguity if several match.", {"space": "required approved space", "period": "required human period reference, e.g. a month name or YYYY-MM"}),
    CapabilitySpecV4("sprint.list", "List source-backed sprints in a space (optionally only active ones) as a complete collection.", {"space": "required approved space", "active_only": "optional 'true' to keep only non-closed sprints"}),
    CapabilitySpecV4("release.resolve", "Validate a release/version id against REAL AS21 tasks.", {"reference": "required release id", "space": "optional canonical space"}),
    CapabilitySpecV4("task.search", "Search REAL AS21 tasks by any resolved assignee/space/sprint/status combination.", {"assignee": "optional canonical login from member.resolve", "space": "optional approved space", "sprint_id": "optional canonical sprint", "status": "optional status; not_completed is supported"}),
    CapabilitySpecV4("task.lookup", "Read one REAL AS21 task by key, including live attachment metadata and canonical assignee identity.", {"task_key": "required task key"}),
    CapabilitySpecV4("task.summary", "Summarize one REAL AS21 task.", {"task_key": "required task key"}),
    CapabilitySpecV4("task.quality", "Analyze one task's formulation quality.", {"task_key": "required task key"}),
    CapabilitySpecV4("task.acceptance", "Analyze acceptance criteria/testability for one task.", {"task_key": "required task key"}),
    CapabilitySpecV4("task.blockers", "Analyze blockers/dependencies for one task.", {"task_key": "required task key"}),
    CapabilitySpecV4("sprint.health", "Calculate current sprint health from REAL AS21 sprint tasks.", {"sprint_id": "required canonical sprint id"}),
    CapabilitySpecV4("sprint.current", "Read the current sprint for a product space.", {"product": "required approved space"}),
    CapabilitySpecV4("release.health", "Calculate release progress from REAL AS21 release tasks.", {"release_id": "required release id"}),
)

SKILLS = (
    SkillSpecV4(
        "tasks.search",
        "Compose task search when the request has multiple filters, a current/period sprint, or another multi-step constraint combination. For a single canonical assignee/status/explicit-sprint filter prefer the dedicated task catalog skill when available.",
        (
            "Use this composition helper when several constraints or current/period sprint resolution must be combined; prefer a dedicated canonical single-filter skill when it directly matches the whole request.",
            "Resolve only the entities needed by the user's filters.",
            "For a human reference call member.resolve.",
            "For a sprint given by id call sprint.resolve; for a sprint given by a month/period call sprint.search.",
            "For 'current sprint' call sprint.current to obtain the canonical sprint id before searching.",
            "Call task.search with every resolved user constraint and validate the returned collection.",
        ),
        ("member.resolve", "space.resolve", "sprint.resolve", "sprint.search", "sprint.current", "task.search"),
        completion=(CompletionRequirement("task.search", data_keys=("count",), covers_resolved_constraints=True),),
    ),
    SkillSpecV4(
        "sprints.discover",
        "Find a sprint by a human month/period reference in a product space.",
        (
            "Validate the product space, then call sprint.search with the space and the period reference.",
            "If sprint.search returns typed ambiguity, surface the options instead of guessing.",
        ),
        ("space.resolve", "sprint.search"),
        completion=(CompletionRequirement("sprint.search", data_keys=("sprint_id",)),),
    ),
    SkillSpecV4(
        "sprints.list",
        "List the sprints (or the active sprints) of a product space as a complete collection.",
        (
            "Validate the product space, then call sprint.list for the full source-backed collection.",
            "Do not answer a request for several/active sprints with sprint.current, which returns only one sprint.",
        ),
        ("space.resolve", "sprint.list"),
        completion=(CompletionRequirement("sprint.list", data_keys=("sprints",)),),
    ),
    SkillSpecV4(
        "tasks.lookup_then_assignee",
        "Read a task and then inspect tasks of its assignee.",
        (
            "Call task.lookup for the user-supplied task key.",
            "Use the authoritative assignee from the observation, never infer a person from prose.",
            "Call task.search for that assignee and preserve any additional user filters.",
        ),
        ("task.lookup", "task.search"),
        completion=(
            CompletionRequirement("task.lookup", data_keys=("task", "assignee_login")),
            CompletionRequirement(
                "task.search",
                data_keys=("count",),
                bound_argument=("assignee", "task.lookup", ("assignee_login", "task.assignee_login", "assignee_id", "task.assignee_id")),
                covers_resolved_constraints=True,
            ),
        ),
    ),
    SkillSpecV4("task.lookup", "Read one task by key.", ("Call task.lookup with the literal task key.",), ("task.lookup",), completion=(CompletionRequirement("task.lookup", data_keys=("task",)),)),
    SkillSpecV4("task.summary", "Explain/summarize one task.", ("Call task.summary with the literal task key.",), ("task.summary",), completion=(CompletionRequirement("task.summary", data_keys=("task_key",), data_absent_keys=("found",)),)),
    SkillSpecV4("task.quality", "Assess task statement quality/completeness.", ("Call task.quality with the literal task key.",), ("task.quality",), completion=(CompletionRequirement("task.quality", data_keys=("task_key",), data_absent_keys=("found",)),)),
    SkillSpecV4("task.acceptance", "Assess acceptance criteria/testability of a task.", ("Call task.acceptance with the literal task key.",), ("task.acceptance",), completion=(CompletionRequirement("task.acceptance", data_keys=("task_key",), data_absent_keys=("found",)),)),
    SkillSpecV4("task.blockers", "Inspect blockers/dependencies of a task.", ("Call task.blockers with the literal task key.",), ("task.blockers",), completion=(CompletionRequirement("task.blockers", data_keys=("task_key",), data_absent_keys=("found",)),)),
    SkillSpecV4("sprint.health", "Show health/progress of a sprint.", ("Resolve/validate the sprint if needed, then call sprint.health.",), ("sprint.resolve", "sprint.health"), completion=(CompletionRequirement("sprint.health", data_keys=("sprint_id", "total")),)),
    SkillSpecV4("sprint.current", "Report which sprint is currently active in a product space (identity only; use tasks.search to list tasks within it).", ("Validate the product space, then call sprint.current.",), ("space.resolve", "sprint.current"), completion=()),
    SkillSpecV4("release.health", "Show release health/progress.", ("Validate the release if useful, then call release.health.",), ("release.resolve", "release.health"), completion=(CompletionRequirement("release.health", data_keys=("release_id", "total")),)),
)

BINDINGS = (
    CapabilityBindingV4("member.resolve", handler_method="_member_resolve"),
    CapabilityBindingV4("space.resolve", handler_method="_space_resolve"),
    CapabilityBindingV4("sprint.resolve", handler_method="_sprint_resolve"),
    CapabilityBindingV4("sprint.search", handler_method="_sprint_search"),
    CapabilityBindingV4("sprint.list", handler_method="_sprint_list"),
    CapabilityBindingV4("release.resolve", handler_method="_release_resolve"),
    CapabilityBindingV4("task.search", handler_method="_task_search"),
    CapabilityBindingV4("task.lookup", handler_builder=build_task_lookup),
    CapabilityBindingV4("task.summary", legacy_capability_id="task.summary"),
    CapabilityBindingV4("task.quality", legacy_capability_id="task.quality"),
    CapabilityBindingV4("task.acceptance", legacy_capability_id="task.acceptance_analysis"),
    CapabilityBindingV4("task.blockers", legacy_capability_id="task.blockers"),
    CapabilityBindingV4("sprint.health", legacy_capability_id="sprint.health"),
    CapabilityBindingV4("sprint.current", handler_method="_sprint_current_source_backed"),
    CapabilityBindingV4("release.health", legacy_capability_id="release.health"),
)

UI = {
    "tasks.search": UIContractV4("task_collection", preferred_widget="task_table", required_fields=("count", "tasks")),
    "tasks.lookup_then_assignee": UIContractV4("task_collection", preferred_widget="task_table", required_fields=("count", "tasks")),
    "sprints.list": UIContractV4("sprint_collection", preferred_widget="sprint_list", required_fields=("sprints",)),
    "sprints.discover": UIContractV4("sprint", preferred_widget="sprint_summary", required_fields=("sprint_id",)),
    "task.lookup": UIContractV4("task", preferred_widget="task_detail", required_fields=("task",)),
    "task.quality": UIContractV4("analysis", preferred_widget="task_analysis", required_fields=("task_key", "score")),
    "sprint.current": UIContractV4("sprint", preferred_widget="sprint_summary"),
    "sprint.health": UIContractV4("analysis", preferred_widget="sprint_health"),
    "release.health": UIContractV4("analysis", preferred_widget="release_health"),
}

PLUGIN = V4SkillPlugin(plugin_id="builtin.core.a188", skills=SKILLS, capabilities=CAPABILITIES, bindings=BINDINGS, ui=UI)
