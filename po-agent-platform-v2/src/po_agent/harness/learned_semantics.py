"""Versioned configuration learning for dialogue semantics.

The agent may learn configuration from explicit user corrections without
rewriting Python code. Conflicting definitions remain pending for review.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import uuid


@dataclass(frozen=True)
class LearnedSemanticRule:
    rule_id: str
    term: str
    meaning: str
    scope: str
    source_trace_id: str
    version: int
    status: str
    created_at: str


class LearnedSemanticsStore:
    """Small versioned JSON config store with safe autonomous promotion.

    Exact explicit definitions can be auto-promoted when they do not conflict
    with an active definition in the same scope. Conflicts are stored as
    pending candidates and never silently override existing behavior.
    """

    def __init__(self, path: str | Path = "var/learned_semantics.json") -> None:
        self.path = Path(path)

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": 1, "rules": []}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {"schema_version": 1, "rules": []}
        except (json.JSONDecodeError, OSError):
            return {"schema_version": 1, "rules": []}

    def _save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def active_rules(self, scope: str | None = None) -> list[LearnedSemanticRule]:
        rules = []
        for raw in self._load().get("rules", []):
            if raw.get("status") != "active":
                continue
            if scope is not None and raw.get("scope") not in {scope, "global"}:
                continue
            rules.append(LearnedSemanticRule(**raw))
        return rules

    def context(self, scope: str = "global") -> dict[str, str]:
        return {rule.term: rule.meaning for rule in self.active_rules(scope)}

    def learn_explicit_definition(
        self,
        *,
        term: str,
        meaning: str,
        source_trace_id: str,
        scope: str = "global",
    ) -> LearnedSemanticRule:
        term_n = term.strip().casefold()
        meaning_n = meaning.strip()
        if not term_n or not meaning_n or not source_trace_id:
            raise ValueError("term, meaning and source_trace_id are required")
        data = self._load()
        items = list(data.get("rules", []))
        active = [x for x in items if x.get("status") == "active" and x.get("term") == term_n and x.get("scope") == scope]
        same = next((x for x in active if x.get("meaning") == meaning_n), None)
        if same:
            return LearnedSemanticRule(**same)
        version = 1 + max((int(x.get("version", 0)) for x in items if x.get("term") == term_n and x.get("scope") == scope), default=0)
        status = "pending" if active else "active"
        rule = LearnedSemanticRule(
            rule_id=str(uuid.uuid4()),
            term=term_n,
            meaning=meaning_n,
            scope=scope,
            source_trace_id=source_trace_id,
            version=version,
            status=status,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        items.append(asdict(rule))
        data["rules"] = items
        self._save(data)
        return rule
