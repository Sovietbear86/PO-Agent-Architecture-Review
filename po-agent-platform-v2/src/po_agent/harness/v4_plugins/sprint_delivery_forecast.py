"""Additive sprint.delivery_forecast skill; frozen V4 Core is unchanged.

Only consumes the server-authorized, bounded, real-AS21 scalar projection.
Never treats a current-scope throughput estimate as committed Predictability.
"""
from __future__ import annotations

import re
from typing import Any

from ..agent_core_v4 import CapabilitySpecV4, SkillSpecV4, V4CapabilityUnavailable, V4NeedsClarification
from ..agent_core_v4_completion import CompletionRequirement
from ..contracts import CapabilityResult, Evidence
from ..v4_plugin_registry import CapabilityBindingV4, UIContractV4, V4SkillPlugin


def build_sprint_delivery_forecast(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        sprint_id = str(args.get("sprint_id") or "").strip().upper()
        if not sprint_id:
            raise V4NeedsClarification("Укажите идентификатор спринта, например DMS-SPRNT-5.")
        if not re.fullmatch(r"[A-Z][A-Z0-9_-]*-SPRNT-[0-9]+", sprint_id):
            raise V4NeedsClarification("Укажите корректный идентификатор спринта.")
        getter = getattr(runtime.adapter, "get_sprint_delivery_forecast", None)
        if getter is None:
            raise V4CapabilityUnavailable("Source-backed delivery forecast is unavailable")
        try:
            result = await getter(sprint_id)
        except Exception as exc:
            # Never leak source errors, credentials or AS21 payloads to UI.
            raise V4CapabilityUnavailable("Delivery forecast source is unavailable") from exc
        if not isinstance(result, dict) or result.get("sprint_id") != sprint_id:
            raise V4CapabilityUnavailable("Delivery forecast source identity mismatch")
        if result.get("status") != "READY" or result.get("source") != "REAL_AS21":
            reason = result.get("reason")
            if not isinstance(reason, str) or not re.fullmatch(r"[a-z0-9_]{3,80}", reason):
                reason = "source_evidence_insufficient"
            raise V4CapabilityUnavailable(f"Delivery forecast not available: {reason}")
        percentage = result.get("forecast_completion_percent")
        if isinstance(percentage, bool) or not isinstance(percentage, (int, float)) or not 0 <= percentage <= 100:
            raise V4CapabilityUnavailable("Delivery forecast numeric proof is incomplete")
        data = {
            key: result[key] for key in (
                "sprint_id", "status", "source", "method", "as_of",
                "sprint_start", "sprint_end", "scope_total", "closed_total",
                "open_count", "observed_tasks_per_workday", "remaining_workdays",
                "forecast_closed_by_end", "forecast_completion_percent",
                "forecast_scope_kind", "committed_predictability",
            ) if key in result
        }
        return CapabilityResult(
            answer=(
                f"Операционный прогноз по {sprint_id}: {percentage:g}% задач текущего "
                "состава к завершению спринта. Это оценка по фактическому throughput, "
                "не показатель выполнения первоначального обязательства."
            ),
            data=data,
            evidence=[Evidence(
                type="sprint_delivery_forecast", source="REAL_AS21",
                entity_id=sprint_id, label="Прогноз по текущему составу спринта",
                value={"forecast_completion_percent": percentage,
                       "scope_total": result.get("scope_total"),
                       "closed_total": result.get("closed_total")},
                freshness=result.get("as_of"),
            )],
            warnings=["forecast_current_scope_not_committed", "forecast_heuristic_no_probability_claim"],
        )

    return execute


CAPABILITIES = (
    CapabilitySpecV4(
        "sprint.delivery_forecast",
        "Operational sprint delivery forecast from authoritative complete AS21 task membership and terminal transition history; not committed predictability.",
        {"sprint_id": "required canonical sprint id e.g. DMS-SPRNT-5"},
    ),
)

SKILLS = (
    SkillSpecV4(
        "sprint.delivery_forecast",
        "Forecast current-scope sprint completion from source-verified throughput, or fail closed without verified source history.",
        (
            "Determine one canonical sprint identifier; never invent an identifier or silently scan all spaces.",
            "Call sprint.delivery_forecast with the canonical sprint_id.",
            "The result is a heuristic current-scope estimate, NOT committed Predictability or a delivery guarantee.",
            "If the source/policy is incomplete, report source unavailability without fabricating 0 or 100%.",
        ),
        ("sprint.delivery_forecast",),
        completion=(CompletionRequirement(
            "sprint.delivery_forecast",
            data_keys=("sprint_id", "status", "forecast_completion_percent", "source"),
        ),),
    ),
)

BINDINGS = (CapabilityBindingV4(
    "sprint.delivery_forecast", handler_builder=build_sprint_delivery_forecast,
),)

UI = {
    "sprint.delivery_forecast": UIContractV4(
        "analysis", preferred_widget="sprint_delivery_forecast",
        required_fields=("sprint_id", "status", "forecast_completion_percent", "source"),
    ),
}

PLUGIN = V4SkillPlugin(
    plugin_id="builtin.sprint.delivery_forecast",
    skills=SKILLS,
    capabilities=CAPABILITIES,
    bindings=BINDINGS,
    ui=UI,
)
