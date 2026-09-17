from __future__ import annotations

import pytest

from po_agent.api.v1 import (
    QueryRequest,
    _pending_clarifications,
    _prepare_query,
    _remember_clarification,
)
from po_agent.harness.v4_plugin_registry import (
    CapabilityBindingV4,
    V4PluginError,
    V4PluginRegistry,
    V4SkillPlugin,
)
from po_agent.harness.agent_core_v4 import CapabilitySpecV4, SkillSpecV4
from po_agent.harness.v4_plugins._task_live_handlers import _authorized_identity_hint


@pytest.fixture(autouse=True)
def clear_pending_clarifications():
    _pending_clarifications.clear()
    yield
    _pending_clarifications.clear()


def _builder_plugin(builder):
    return V4SkillPlugin(
        plugin_id="test.builder",
        skills=(SkillSpecV4("test.skill", "x", ("x",), ("test.cap",)),),
        capabilities=(CapabilitySpecV4("test.cap", "x", {}),),
        bindings=(CapabilityBindingV4("test.cap", handler_builder=builder),),
    )


@pytest.mark.asyncio
async def test_handler_builder_binds_without_agent_core_method():
    async def built(arguments):
        return {"ok": arguments.get("value")}

    def builder(runtime):
        assert runtime.marker == "runtime"
        return built

    runtime = type("RuntimeStub", (), {"marker": "runtime"})()
    handlers = V4PluginRegistry((_builder_plugin(builder),)).bind_handlers(runtime)
    assert await handlers["test.cap"]({"value": "yes"}) == {"ok": "yes"}


def test_handler_builder_is_mutually_exclusive_with_core_or_legacy_binding():
    def builder(runtime):
        return lambda arguments: arguments

    plugin = V4SkillPlugin(
        plugin_id="test.bad-builder",
        skills=(SkillSpecV4("test.skill", "x", ("x",), ("test.cap",)),),
        capabilities=(CapabilitySpecV4("test.cap", "x", {}),),
        bindings=(CapabilityBindingV4("test.cap", handler_method="_x", handler_builder=builder),),
    )
    with pytest.raises(V4PluginError, match="exactly one handler binding"):
        V4PluginRegistry((plugin,))


def test_authorized_identity_hint_is_generic_unique_roster_bridge_only():
    entry = type("Entry", (), {"login": "Canonical.Login"})()
    team = type("Team", (), {"resolve_person": lambda self, reference: (entry,) if reference == "Natural Name" else ()})()
    runtime = type("Runtime", (), {"team": team})()

    assert _authorized_identity_hint(runtime, "Natural Name") == "Canonical.Login"
    assert _authorized_identity_hint(runtime, "Unknown Person") == "Unknown Person"


def test_authorized_identity_hint_does_not_guess_on_ambiguity():
    first = type("Entry", (), {"login": "first"})()
    second = type("Entry", (), {"login": "second"})()
    team = type("Team", (), {"resolve_person": lambda self, reference: (first, second)})()
    runtime = type("Runtime", (), {"team": team})()

    assert _authorized_identity_hint(runtime, "Ambiguous Name") == "Ambiguous Name"


def test_clarification_continuation_restores_original_query_and_option():
    session_id = "ui-session-1"
    first = {
        "status": "NEEDS_CLARIFICATION",
        "question": "Укажите пространство.",
        "options": ["CRPV", "DMS", "OLP", "STS", "WMB"],
        "clarification_id": None,
    }
    remembered = _remember_clarification(
        first,
        session_id,
        "задачи Гаранина в сентябрьском спринте",
    )
    clarification_id = remembered["clarification_id"]
    assert clarification_id

    effective, early = _prepare_query(
        QueryRequest(
            query="DMS",
            session_id=session_id,
            clarification_id=clarification_id,
            clarification_option="DMS",
        ),
        session_id,
    )
    assert early is None
    assert "задачи Гаранина в сентябрьском спринте" in effective
    assert "Ответ пользователя на уточнение: DMS" in effective
    assert "Не трактуй ответ на уточнение как новый отдельный запрос" in effective
    assert session_id not in _pending_clarifications


def test_clarification_is_session_bound_and_fails_closed_in_russian():
    first = {
        "status": "NEEDS_CLARIFICATION",
        "question": "Укажите пространство.",
        "options": ["DMS"],
        "clarification_id": None,
    }
    remembered = _remember_clarification(first, "session-a", "исходный запрос")
    effective, early = _prepare_query(
        QueryRequest(
            query="DMS",
            session_id="session-b",
            clarification_id=remembered["clarification_id"],
            clarification_option="DMS",
        ),
        "session-b",
    )
    assert effective is None
    assert early["status"] == "NEEDS_CLARIFICATION"
    assert "Контекст предыдущего уточнения" in early["question"]
    assert early["warnings"] == ["clarification_context_lost"]


def test_invalid_clarification_option_does_not_replan_as_standalone_query():
    first = {
        "status": "NEEDS_CLARIFICATION",
        "question": "Укажите пространство.",
        "options": ["DMS", "WMB"],
        "clarification_id": None,
    }
    remembered = _remember_clarification(first, "session-a", "исходный запрос")
    effective, early = _prepare_query(
        QueryRequest(
            query="UNKNOWN",
            session_id="session-a",
            clarification_id=remembered["clarification_id"],
            clarification_option="UNKNOWN",
        ),
        "session-a",
    )
    assert effective is None
    assert early["status"] == "NEEDS_CLARIFICATION"
    assert early["options"] == ["DMS", "WMB"]
    assert early["warnings"] == ["invalid_clarification_option"]
