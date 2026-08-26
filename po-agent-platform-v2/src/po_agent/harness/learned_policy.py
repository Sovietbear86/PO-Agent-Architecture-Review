"""Persistent, bounded behavioural learning for runtime corrections.

The store deliberately persists *generalised policies*, never entity facts or
arbitrary Python.  A correction may promote only an allow-listed behaviour
whose validation was grounded in source evidence.  Policies are versioned,
auditable and reversible and can therefore be exercised for every skill
without allowing runtime self-modifying code.
"""
from __future__ import annotations

import json
import os
import tempfile
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_ALLOWED_BEHAVIOURS = frozenset({"authoritative_recheck_on_negative"})


@dataclass(frozen=True)
class LearnedPolicy:
    policy_id: str
    skill_id: str
    behaviour: str
    version: int
    state: str
    created_at: str
    correction_trace_id: str
    validation_trace_id: str
    evidence_count: int
    rollback_reason: str | None = None

    @property
    def active(self) -> bool:
        return self.state == "promoted" and self.behaviour in _ALLOWED_BEHAVIOURS


class LearnedPolicyStore:
    """Small JSON persistence layer for safe runtime behavioural policies."""

    def __init__(self, path: str | Path | None = None) -> None:
        configured = path or os.getenv("PO_AGENT_LEARNED_POLICY_PATH")
        self.path = Path(configured) if configured else Path(".po_agent/learned_policies.json")
        self._lock = threading.RLock()

    def active_for(self, skill_id: str | None) -> LearnedPolicy | None:
        if not skill_id:
            return None
        records = [item for item in self._load() if item.skill_id == skill_id and item.active]
        return max(records, key=lambda item: item.version, default=None)

    def promote_grounded_recheck(
        self,
        *,
        skill_id: str,
        correction_trace_id: str,
        validation_trace_id: str,
        evidence_count: int,
    ) -> LearnedPolicy:
        """Promote the only runtime-mutable policy currently allow-listed.

        Promotion is accepted only after a successful source-grounded validation.
        Repeated corrections are idempotent while an active policy exists.
        """
        if not skill_id.strip():
            raise ValueError("skill_id is required")
        if evidence_count < 1:
            raise ValueError("grounded evidence is required before policy promotion")
        with self._lock:
            existing = self.active_for(skill_id)
            if existing is not None and existing.behaviour == "authoritative_recheck_on_negative":
                return existing
            all_records = self._load()
            version = 1 + max((item.version for item in all_records if item.skill_id == skill_id), default=0)
            policy = LearnedPolicy(
                policy_id=f"{skill_id}:authoritative_recheck_on_negative:v{version}",
                skill_id=skill_id,
                behaviour="authoritative_recheck_on_negative",
                version=version,
                state="promoted",
                created_at=datetime.now(timezone.utc).isoformat(),
                correction_trace_id=correction_trace_id,
                validation_trace_id=validation_trace_id,
                evidence_count=evidence_count,
            )
            all_records.append(policy)
            self._save(all_records)
            return policy

    def rollback(self, skill_id: str, *, reason: str) -> LearnedPolicy:
        if not reason.strip():
            raise ValueError("rollback reason is required")
        with self._lock:
            records = self._load()
            active = max(
                (item for item in records if item.skill_id == skill_id and item.active),
                key=lambda item: item.version,
                default=None,
            )
            if active is None:
                raise ValueError(f"no active learned policy for {skill_id}")
            replacement = LearnedPolicy(**{
                **asdict(active),
                "state": "rolled_back",
                "rollback_reason": reason.strip(),
            })
            records = [replacement if item.policy_id == active.policy_id else item for item in records]
            self._save(records)
            return replacement

    def inventory(self) -> list[dict[str, Any]]:
        return [asdict(item) for item in self._load()]

    def _load(self) -> list[LearnedPolicy]:
        with self._lock:
            if not self.path.exists():
                return []
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return []
            if not isinstance(raw, list):
                return []
            result: list[LearnedPolicy] = []
            for row in raw:
                if not isinstance(row, dict):
                    continue
                try:
                    policy = LearnedPolicy(**row)
                except (TypeError, ValueError):
                    continue
                if policy.behaviour in _ALLOWED_BEHAVIOURS:
                    result.append(policy)
            return result

    def _save(self, records: list[LearnedPolicy]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps([asdict(item) for item in records], ensure_ascii=False, indent=2, sort_keys=True)
        fd, tmp_name = tempfile.mkstemp(prefix="learned-policies-", suffix=".json", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self.path)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
