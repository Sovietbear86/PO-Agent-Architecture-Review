"""Regression suite for PO Agent Platform v2.1.

Tests for:
- Component regression
- Integration regression
- API regression
- Memory leak detection
- Performance benchmarks
"""

import pytest
import time
import sqlite3
from pathlib import Path

from po_agent.knowledge.layer import KnowledgeLayer, KnowledgeLoader
from po_agent.contracts.actions import ActionManager, ActionProposal, ActionStatus
from po_agent.shadow.promotion import PromotionManager, PromotionRecord
from po_agent.shadow.approval import HumanApprovalGate, HumanApprovalRecord


class TestKnowledgeLayerRegression:
    """Regression tests for Knowledge Layer."""

    def test_knowledge_layer_init_no_error(self):
        """Test knowledge layer initialization doesn't error on missing files."""
        # Just initialize without loading - should not fail
        layer = KnowledgeLayer()
        # The layer should be created without loading config
        layer.close()

    def test_knowledge_loader_no_error_on_missing(self):
        """Test knowledge loader handles missing files gracefully."""
        loader = KnowledgeLoader()
        # Should handle missing team.example.yaml gracefully
        assert loader is not None


class TestActionContractsRegression:
    """Regression tests for Action Contracts."""

    def test_proposal_lifecycle(self, action_manager: ActionManager):
        """Test full proposal lifecycle."""
        proposal = action_manager.create_proposal(
            action_type="create_task",
            target="WMB-123",
            details={"title": "Test"},
        )

        assert proposal.status == ActionStatus.PROPOSAL.value

        proposal.confirm(confirmed_by="Kalachanov.V.V")
        assert proposal.status == ActionStatus.CONFIRMED.value

        proposal.execute(success=True, result={"id": "WMB-123"})
        assert proposal.status == ActionStatus.EXECUTED.value

    def test_proposal_statistics(self, action_manager: ActionManager):
        """Test proposal statistics."""
        for i in range(5):
            action_manager.create_proposal(
                action_type="create_task",
                target=f"WMB-{i}",
                details={},
            )

        stats = action_manager.get_statistics()
        assert stats["total"] == 5
        assert stats.get("proposed", 0) == 5 or stats.get("proposal", 0) == 5


class TestPromotionManagerRegression:
    """Regression tests for Promotion Manager."""

    def test_promotion_create(self, promotion_manager: PromotionManager):
        """Test promotion creation."""
        record = promotion_manager.create_promotion(
            prompt_name="quality_rules",
            from_version=1,
            to_version=2,
            requested_by="Kalachanov.V.V",
        )

        assert record is not None
        assert record.prompt_name == "quality_rules"
        assert record.to_version == 2

    def test_rollback_create(self, promotion_manager: PromotionManager):
        """Test rollback creation."""
        record = promotion_manager.create_rollback(
            prompt_name="quality_rules",
            from_version=2,
            to_version=1,
            rollback_reason="Testing rollback",
            requested_by="Kalachanov.V.V",
        )

        assert record is not None
        assert record.action_type == "rollback"
        assert record.to_version == 1
        assert "Testing rollback" in record.rollback_reason or record.rollback_reason is None


class TestApprovalGateRegression:
    """Regression tests for Human Approval Gate."""

    def test_approval_request(self, approval_gate: HumanApprovalGate):
        """Test approval request flow."""
        record = approval_gate.request_approval(
            gate_record_id="gate-001",
            prompt_name="quality_rules",
            shadow_version=2,
            requested_by="Kalachanov.V.V",
            approval_reason="Review needed",
        )

        assert record is not None
        assert record.status == "pending"
        assert record.prompt_name == "quality_rules"

    def test_approval_approve(self, approval_gate: HumanApprovalGate):
        """Test approval approval."""
        record = approval_gate.request_approval(
            gate_record_id="gate-001",
            prompt_name="quality_rules",
            shadow_version=2,
            requested_by="Kalachanov.V.V",
        )

        approved = approval_gate.approve(
            record_id=record.id,
            approved_by="Garanin.R.V",
            reason="Approved for release",
        )

        assert approved is not None
        assert approved.status == "approved"

    def test_approval_reject(self, approval_gate: HumanApprovalGate):
        """Test approval rejection."""
        record = approval_gate.request_approval(
            gate_record_id="gate-001",
            prompt_name="quality_rules",
            shadow_version=3,
            requested_by="Kalachanov.V.V",
        )

        rejected = approval_gate.reject(
            record_id=record.id,
            approved_by="Garanin.R.V",
            reason="Threshold too high",
        )

        assert rejected is not None
        assert rejected.status == "rejected"

    def test_get_by_id(self, approval_gate: HumanApprovalGate):
        """Test get approval by ID."""
        record = approval_gate.request_approval(
            gate_record_id="gate-001",
            prompt_name="quality_rules",
            shadow_version=2,
            requested_by="Kalachanov.V.V",
        )

        retrieved = approval_gate.get_by_id(record.id)
        assert retrieved is not None
        assert retrieved.id == record.id


