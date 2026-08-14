"""Comparison Engine for PO Agent Platform v2.

Compares outputs from prod and shadow prompt versions:
1. Run prod and shadow versions in parallel
2. Compare results
3. Log comparison results
4. Track statistics
"""

import sqlite3
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional


class ComparisonResult(Enum):
    """Result of comparison."""
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"
    ERROR = "error"


class ComparisonRecord:
    """Single comparison record."""

    def __init__(
        self,
        config_id: str,
        prompt_name: str,
        prod_version: int,
        shadow_version: int,
        prod_output: str,
        shadow_output: str,
        similarity_score: float,
        passed_threshold: bool,
        result: str = ComparisonResult.PASSED.value,
        created_at: Optional[datetime] = None,
    ):
        """Initialize comparison record.

        Args:
            config_id: Shadow mode config ID
            prompt_name: Name of the prompt
            prod_version: Production version number
            shadow_version: Shadow version number
            prod_output: Output from production version
            shadow_output: Output from shadow version
            similarity_score: Similarity score (0-1)
            passed_threshold: Did it pass threshold
            result: Comparison result
            created_at: Creation timestamp
        """
        self.id = str(uuid.uuid4())
        self.config_id = config_id
        self.prompt_name = prompt_name
        self.prod_version = prod_version
        self.shadow_version = shadow_version
        self.prod_output = prod_output
        self.shadow_output = shadow_output
        self.similarity_score = similarity_score
        self.passed_threshold = passed_threshold
        self.result = result
        self.created_at = created_at or datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "config_id": self.config_id,
            "prompt_name": self.prompt_name,
            "prod_version": self.prod_version,
            "shadow_version": self.shadow_version,
            "prod_output": self.prod_output,
            "shadow_output": self.shadow_output,
            "similarity_score": self.similarity_score,
            "passed_threshold": self.passed_threshold,
            "result": self.result,
            "created_at": self.created_at.isoformat(),
        }


class ComparisonEngine:
    """Comparison engine for shadow mode with SQLite persistence."""

    def __init__(self, db_path: str = ":memory:"):
        """Initialize comparison engine.

        Args:
            db_path: SQLite database path (":memory:" for in-memory, or file path)
        """
        self.db_path = db_path
        self.comparisons: list[ComparisonRecord] = []
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        cursor = self._conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comparisons (
                id TEXT PRIMARY KEY,
                config_id TEXT NOT NULL,
                prompt_name TEXT NOT NULL,
                prod_version INTEGER NOT NULL,
                shadow_version INTEGER NOT NULL,
                prod_output TEXT,
                shadow_output TEXT,
                similarity_score REAL NOT NULL,
                passed_threshold INTEGER NOT NULL,
                result TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_comparisons_config ON comparisons(config_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_comparisons_prompt ON comparisons(prompt_name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_comparisons_result ON comparisons(result)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_comparisons_created ON comparisons(created_at)
        """)
        self._conn.commit()

    def compare(
        self,
        config_id: str,
        prompt_name: str,
        prod_version: int,
        shadow_version: int,
        prod_output: str,
        shadow_output: str,
        threshold: float = 0.8,
    ) -> ComparisonRecord:
        """Compare prod and shadow outputs.

        Args:
            config_id: Shadow mode config ID
            prompt_name: Name of the prompt
            prod_version: Production version number
            shadow_version: Shadow version number
            prod_output: Output from production version
            shadow_output: Output from shadow version
            threshold: Similarity threshold for passing

        Returns:
            Comparison record
        """
        # Simple similarity calculation (length-based for now)
        # In production, this could use embedding similarity or BLEU score
        similarity = self._calculate_similarity(prod_output, shadow_output)
        passed_threshold = similarity >= threshold

        result = ComparisonResult.PASSED.value if passed_threshold else ComparisonResult.FAILED.value

        record = ComparisonRecord(
            config_id=config_id,
            prompt_name=prompt_name,
            prod_version=prod_version,
            shadow_version=shadow_version,
            prod_output=prod_output,
            shadow_output=shadow_output,
            similarity_score=similarity,
            passed_threshold=passed_threshold,
            result=result,
        )
        self.comparisons.append(record)
        self.save_comparison(record)
        return record

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts.

        Simple implementation using character-level comparison.
        In production, use embedding-based similarity.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-1)
        """
        if not text1 or not text2:
            return 0.0

        if text1 == text2:
            return 1.0

        # Jaccard similarity on characters
        set1 = set(text1.lower())
        set2 = set(text2.lower())

        if not set1 and not set2:
            return 1.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def save_comparison(self, record: ComparisonRecord) -> None:
        """Save comparison to database."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO comparisons
            (id, config_id, prompt_name, prod_version, shadow_version,
             prod_output, shadow_output, similarity_score, passed_threshold, result, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.id,
                record.config_id,
                record.prompt_name,
                record.prod_version,
                record.shadow_version,
                record.prod_output,
                record.shadow_output,
                record.similarity_score,
                1 if record.passed_threshold else 0,
                record.result,
                record.created_at.isoformat(),
            ),
        )
        self._conn.commit()

    def get_by_config(self, config_id: str) -> list[ComparisonRecord]:
        """Get comparisons by config ID."""
        return [c for c in self.comparisons if c.config_id == config_id]

    def get_by_prompt(self, prompt_name: str) -> list[ComparisonRecord]:
        """Get comparisons by prompt name."""
        return [c for c in self.comparisons if c.prompt_name == prompt_name]

    def get_by_result(self, result: str) -> list[ComparisonRecord]:
        """Get comparisons by result."""
        return [c for c in self.comparisons if c.result == result]

    def get_latest(self, prompt_name: str, limit: int = 10) -> list[ComparisonRecord]:
        """Get latest comparisons for a prompt."""
        prompt_comparisons = self.get_by_prompt(prompt_name)
        return sorted(prompt_comparisons, key=lambda c: c.created_at, reverse=True)[:limit]

    def get_statistics(self, prompt_name: Optional[str] = None) -> dict:
        """Get comparison statistics.

        Args:
            prompt_name: Optional prompt name to filter

        Returns:
            Dictionary with statistics
        """
        comparisons = self.comparisons
        if prompt_name:
            comparisons = self.get_by_prompt(prompt_name)

        total = len(comparisons)
        if total == 0:
            return {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "passed_rate": 0.0,
                "avg_similarity": 0.0,
            }

        passed = len([c for c in comparisons if c.result == ComparisonResult.PASSED.value])
        failed = total - passed
        avg_similarity = sum(c.similarity_score for c in comparisons) / total

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "passed_rate": passed / total,
            "avg_similarity": avg_similarity,
        }

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
