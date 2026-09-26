"""Batch 6: release forecast.

This is the final canonical V4 gap. Forecasting is deliberately conservative:
- release identity must be source-backed via release.search;
- release membership must be authoritative and non-empty;
- no task completion timestamp is inferred from updated_at;
- no forecast is produced without enough source-backed completion history;
- current sparse REAL AS21 release data therefore normally terminates
  SOURCE_CONDITIONAL rather than fabricating a delivery date.

The deterministic forecast is a simple observed task-throughput projection. It is
an operational estimate, not a commitment.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from ..agent_core_v4 import CapabilitySpecV4, SkillSpecV4, V4CapabilityUnavailable
from ..agent_core_v4_completion import CompletionRequirement
from ..contracts import CapabilityResult, Evidence
from ..v4_plugin_registry import CapabilityBindingV4, UIContractV4, V4SkillPlugin
from .wave_batch4 import _release_tasks


def _completion_timestamp(task: Any) -> datetime | None:
    """Use only authoritative completion timestamps; never updated_at as a proxy."""
    for value in (
        getattr(task, "closed_at", None),
        getattr(task, "resolved_at", None),
    ):
        if isinstance(value, datetime):
            return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    return None


def _created_timestamp(task: Any) -> datetime | None:
    value = getattr(task, "created_at", None)
    if not isinstance(value, datetime):
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def _evidence(tasks: list[Any]) -> list[Evidence]:
    return [
        Evidence(
            type="release_forecast_task",
            source="as21",
            entity_id=task.key,
            label=task.title,
            value={
                "completed": bool(task.is_completed),
                "created_at": getattr(task, "created_at", None).isoformat()
                if isinstance(getattr(task, "created_at", None), datetime)
                else None,
                "completion_timestamp": (
                    _completion_timestamp(task).isoformat()
                    if _completion_timestamp(task) is not None
                    else None
                ),
            },
        )
        for task in tasks
    ]


def build_release_forecast(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        space, release_id, tasks = await _release_tasks(runtime, args)

        completed = [task for task in tasks if task.is_completed]
        remaining = [task for task in tasks if not task.is_completed]

        completion_points = [
            (task, _completion_timestamp(task))
            for task in completed
        ]
        completion_points = [
            (task, timestamp)
            for task, timestamp in completion_points
            if timestamp is not None
        ]

        if not remaining:
            if not completion_points:
                raise V4CapabilityUnavailable(
                    "release.forecast cannot prove an actual completion date because "
                    "completed release tasks do not expose authoritative resolved/closed timestamps"
                )
            actual = max(timestamp for _, timestamp in completion_points)
            data = {
                "space": space,
                "release_id": release_id,
                "state": "COMPLETED",
                "total_tasks": len(tasks),
                "completed_tasks": len(completed),
                "remaining_tasks": 0,
                "forecast_date": actual.isoformat(),
                "forecast_kind": "actual_completion",
                "method": "authoritative_latest_completion_timestamp",
                "source": "REAL_AS21",
                "membership": "source_backed_release_task_query",
            }
            return CapabilityResult(
                answer=f"Релиз {release_id} завершён. Подтверждённая дата завершения: {actual.date().isoformat()}.",
                data=data,
                evidence=_evidence(tasks),
            )

        if len(completion_points) < 2:
            raise V4CapabilityUnavailable(
                "release.forecast requires at least two completed release tasks with authoritative "
                "resolved/closed timestamps; the current source history is insufficient"
            )

        created_points = [
            timestamp
            for task in tasks
            for timestamp in [_created_timestamp(task)]
            if timestamp is not None
        ]
        if not created_points:
            raise V4CapabilityUnavailable(
                "release.forecast requires authoritative task creation timestamps for the observation window"
            )

        observation_start = min(created_points)
        observation_end = max(timestamp for _, timestamp in completion_points)
        if observation_end <= observation_start:
            raise V4CapabilityUnavailable(
                "release.forecast source timestamps do not form a valid positive observation window"
            )

        observation_days = max(
            (observation_end - observation_start).total_seconds() / 86400.0,
            1.0,
        )
        throughput = len(completion_points) / observation_days
        if throughput <= 0:
            raise V4CapabilityUnavailable("release.forecast observed throughput is not positive")

        days_remaining = len(remaining) / throughput
        now = datetime.now(tz=observation_end.tzinfo or timezone.utc)
        forecast_date = now + timedelta(days=days_remaining)

        data = {
            "space": space,
            "release_id": release_id,
            "state": "FORECAST",
            "total_tasks": len(tasks),
            "completed_tasks": len(completed),
            "completed_tasks_with_authoritative_timestamp": len(completion_points),
            "remaining_tasks": len(remaining),
            "observation_start": observation_start.isoformat(),
            "observation_end": observation_end.isoformat(),
            "observation_days": round(observation_days, 3),
            "observed_throughput_tasks_per_day": round(throughput, 4),
            "forecast_days_remaining": round(days_remaining, 2),
            "forecast_date": forecast_date.isoformat(),
            "forecast_kind": "operational_projection",
            "method": "linear_task_throughput_v1",
            "source": "REAL_AS21",
            "membership": "source_backed_release_task_query",
            "completion_timestamp_policy": "closed_at_or_resolved_at_only",
        }
        return CapabilityResult(
            answer=(
                f"Операционный прогноз по {release_id}: около {data['forecast_days_remaining']:g} "
                f"календарных дней до завершения, ориентировочно {forecast_date.date().isoformat()}."
            ),
            data=data,
            evidence=_evidence(tasks),
            warnings=[
                "forecast_is_operational_projection_not_commitment",
                "forecast_uses_task_count_throughput_not_story_points_or_effort",
                "forecast_requires_stable_scope_assumption",
            ],
        )

    return execute


CAPABILITIES = (
    CapabilitySpecV4(
        "release.forecast",
        "Forecast release completion only from authoritative release membership and source-backed task completion timestamps. Never infer completion dates from updated_at and never fabricate a forecast when source history is insufficient.",
        {
            "space": "required canonical product space",
            "release_id": "required canonical source-backed release id",
        },
    ),
)

SKILLS = (
    SkillSpecV4(
        "release.forecast",
        "Forecast an identified release using a conservative source-backed task-throughput projection, or fail closed when release membership/history is insufficient.",
        (
            "Resolve product space and exactly one release through release.search(require_single=true).",
            "Call release.forecast with the canonical space and release_id.",
            "A release identity alone never satisfies this request.",
            "If authoritative release-to-task membership is missing, terminate SOURCE_CONDITIONAL; never treat empty membership as a zero-task release.",
            "If release membership exists but fewer than two completed tasks expose authoritative closed_at/resolved_at timestamps, terminate SOURCE_CONDITIONAL; never use updated_at as a completion proxy.",
            "If source history is sufficient, present the result explicitly as an operational task-count projection, not a delivery commitment.",
        ),
        ("space.resolve", "release.search", "release.forecast"),
        completion=(
            CompletionRequirement(
                "release.forecast",
                data_keys=("release_id", "state", "forecast_date", "method"),
            ),
        ),
    ),
)

BINDINGS = (
    CapabilityBindingV4("release.forecast", handler_builder=build_release_forecast),
)

UI = {
    "release.forecast": UIContractV4(
        "analysis",
        preferred_widget="release_forecast",
        required_fields=("release_id", "state", "forecast_date", "method"),
    ),
}

PLUGIN = V4SkillPlugin(
    plugin_id="builtin.batch6.release_forecast",
    skills=SKILLS,
    capabilities=CAPABILITIES,
    bindings=BINDINGS,
    ui=UI,
)
