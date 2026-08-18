"""In-memory AS21 adapter backed only by an immutable frozen task corpus.

The adapter deliberately has no network fallback.  It exists to run the real PO
Agent/Harness against a corpus captured from SWTR once, while preserving the
existing :class:`AS21Adapter` contract used by production capabilities.
"""
from __future__ import annotations

import json
import re
from typing import Iterable, Optional

from po_agent.domain.models import Attachment, StatusTransition, Task

from .as21 import AS21Adapter
from .swtr_shadow import SWTRShadowBatch


_KEY_QUERY_RE = re.compile(r"^\s*(?:key\s*=\s*)?([A-Za-z]+-\d+)\s*$", re.IGNORECASE)


class FrozenAS21Adapter(AS21Adapter):
    """Read-only adapter over canonical JSON snapshots of :class:`Task` objects.

    Canonical JSON is retained instead of mutable model instances.  Every public
    read reconstructs a fresh Pydantic model, so callers cannot mutate the
    underlying corpus through nested lists, attachments, or status history.
    """

    def __init__(self, tasks: Iterable[Task]) -> None:
        corpus: dict[str, str] = {}
        for task in tasks:
            if not isinstance(task, Task):
                raise TypeError("FrozenAS21Adapter accepts Task instances only")
            key = task.key.strip().upper()
            if not key:
                raise ValueError("task key must not be empty")
            if key in corpus:
                raise ValueError(f"duplicate frozen task key: {key}")
            corpus[key] = self._dump_task(task)
        self._corpus = corpus
        self._closed = False

    @classmethod
    def from_shadow_batch(cls, batch: SWTRShadowBatch) -> "FrozenAS21Adapter":
        """Build an adapter from an already captured immutable SWTR batch."""
        if not isinstance(batch, SWTRShadowBatch):
            raise TypeError("batch must be SWTRShadowBatch")
        tasks: list[Task] = []
        seen: set[str] = set()
        for snapshot in batch.cases:
            key = snapshot.task_key.strip().upper()
            if key in seen:
                raise ValueError(f"duplicate frozen task key: {key}")
            seen.add(key)
            payload = json.loads(snapshot.payload_json)
            task = Task.model_validate(payload)
            if task.key.strip().upper() != key:
                raise ValueError(f"snapshot/task key mismatch: {snapshot.task_key!r} != {task.key!r}")
            tasks.append(task)
        return cls(tasks)

    @staticmethod
    def _dump_task(task: Task) -> str:
        return json.dumps(
            task.model_dump(mode="json", exclude_none=False),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    @staticmethod
    def _load_task(payload_json: str) -> Task:
        return Task.model_validate(json.loads(payload_json))

    def _ensure_open(self) -> None:
        # close() is intentionally only a lifecycle marker; reads remain valid
        # after close for compatibility with in-memory/fake adapters.  More
        # importantly, close can never trigger a network reconnect/fallback.
        return None

    @property
    def task_count(self) -> int:
        return len(self._corpus)

    @property
    def task_keys(self) -> tuple[str, ...]:
        return tuple(sorted(self._corpus))

    async def get_task(self, task_key: str) -> Optional[Task]:
        self._ensure_open()
        key = task_key.strip().upper()
        if not key:
            return None
        payload = self._corpus.get(key)
        return None if payload is None else self._load_task(payload)

    async def search_tasks(
        self,
        jql: str,
        max_results: int = 50,
        fields: Optional[list[str]] = None,
    ) -> list[Task]:
        """Deterministic bounded search over the frozen corpus.

        This is intentionally not a Jira/JQL implementation.  Exact task-key
        queries (``WMB-1`` or ``key = WMB-1``) are supported, as are simple
        case-insensitive text queries over key/title/description.  Complex JQL
        syntax fails closed rather than falling back to a live source.
        """
        self._ensure_open()
        del fields  # field projection is intentionally not used for domain models
        if max_results <= 0:
            raise ValueError("max_results must be positive")
        if max_results > 10_000:
            raise ValueError("max_results exceeds frozen-search safety bound")

        query = jql.strip()
        if not query:
            return [self._load_task(self._corpus[key]) for key in sorted(self._corpus)[:max_results]]

        exact = _KEY_QUERY_RE.fullmatch(query)
        if exact:
            task = await self.get_task(exact.group(1))
            return [] if task is None else [task]

        lowered = query.casefold()
        if any(token in lowered for token in (" and ", " or ", " order by ", "!=", ">=", "<=", "~")):
            raise ValueError("complex JQL is not supported by FrozenAS21Adapter")

        matches: list[Task] = []
        for key in sorted(self._corpus):
            task = self._load_task(self._corpus[key])
            haystack = "\n".join((task.key, task.title, task.description or "")).casefold()
            if lowered in haystack:
                matches.append(task)
                if len(matches) >= max_results:
                    break
        return matches

    async def get_task_history(self, task_key: str) -> list[StatusTransition]:
        task = await self.get_task(task_key)
        if task is None:
            return []
        return [item.model_copy(deep=True) for item in task.status_transitions]

    async def get_sprint_tasks(self, sprint_id: str, space: Optional[str] = None) -> list[Task]:
        self._ensure_open()
        sprint = sprint_id.strip()
        if not sprint:
            return []
        prefix = space.strip().upper() if space else None
        result: list[Task] = []
        for key in sorted(self._corpus):
            task = self._load_task(self._corpus[key])
            if task.sprint_id == sprint and (prefix is None or task.key.upper().startswith(prefix + "-")):
                result.append(task)
        return result

    async def get_release_tasks(self, release_id: str, space: Optional[str] = None) -> list[Task]:
        self._ensure_open()
        release = release_id.strip()
        if not release:
            return []
        prefix = space.strip().upper() if space else None
        result: list[Task] = []
        for key in sorted(self._corpus):
            task = self._load_task(self._corpus[key])
            if task.release_id == release and (prefix is None or task.key.upper().startswith(prefix + "-")):
                result.append(task)
        return result

    async def get_attachment_metadata(
        self,
        task_key: str,
        attachment_id: Optional[str] = None,
    ) -> list[Attachment]:
        task = await self.get_task(task_key)
        if task is None:
            return []
        attachments = task.attachments
        if attachment_id is not None:
            attachments = [item for item in attachments if item.id == attachment_id]
        return [item.model_copy(deep=True) for item in attachments]

    async def close(self) -> None:
        # Idempotent and intentionally side-effect free.  No resource owned by
        # this adapter can initiate network access.
        self._closed = True
