"""Optional deterministic final rendering for simple V4 task trajectories.

This module removes exactly one post-execution LLM synthesis turn for a narrow,
source-grounded subset. Planning, capability execution, completion, evidence and
clarification semantics stay unchanged. Non-eligible trajectories delegate to
the original LLM synthesizer.
"""
from __future__ import annotations

import re
from typing import Any

from .agent_core_v4 import V4Observation


_ELIGIBLE_TERMINALS = frozenset({
    "task.search",
    "task.search_assignee",
    "task.search_created",
    "task.search_created_in_progress",
    "task.search_status",
    "task.search_sprint",
    "task.search_text",
    "task.search_attachments",
    "task.search_excel",
    "task.search_pdf",
    "task.search_msg",
    "task.type_analysis",
    "task.lookup",
    "task.hierarchy",
})

_INTERMEDIATE_CAPABILITIES = frozenset({
    "sprint.search",
    "sprint.current",
    "sprint.list",
    "release.search",
})


class TerminalSynthesisElider:
    """Render one proven terminal observation without another model round-trip."""

    def __init__(self, underlying: Any) -> None:
        self.underlying = underlying

    @staticmethod
    def _is_intermediate(capability_id: str) -> bool:
        return capability_id.endswith(".resolve") or capability_id in _INTERMEDIATE_CAPABILITIES

    @classmethod
    def _eligible_terminal(cls, observations: list[V4Observation]) -> V4Observation | None:
        terminals: list[V4Observation] = []
        for observation in observations:
            capability_id = str(observation.capability_id or "")
            if capability_id in _ELIGIBLE_TERMINALS:
                terminals.append(observation)
                continue
            if cls._is_intermediate(capability_id):
                continue
            # Unknown/non-resolver observations may represent another user goal.
            # Delegate rather than risk flattening a multi-part answer.
            return None
        return terminals[0] if len(terminals) == 1 else None

    @staticmethod
    def _task_keys(data: dict[str, Any]) -> list[str]:
        """Only return a complete source-backed key set, never a truncated sample."""
        raw = data.get("task_keys")
        if not isinstance(raw, list):
            raw = data.get("task_keys_sample")
        if isinstance(raw, list):
            keys = [str(item) for item in raw if str(item).strip()]
        else:
            tasks = data.get("tasks")
            if not isinstance(tasks, list):
                return []
            keys = []
            for task in tasks:
                if isinstance(task, dict):
                    key = task.get("key") or task.get("id") or task.get("source_id")
                    if key is not None and str(key).strip():
                        keys.append(str(key))
        total = data.get("task_key_count", data.get("count"))
        if total is not None:
            try:
                if int(total) != len(keys):
                    return []  # Compact sample is incomplete, do not imply a full list.
            except (TypeError, ValueError):
                return []
        return keys

    @classmethod
    def _render(cls, observation: V4Observation) -> str | None:
        answer = str(observation.answer or "").strip()
        if not answer:
            return None

        capability_id = str(observation.capability_id or "")
        data = dict(observation.data or {})

        # Search answers are intentionally compact, but preserve the exact
        # source-backed key set in prose when it is reasonably small. The UI
        # still renders the full structured task collection from response data.
        if capability_id.startswith("task.search"):
            keys = cls._task_keys(data)
            if keys and len(keys) <= 20 and not all(key in answer for key in keys):
                return f"{answer}\nКлючи: {', '.join(keys)}"
        return answer

    @staticmethod
    def _potential_multi_intent(query: str) -> bool:
        # Presentation-only safety guard: coordination can imply several goals.
        # False positives merely retain LLM synthesis, never change execution.
        return bool(re.search(r"(?i)(?:\s+и\s+|\s+and\s+|[,;])", str(query or "")))

    async def synthesize(self, user_query: str, observations: list[V4Observation]) -> str:
        if self._potential_multi_intent(user_query):
            return await self.underlying.synthesize(user_query, observations)
        terminal = self._eligible_terminal(observations)
        if terminal is not None:
            rendered = self._render(terminal)
            if rendered:
                return rendered
        return await self.underlying.synthesize(user_query, observations)
