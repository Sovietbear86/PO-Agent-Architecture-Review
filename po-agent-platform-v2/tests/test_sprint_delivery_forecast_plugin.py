"""Plugin acceptance tests: no changes to frozen Core V4."""
import asyncio
from types import SimpleNamespace

import pytest

from po_agent.harness.agent_core_v4 import V4CapabilityUnavailable
from po_agent.harness.v4_plugin_registry import discover_v4_plugins
from po_agent.harness.v4_plugins.sprint_delivery_forecast import build_sprint_delivery_forecast


class Adapter:
    async def get_sprint_delivery_forecast(self, sprint_id):
        return {
            "sprint_id": sprint_id, "status": "READY", "source": "REAL_AS21",
            "forecast_completion_percent": 72.5, "scope_total": 8,
            "closed_total": 5, "committed_predictability": None,
        }


def test_discovery():
    registry = discover_v4_plugins()
    assert "builtin.sprint.delivery_forecast" in registry.plugin_ids


def test_proven_answer_only():
    result = asyncio.run(build_sprint_delivery_forecast(
        SimpleNamespace(adapter=Adapter()))({"sprint_id": "PRD-SPRNT-1"}))
    assert result.data["forecast_completion_percent"] == 72.5
    assert result.data["committed_predictability"] is None
    assert "closed_at_by_task" not in result.data


def test_missing_adapter_fails_closed():
    with pytest.raises(V4CapabilityUnavailable):
        asyncio.run(build_sprint_delivery_forecast(
            SimpleNamespace(adapter=object()))({"sprint_id": "PRD-SPRNT-1"}))
