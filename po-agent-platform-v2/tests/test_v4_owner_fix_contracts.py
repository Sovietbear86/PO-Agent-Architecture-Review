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
from po_agent.harness.agent_core_v4 import CapabilitySpecV4, SkillSpecV4, V4NeedsClarification
from po_agent.harness.contracts import CapabilityResult
from po_agent.harness.v4_plugins._task_live_handlers import build_task_search_assignee


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


class _AssigneeAdapterStub:
    def __init__(self):
        self.queries = []

    async def search_tasks(self, query, max_results=10000):
        self.queries.append((query, max_results))
        return []


class _AssigneeRuntimeStub:
    def __init__(self, resolved="External.Person"):
        self.adapter = _AssigneeAdapterStub()
        self.resolved = resolved
        self.resolve_calls = []

    async def _member_resolve(self, args):
        self.resolve_calls.append(dict(args))
        return CapabilityResult(
            answer=f"Пользователь подтверждён: {self.resolved}.",
            data={"external_id": self.resolved, "member_login": self.resolved, "source": "REAL_AS21"},
        )


@pytest.mark.asyncio
async def test_assignee_plugin_uses_generic_member_resolver_for_non_team_person():
    runtime = _AssigneeRuntimeStub(resolved="External.Person")
    handler = build_task_search_assignee(runtime)

    result = await handler({"reference": "Внешний Пользователь", "space": "DMS"})

    assert runtime.resolve_calls == [{"reference": "Внешний Пользователь", "space": "DMS"}]
    assert runtime.adapter.queries == [('assignee = "External.Person" AND project = "DMS"', 10000)]
    assert result.data["source_reference"] == "External.Person"
    assert result.data["member_login"] == "External.Person"


@pytest.mark.asyncio
async def test_assignee_plugin_does_not_treat_team_directory_as_population_boundary():
    runtime = _AssigneeRuntimeStub(resolved="Any.Source.Identity")
    # No team/roster object exists on this runtime at all. The handler must still
    # resolve through the governed source identity contract rather than fail early.
    handler = build_task_search_assignee(runtime)

    result = await handler({"reference": "Любой Человек"})

    assert runtime.resolve_calls == [{"reference": "Любой Человек"}]
    assert runtime.adapter.queries == [('assignee = "Any.Source.Identity"', 10000)]
    assert result.data["count"] == 0


@pytest.mark.asyncio
async def test_assignee_plugin_propagates_identity_clarification_instead_of_source_error():
    class AmbiguousRuntime(_AssigneeRuntimeStub):
        async def _member_resolve(self, args):
            self.resolve_calls.append(dict(args))
            raise V4NeedsClarification(
                "Нашёл несколько пользователей. Уточните ФИО или login.",
                options=("person.one", "person.two"),
            )

    runtime = AmbiguousRuntime()
    handler = build_task_search_assignee(runtime)

    with pytest.raises(V4NeedsClarification) as exc:
        await handler({"reference": "Неоднозначная Фамилия"})

    assert exc.value.options == ("person.one", "person.two")
    assert runtime.adapter.queries == []


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
