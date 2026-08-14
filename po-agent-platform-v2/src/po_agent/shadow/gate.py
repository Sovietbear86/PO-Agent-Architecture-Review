"""Regression Gate for PO Agent Platform v2.

Prevents deployment of prompts that fail comparison tests:
1. Check recent shadow mode comparisons
2. Calculate pass rate for each prompt
3. Block deployment if pass rate < threshold
4. Log gate decisions
"""

import sqlite3
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional


class GateStatus(Enum):
    """Status of regression gate."""
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    REVIEW_REQUIRED = "review_required"


class RegressionGateRecord:
    """Single regression gate record."""

    def __init__(
        self,
        prompt_name: str,
        shadow_version: int,
        pass_rate: float,
        threshold: float,
        gate_passed: bool,
        decision_reason: str,
        reviewed_by: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ):
        """Initialize regression gate record.

        Args:
            prompt_name: Name of the prompt
            shadow_version: Version to deploy
            pass_rate: Pass rate from comparisons
            threshold: Threshold for passing
            gate_passed: Did it pass the gate
            decision_reason: Reason for decision
            reviewed_by: User who reviewed
            created_at: Creation timestamp
        """
        self.id = str(uuid.uuid4())
        self.prompt_name = prompt_name
        self.shadow_version = shadow_version
        self.pass_rate = pass_rate
        self.threshold = threshold
        self.gate_passed = gate_passed
        self.decision_reason = decision_reason
        self.reviewed_by = reviewed_by
        self.created_at = created_at or datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "prompt_name": self.prompt_name,
            "shadow_version": self.shadow_version,
            "pass_rate": self.pass_rate,
            "threshold": self.threshold,
            "gate_passed": self.gate_passed,
            "decision_reason": self.decision_reason,
            "reviewed_by": self.reviewed_by,
            "created_at": self.created_at.isoformat(),
        }


class RegressionGate:
    """Regression gate for preventing deployments with low pass rates."""

    def __init__(self, db_path: str = ":memory:"):
        """Initialize regression gate.

        Args:
            db_path: SQLite database path (":memory:" for in-memory, or file path)
        """
        self.db_path = db_path
        self.gates: list[RegressionGateRecord] = []
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        cursor = self._conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS regression_gates (
                id TEXT PRIMARY KEY,
                prompt_name TEXT NOT NULL,
                shadow_version INTEGER NOT NULL,
                pass_rate REAL NOT NULL,
                threshold REAL NOT NULL,
                gate_passed INTEGER NOT NULL,
                decision_reason TEXT,
                reviewed_by TEXT,
                created_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_gates_prompt ON regression_gates(prompt_name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_gates_passed ON regression_gates(gate_passed)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_gates_created ON regression_gates(created_at)
        """)
        self._conn.commit()

    def check(
        self,
        prompt_name: str,
        shadow_version: int,
        comparisons: list[dict],
        threshold: float = 0.8,
        reviewed_by: Optional[str] = None,
    ) -> RegressionGateRecord:
        """Check if prompt passes regression gate.

        Args:
            prompt_name: Name of the prompt
            shadow_version: Version to deploy
            comparisons: List of comparison results
            threshold: Minimum pass rate required
            reviewed_by: User who reviewed

        Returns:
            Gate record
        """
        if not comparisons:
            record = RegressionGateRecord(
                prompt_name=prompt_name,
                shadow_version=shadow_version,
                pass_rate=0.0,
                threshold=threshold,
                gate_passed=False,
                decision_reason="No comparisons available",
                reviewed_by=reviewed_by,
            )
            self.gates.append(record)
            self.save_record(record)
            return record

        passed = sum(1 for c in comparisons if c.get("passed_threshold", False))
        pass_rate = passed / len(comparisons)

        gate_passed = pass_rate >= threshold

        if gate_passed:
            decision_reason = f"Pass rate {pass_rate:.2f} >= threshold {threshold}"
        else:
            decision_reason = f"Pass rate {pass_rate:.2f} < threshold {threshold}"

        record = RegressionGateRecord(
            prompt_name=prompt_name,
            shadow_version=shadow_version,
            pass_rate=pass_rate,
            threshold=threshold,
            gate_passed=gate_passed,
            decision_reason=decision_reason,
            reviewed_by=reviewed_by,
        )
        self.gates.append(record)
        self.save_record(record)
        return record

    def save_record(self, record: RegressionGateRecord) -> None:
        """Save gate record to database."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO regression_gates
            (id, prompt_name, shadow_version, pass_rate, threshold, gate_passed, decision_reason, reviewed_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.id,
                record.prompt_name,
                record.shadow_version,
                record.pass_rate,
                record.threshold,
                1 if record.gate_passed else 0,
                record.decision_reason,
                record.reviewed_by,
                record.created_at.isoformat(),
            ),
        )
        self._conn.commit()

    def get_by_prompt(self, prompt_name: str) -> list[RegressionGateRecord]:
        """Get gate records by prompt name."""
        return [g for g in self.gates if g.prompt_name == prompt_name]

    def get_passed(self) -> list[RegressionGateRecord]:
        """Get passed gate records."""
        return [g for g in self.gates if g.gate_passed]

    def get_failed(self) -> list[RegressionGateRecord]:
        """Get failed gate records."""
        return [g for g in self.gates if not g.gate_passed]

    def get_latest(self, prompt_name: str, limit: int = 10) -> list[RegressionGateRecord]:
        """Get latest gate records for a prompt."""
        prompt_gates = self.get_by_prompt(prompt_name)
        return sorted(prompt_gates, key=lambda g: g.created_at, reverse=True)[:limit]

    def get_statistics(self, prompt_name: Optional[str] = None) -> dict:
        """Get gate statistics.

        Args:
            prompt_name: Optional prompt name to filter

        Returns:
            Dictionary with statistics
        """
        gates = self.gates
        if prompt_name:
            gates = self.get_by_prompt(prompt_name)

        total = len(gates)
        if total == 0:
            return {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "passed_rate": 0.0,
            }

        passed = len([g for g in gates if g.gate_passed])
        failed = total - passed

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "passed_rate": passed / total,
        }

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
