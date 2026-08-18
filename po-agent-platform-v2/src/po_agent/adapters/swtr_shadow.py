"""Read-only SWTR/AS21 real-case capture for shadow evaluation.

This module is deliberately incapable of mutating AS21. It converts live AS21
facts into immutable, content-addressed snapshots that can be fed into the
existing evaluation/evolution stack without creating a production write path.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Iterable, Optional

from po_agent.domain.models import Task

from .as21 import AS21Adapter


class SWTRShadowError(RuntimeError):
    """Base error for the read-only SWTR shadow boundary."""


class SWTRShadowBudgetExceeded(SWTRShadowError):
    """The requested real-case sample exceeds the configured safety budget."""


@dataclass(frozen=True, slots=True)
class SWTRTaskSnapshot:
    """Immutable canonical snapshot of one real SWTR task."""

    task_key: str
    source: str
    payload_json: str
    content_sha256: str

    @classmethod
    def from_task(cls, task: Task) -> "SWTRTaskSnapshot":
        payload = task.model_dump(mode="json", exclude_none=False)
        payload_json = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = sha256(payload_json.encode("utf-8")).hexdigest()
        return cls(
            task_key=task.key,
            source=task.source,
            payload_json=payload_json,
            content_sha256=digest,
        )

    def as_dict(self) -> dict:
        """Return a detached JSON-compatible copy for downstream evaluation."""
        return json.loads(self.payload_json)


@dataclass(frozen=True, slots=True)
class SWTRShadowBatch:
    """Bounded, immutable collection of real-case snapshots."""

    cases: tuple[SWTRTaskSnapshot, ...]
    batch_sha256: str

    @classmethod
    def build(cls, cases: Iterable[SWTRTaskSnapshot]) -> "SWTRShadowBatch":
        ordered = tuple(sorted(cases, key=lambda item: item.task_key))
        material = "\n".join(
            f"{case.task_key}:{case.content_sha256}" for case in ordered
        )
        return cls(
            cases=ordered,
            batch_sha256=sha256(material.encode("utf-8")).hexdigest(),
        )


class SWTRReadOnlyShadowSource:
    """Read-only real-case source backed by an :class:`AS21Adapter`.

    The class exposes only observation methods. There is intentionally no
    transition/update/comment/attachment-write API. The boundary therefore
    remains safe even when the downstream shadow evaluator is autonomous.
    """

    def __init__(
        self,
        adapter: AS21Adapter,
        *,
        max_cases: int = 30,
        require_swtr_source: bool = True,
    ) -> None:
        if max_cases <= 0:
            raise ValueError("max_cases must be positive")
        self._adapter = adapter
        self._max_cases = max_cases
        self._require_swtr_source = require_swtr_source

    @property
    def max_cases(self) -> int:
        return self._max_cases

    @staticmethod
    def _normalize_keys(task_keys: Iterable[str]) -> tuple[str, ...]:
        keys: list[str] = []
        seen: set[str] = set()
        for raw in task_keys:
            key = raw.strip().upper()
            if not key:
                raise ValueError("task key must not be empty")
            if key not in seen:
                seen.add(key)
                keys.append(key)
        return tuple(keys)

    def _validate_task(self, task: Task) -> None:
        if self._require_swtr_source and task.source.lower() not in {"swtr", "as21"}:
            raise SWTRShadowError(
                f"unexpected task source {task.source!r}; real SWTR shadow requires swtr/as21"
            )

    async def capture_keys(self, task_keys: Iterable[str]) -> SWTRShadowBatch:
        """Capture an explicit bounded set of real AS21 tasks.

        Missing tasks fail closed. This avoids silently changing the evaluation
        corpus and prevents a source outage from looking like a smaller sample.
        """
        keys = self._normalize_keys(task_keys)
        if len(keys) > self._max_cases:
            raise SWTRShadowBudgetExceeded(
                f"requested {len(keys)} tasks, budget is {self._max_cases}"
            )

        snapshots: list[SWTRTaskSnapshot] = []
        for key in keys:
            task = await self._adapter.get_task(key)
            if task is None:
                raise SWTRShadowError(f"SWTR task {key} was not found")
            self._validate_task(task)
            snapshots.append(SWTRTaskSnapshot.from_task(task))
        return SWTRShadowBatch.build(snapshots)

    async def capture_query(
        self,
        query: str,
        *,
        limit: Optional[int] = None,
    ) -> SWTRShadowBatch:
        """Capture a bounded read-only query result from SWTR/AS21."""
        query = query.strip()
        if not query:
            raise ValueError("query must not be empty")
        effective_limit = self._max_cases if limit is None else limit
        if effective_limit <= 0 or effective_limit > self._max_cases:
            raise SWTRShadowBudgetExceeded(
                f"query limit must be in range 1..{self._max_cases}"
            )

        tasks = await self._adapter.search_tasks(query, max_results=effective_limit)
        if len(tasks) > effective_limit:
            raise SWTRShadowError("AS21 adapter returned more tasks than requested")
        snapshots: list[SWTRTaskSnapshot] = []
        seen: set[str] = set()
        for task in tasks:
            self._validate_task(task)
            if task.key in seen:
                raise SWTRShadowError(f"duplicate SWTR task in source result: {task.key}")
            seen.add(task.key)
            snapshots.append(SWTRTaskSnapshot.from_task(task))
        return SWTRShadowBatch.build(snapshots)

    async def close(self) -> None:
        await self._adapter.close()
