import pytest

from po_agent.adapters import FakeAS21Adapter, TaskApiAS21Adapter
from po_agent.harness.runtime_factory import build_runtime_bundle


def test_runtime_factory_defaults_to_fake_source():
    bundle = build_runtime_bundle()
    assert bundle.mode == "fake"
    assert isinstance(bundle.adapter, FakeAS21Adapter)
    assert bundle.readiness.source == "fake-as21"
    assert bundle.readiness.by_skill()["task-history"].status == "ready"


def test_runtime_factory_builds_task_api_source():
    bundle = build_runtime_bundle("task-api", task_api_base_url="http://task-api:8003")
    assert bundle.mode == "task-api"
    assert isinstance(bundle.adapter, TaskApiAS21Adapter)
    assert bundle.adapter.base_url == "http://task-api:8003"
    assert bundle.readiness.source == "task-api"
    assert bundle.readiness.by_skill()["task-history"].status == "unavailable"


def test_runtime_factory_accepts_real_alias_but_normalizes_mode():
    bundle = build_runtime_bundle("real")
    assert bundle.mode == "task-api"


def test_runtime_factory_rejects_unknown_mode():
    with pytest.raises(ValueError, match="Unsupported PO_AGENT_AS21_MODE"):
        build_runtime_bundle("magic")
