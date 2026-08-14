"""Source-gated sprint scope history and bounded release forecast capabilities."""
from __future__ import annotations

from datetime import timedelta

from po_agent.adapters.as21 import AS21Adapter

from .contracts import CapabilityResult, Evidence
from .source_contracts import ReleaseTimelineSource, SprintSnapshotSource


class SprintHistoricalCapabilities:
    def __init__(self, adapter: AS21Adapter, snapshots: SprintSnapshotSource) -> None:
        self.a = adapter
        self.snapshots = snapshots

    async def _facts(self, sprint_id: str):
        snapshot = await self.snapshots.get_commitment_snapshot(sprint_id)
        if snapshot is None:
            return None, []
        current = await self.a.get_sprint_tasks(sprint_id)
        return snapshot, current

    async def carryover(self, args: dict[str, str]) -> CapabilityResult:
        sprint_id = args["sprint_id"].upper()
        snapshot, current = await self._facts(sprint_id)
        if snapshot is None:
            return CapabilityResult(
                answer=f"Для {sprint_id} нет commitment snapshot; carryover нельзя посчитать.",
                data={"sprint_id": sprint_id, "available": False},
                warnings=["commitment_snapshot_missing"],
            )
        current_by_key = {t.key: t for t in current}
        committed = set(snapshot.task_keys)
        unresolved = sorted(key for key in committed if key in current_by_key and not current_by_key[key].is_completed)
        disappeared = sorted(key for key in committed if key not in current_by_key)
        evidence = [Evidence(type="sprint_commitment", source="sprint_snapshots", entity_id=sprint_id, label="captured_at", value=snapshot.captured_at.isoformat())]
        evidence.extend(Evidence(type="sprint_task", source="as21", entity_id=t.key, label=t.title, value=t.status.value) for t in current if t.key in committed)
        warnings = ["committed_tasks_missing_from_current_scope"] if disappeared else []
        return CapabilityResult(
            answer=f"{sprint_id}: carryover-кандидатов {len(unresolved)} из {len(committed)} committed задач.",
            data={
                "sprint_id": sprint_id,
                "committed": len(committed),
                "carryover_count": len(unresolved),
                "carryover_task_keys": unresolved,
                "missing_from_current_scope": disappeared,
                "snapshot_captured_at": snapshot.captured_at.isoformat(),
                "method": "committed_scope_not_completed_in_current_state",
            },
            evidence=evidence,
            warnings=warnings,
        )

    async def scope_change(self, args: dict[str, str]) -> CapabilityResult:
        sprint_id = args["sprint_id"].upper()
        snapshot, current = await self._facts(sprint_id)
        if snapshot is None:
            return CapabilityResult(
                answer=f"Для {sprint_id} нет commitment snapshot; изменение scope нельзя посчитать.",
                data={"sprint_id": sprint_id, "available": False},
                warnings=["commitment_snapshot_missing"],
            )
        committed = set(snapshot.task_keys)
        current_keys = {t.key for t in current}
        added = sorted(current_keys - committed)
        removed = sorted(committed - current_keys)
        base = len(committed)
        change_percent = round((len(added) + len(removed)) / base * 100, 1) if base else 0.0
        evidence = [Evidence(type="sprint_commitment", source="sprint_snapshots", entity_id=sprint_id, label="captured_at", value=snapshot.captured_at.isoformat())]
        evidence.extend(Evidence(type="sprint_task", source="as21", entity_id=t.key, label=t.title, value=t.status.value) for t in current)
        return CapabilityResult(
            answer=f"{sprint_id}: после commitment добавлено {len(added)}, удалено {len(removed)} задач; scope change {change_percent}%.",
            data={
                "sprint_id": sprint_id,
                "committed": base,
                "current": len(current_keys),
                "added": added,
                "removed": removed,
                "scope_change_percent": change_percent,
                "snapshot_captured_at": snapshot.captured_at.isoformat(),
                "method": "set_difference_vs_commitment_snapshot",
            },
            evidence=evidence,
        )


class ReleaseForecastCapabilities:
    def __init__(self, adapter: AS21Adapter, timeline: ReleaseTimelineSource) -> None:
        self.a = adapter
        self.timeline = timeline

    async def forecast(self, args: dict[str, str]) -> CapabilityResult:
        release_id = args["release_id"].upper()
        points = tuple(sorted(await self.timeline.get_timeline(release_id), key=lambda p: p.captured_at))
        current = await self.a.get_release_tasks(release_id)
        current_done = sum(t.is_completed for t in current)
        current_total = len(current)
        evidence = [Evidence(type="release_task", source="as21", entity_id=t.key, label=t.title, value=t.status.value) for t in current]
        evidence.extend(Evidence(type="release_timeline", source="release_timeline", entity_id=release_id, label=p.captured_at.isoformat(), value=f"{p.completed}/{p.total}") for p in points)
        if len(points) < 2:
            return CapabilityResult(
                answer=f"Для {release_id} недостаточно временных точек для прогноза.",
                data={"release_id": release_id, "forecast_date": None, "timeline_points": len(points), "current_completed": current_done, "current_total": current_total},
                evidence=evidence,
                warnings=["insufficient_release_timeline"],
            )
        first, last = points[0], points[-1]
        elapsed_days = (last.captured_at - first.captured_at).total_seconds() / 86400
        delta_completed = last.completed - first.completed
        if elapsed_days <= 0 or delta_completed <= 0:
            return CapabilityResult(
                answer=f"Для {release_id} нет положительной наблюдаемой скорости завершения; прогноз не строится.",
                data={"release_id": release_id, "forecast_date": None, "timeline_points": len(points), "elapsed_days": round(elapsed_days, 3), "completed_delta": delta_completed},
                evidence=evidence,
                warnings=["non_positive_completion_rate"],
            )
        rate = delta_completed / elapsed_days
        remaining = max(current_total - current_done, 0)
        days_remaining = remaining / rate if rate else None
        forecast_date = (last.captured_at + timedelta(days=days_remaining)).date().isoformat() if days_remaining is not None else None
        return CapabilityResult(
            answer=f"{release_id}: наблюдаемая скорость {rate:.2f} задач/день; bounded forecast — {forecast_date}.",
            data={
                "release_id": release_id,
                "forecast_date": forecast_date,
                "observed_rate_tasks_per_day": round(rate, 3),
                "remaining_tasks": remaining,
                "timeline_points": len(points),
                "baseline_from": first.captured_at.isoformat(),
                "baseline_to": last.captured_at.isoformat(),
                "method": "linear_observed_completion_rate",
                "bounded": True,
            },
            evidence=evidence,
            warnings=["forecast_is_linear_observed_rate_not_commitment"],
        )
