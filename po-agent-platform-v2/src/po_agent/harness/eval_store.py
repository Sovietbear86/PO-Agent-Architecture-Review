"""Versioned evaluation seeds derived from explicit traces and feedback.

Eval seeds are evidence for offline/shadow evaluation. Creating a seed never
changes router rules, prompts, capabilities or production behavior.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol

from .feedback_store import FeedbackRecord
from .operational_history import ExecutionRecord


@dataclass(frozen=True)
class EvalSeed:
    eval_id: str
    source_trace_id: str
    source_feedback_id: str | None
    created_at: str
    query: str
    expected_intent: str | None = None
    expected_entity: str | None = None
    expected_facts: list[str] = field(default_factory=list)
    notes: str | None = None
    source_versions: dict[str, object] = field(default_factory=dict)
    status: str = "candidate"


class EvalSeedStore(Protocol):
    def append(self, seed: EvalSeed) -> None: ...
    def get(self, eval_id: str) -> EvalSeed | None: ...
    def candidates(self, limit: int = 100) -> list[EvalSeed]: ...


class SQLiteEvalSeedStore:
    def __init__(self, db_path: str = ":memory:") -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS harness_eval_seeds (
                eval_id TEXT PRIMARY KEY,
                source_trace_id TEXT NOT NULL,
                source_feedback_id TEXT,
                created_at TEXT NOT NULL,
                query TEXT NOT NULL,
                expected_intent TEXT,
                expected_entity TEXT,
                expected_facts_json TEXT NOT NULL,
                notes TEXT,
                source_versions_json TEXT NOT NULL,
                status TEXT NOT NULL
            )
            """
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_harness_eval_trace ON harness_eval_seeds(source_trace_id)"
        )
        self._conn.commit()

    def append(self, seed: EvalSeed) -> None:
        try:
            self._conn.execute(
                "INSERT INTO harness_eval_seeds VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    seed.eval_id,
                    seed.source_trace_id,
                    seed.source_feedback_id,
                    seed.created_at,
                    seed.query,
                    seed.expected_intent,
                    seed.expected_entity,
                    json.dumps(seed.expected_facts, ensure_ascii=False),
                    seed.notes,
                    json.dumps(seed.source_versions, ensure_ascii=False, sort_keys=True),
                    seed.status,
                ),
            )
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"eval seed already exists: {seed.eval_id}") from exc

    @staticmethod
    def _decode(row: tuple[object, ...]) -> EvalSeed:
        return EvalSeed(
            eval_id=str(row[0]), source_trace_id=str(row[1]),
            source_feedback_id=str(row[2]) if row[2] is not None else None,
            created_at=str(row[3]), query=str(row[4]),
            expected_intent=str(row[5]) if row[5] is not None else None,
            expected_entity=str(row[6]) if row[6] is not None else None,
            expected_facts=json.loads(str(row[7])),
            notes=str(row[8]) if row[8] is not None else None,
            source_versions=json.loads(str(row[9])), status=str(row[10]),
        )

    def get(self, eval_id: str) -> EvalSeed | None:
        row = self._conn.execute(
            "SELECT * FROM harness_eval_seeds WHERE eval_id = ?", (eval_id,)
        ).fetchone()
        return self._decode(row) if row else None

    def candidates(self, limit: int = 100) -> list[EvalSeed]:
        rows = self._conn.execute(
            "SELECT * FROM harness_eval_seeds WHERE status = 'candidate' ORDER BY created_at ASC LIMIT ?",
            (limit,),
        ).fetchall()
        return [self._decode(row) for row in rows]


def seed_from_feedback(trace: ExecutionRecord, feedback: FeedbackRecord) -> EvalSeed:
    if trace.trace_id != feedback.trace_id:
        raise ValueError("feedback trace does not match execution trace")
    if feedback.rating != "down" and not (
        feedback.correction or feedback.expected_intent or feedback.expected_entity
    ):
        raise ValueError("positive feedback without correction is not an eval failure seed")

    facts: list[str] = []
    if feedback.correction:
        facts.append(feedback.correction)
    return EvalSeed(
        eval_id=str(uuid.uuid4()),
        source_trace_id=trace.trace_id,
        source_feedback_id=feedback.feedback_id,
        created_at=datetime.now(timezone.utc).isoformat(),
        query=trace.request,
        expected_intent=feedback.expected_intent,
        expected_entity=feedback.expected_entity,
        expected_facts=facts,
        notes=feedback.comment,
        source_versions={
            "agent": trace.versions.agent,
            "router": trace.versions.router,
            "prompt": trace.versions.prompt,
            "capability": trace.versions.capability,
            "metrics": trace.versions.metrics,
            "model": trace.versions.model,
            "config": trace.versions.config,
            "skill_id": trace.skill_id,
            "skill_version": trace.skill_version,
        },
    )
