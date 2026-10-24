"""Pytest fixtures for PO Agent Platform v2 tests."""

import pytest

from po_agent.contracts.actions import ActionManager
from po_agent.shadow.promotion import PromotionManager
from po_agent.shadow.approval import HumanApprovalGate


@pytest.fixture
def action_manager():
    """Create action manager fixture."""
    manager = ActionManager(db_path=":memory:")
    yield manager
    manager.close()


@pytest.fixture
def promotion_manager():
    """Create promotion manager fixture."""
    manager = PromotionManager(db_path=":memory:")
    yield manager
    manager.close()


@pytest.fixture
def approval_gate():
    """Create approval gate fixture."""
    gate = HumanApprovalGate(db_path=":memory:")
    yield gate
    gate.close()