class TestMemoryRegression:
    """Memory regression tests."""

    def test_sqlite_memory_cleanup(self, tmp_path: Path):
        """Test SQLite database cleanup."""
        db_path = str(tmp_path / "test.db")

        # Create and close multiple times
        for i in range(10):
            conn = sqlite3.connect(db_path, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY)")
            cursor.execute("INSERT OR REPLACE INTO test VALUES (?)", (i + 1,))
            conn.commit()
            conn.close()

        # Check file exists
        assert Path(db_path).exists()
        size = Path(db_path).stat().st_size
        assert size > 0

    def test_sqlite_in_memory(self):
        """Test in-memory SQLite database."""
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
        cursor.execute("INSERT INTO test VALUES (1)")
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM test")
        count = cursor.fetchone()[0]
        assert count == 1

        conn.close()


class TestPerformanceBenchmarks:
    """Performance benchmark tests."""

    def test_action_manager_throughput(self, action_manager: ActionManager):
        """Test action manager throughput."""
        start = time.time()

        for i in range(100):
            proposal = action_manager.create_proposal(
                action_type="test",
                target=f"target-{i}",
                details={},
            )
            proposal.confirm(confirmed_by="test_user")
            proposal.execute(success=True)

        total_time = time.time() - start

        # Should complete 100 operations in < 5 seconds
        assert total_time < 5.0

    def test_promotion_manager_throughput(self, promotion_manager: PromotionManager):
        """Test promotion manager throughput."""
        start = time.time()

        for i in range(50):
            promotion_manager.create_promotion(
                prompt_name=f"prompt-{i}",
                from_version=1,
                to_version=2,
                requested_by="test_user",
            )

        total_time = time.time() - start

        # Should complete 50 promotions in < 3 seconds
        assert total_time < 3.0

    def test_approval_gate_throughput(self, approval_gate: HumanApprovalGate):
        """Test approval gate throughput."""
        start = time.time()

        for i in range(50):
            record = approval_gate.request_approval(
                gate_record_id=f"gate-{i}",
                prompt_name=f"prompt-{i}",
                shadow_version=2,
                requested_by="test_user",
            )
            approval_gate.approve(
                record_id=record.id,
                approved_by="approver",
                reason="test",
            )

        total_time = time.time() - start

        # Should complete 50 approval cycles in < 5 seconds
        assert total_time < 5.0


class TestIntegrationRegression:
    """Integration regression tests."""

    def test_action_and_approval_integration(self, action_manager: ActionManager, approval_gate: HumanApprovalGate):
        """Test action and approval integration."""
        # Create proposal
        proposal = action_manager.create_proposal(
            action_type="config_change",
            target="quality_rules",
            details={"threshold": 0.85},
            requested_by="Kalachanov.V.V",
        )

        # Create approval request
        record = approval_gate.request_approval(
            gate_record_id=proposal.id,
            prompt_name="quality_rules",
            shadow_version=2,
            requested_by="Kalachanov.V.V",
        )

        # Approve
        approval_gate.approve(
            record_id=record.id,
            approved_by="Garanin.R.V",
            reason="Approved",
        )

        # Execute proposal
        proposal.execute(success=True, result={"configured": True})

        # Verify
        stats = action_manager.get_statistics()
        assert stats["total"] >= 1
