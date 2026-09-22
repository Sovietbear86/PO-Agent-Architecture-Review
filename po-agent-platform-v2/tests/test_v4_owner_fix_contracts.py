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
from po_agent.adapters.task_api import AS21SourceUnavailable
from po_agent.harness.agent_core_v4 import CapabilitySpecV4, SkillSpecV4, V4NeedsClarification
from po_agent.harness.contracts import CapabilityResult
from po_agent.harness.v4_plugins._task_live_handlers import (
    build_task_aging,
    build_task_search_assignee,
    build_task_search_attachments,
    build_task_search_status,
    build_task_search_text,
    build_task_similar,
)


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

    effective, early, continuation = _prepare_query(
        QueryRequest(
            query="DMS",
            session_id=session_id,
            clarification_id=clarification_id,
            clarification_option="DMS",
        ),
        session_id,
    )
    assert early is None
    assert continuation.loaded_skills == ()
    assert continuation.observations == ()
    assert continuation.required_completion_skills == ()
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
    assert continuation.loaded_skills == ()
    assert continuation.observations == ()
    assert continuation.required_completion_skills == ()
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
    assert continuation.loaded_skills == ()
    assert continuation.observations == ()
    assert continuation.required_completion_skills == ()
    assert early["status"] == "NEEDS_CLARIFICATION"
    assert early["options"] == ["DMS", "WMB"]
    assert early["warnings"] == ["invalid_clarification_option"]


class _LiveTaskAdapterStub:
    def __init__(self, rows):
        self.rows = rows
        self.attachment_calls = 0

    async def _get_resilient(self, path, params=None):
        assert path == "/api/v1/swtr-read/task-query"
        space = (params or {}).get("space")
        phrase = (params or {}).get("phrase")
        rows = list(self.rows)
        if space:
            rows = [row for row in rows if row.get("source_data", {}).get("swtr_space") == space]
        if phrase:
            needle = str(phrase).casefold()
            rows = [row for row in rows if needle in str(row.get("source_id", "")).casefold() or needle in str(row.get("title", "")).casefold()]
        return type("Response", (), {"json": lambda self: {"tasks": rows}})()

    @staticmethod
    def _map(row):
        return row.get("_task")

    async def get_attachment_metadata(self, task_key):
        self.attachment_calls += 1
        return []


def _task_stub(key, *, space="DMS", age_days=10, is_open=True, title=None, description=""):
    status = type("Status", (), {"value": "Open"})()
    status_category = type("StatusCategory", (), {"value": "in_progress"})()
    priority = type("Priority", (), {"value": "medium"})()
    task = type("Task", (), {})()
    task.key = key
    task.id = key
    task.title = title or key
    task.description = description
    task.status = status
    task.status_category = status_category
    task.assignee = None
    task.assignee_id = None
    task.assignee_login = None
    task.priority = priority
    task.project_space = space
    task.sprint_id = None
    task.release_id = None
    task.source = "swtr"
    task.source_data = {"swtr_space": space, "_canonical_created_at_from_source": True}
    task.attachments = []
    task.age_days = age_days
    task.is_open = is_open
    return task


def _live_row(task):
    return {
        "source_id": task.key,
        "title": task.title,
        "description": task.description,
        "source_data": {"swtr_space": task.project_space},
        "_task": task,
    }


@pytest.mark.asyncio
async def test_aging_uses_bounded_live_space_collection():
    rows = [_live_row(_task_stub("DMS-1", age_days=12)), _live_row(_task_stub("WMB-1", space="WMB", age_days=30))]
    runtime = type("Runtime", (), {"adapter": _LiveTaskAdapterStub(rows)})()
    result = await build_task_aging(runtime)({"space": "DMS", "threshold_days": "7"})
    assert result.data["count"] == 1
    assert [item["key"] for item in result.data["tasks"]] == ["DMS-1"]


@pytest.mark.asyncio
async def test_aging_fails_closed_without_bounded_scope():
    runtime = type("Runtime", (), {"adapter": _LiveTaskAdapterStub([])})()
    with pytest.raises(AS21SourceUnavailable):
        await build_task_aging(runtime)({"threshold_days": "7"})


@pytest.mark.asyncio
async def test_similar_limits_candidate_corpus_to_source_task_space():
    source = _task_stub("DMS-380", title="OAuth auth", description="login token")
    near = _task_stub("DMS-381", title="OAuth token", description="login")
    other = _task_stub("WMB-1", space="WMB", title="OAuth token", description="login")
    runtime = type("Runtime", (), {"adapter": _LiveTaskAdapterStub([_live_row(source), _live_row(near), _live_row(other)])})()
    result = await build_task_similar(runtime)({"task_key": "DMS-380"})
    assert [item["key"] for item in result.data["matches"]] == ["DMS-381"]
    assert result.data["space"] == "DMS"


@pytest.mark.asyncio
async def test_attachment_search_fails_closed_before_unbounded_n_plus_one():
    tasks = [_task_stub(f"WMB-{i}", space="WMB") for i in range(1, 252)]
    adapter = _LiveTaskAdapterStub([_live_row(task) for task in tasks])
    runtime = type("Runtime", (), {"adapter": adapter})()
    with pytest.raises(AS21SourceUnavailable):
        await build_task_search_attachments(runtime)({"space": "WMB", "attachment_type": "excel"})
    assert adapter.attachment_calls == 0


@pytest.mark.asyncio
async def test_aging_rejects_adapter_fallback_timestamps():
    task = _task_stub("DMS-2", age_days=0)
    task.source_data["_canonical_created_at_from_source"] = False
    runtime = type("Runtime", (), {"adapter": _LiveTaskAdapterStub([_live_row(task)])})()
    with pytest.raises(AS21SourceUnavailable):
        await build_task_aging(runtime)({"space": "DMS", "threshold_days": "7"})


@pytest.mark.asyncio
async def test_person_scoped_attachment_search_uses_generic_member_resolver():
    class AttachmentRuntime:
        def __init__(self):
            self.resolve_calls = []
            task = _task_stub("WMB-30000", space="WMB")
            self.adapter = _LiveTaskAdapterStub([_live_row(task)])

        async def _member_resolve(self, args):
            self.resolve_calls.append(dict(args))
            return CapabilityResult(
                answer="Пользователь подтверждён: Kalachanov.V.V.",
                data={
                    "external_id": "Kalachanov.V.V",
                    "member_login": "Kalachanov.V.V",
                    "source": "REAL_AS21",
                },
            )

    runtime = AttachmentRuntime()
    handler = build_task_search_attachments(runtime)
    result = await handler({"reference": "Калачанов", "space": "WMB"})

    assert runtime.resolve_calls == [{"reference": "Калачанов", "space": "WMB"}]
    assert result.data["assignee"] == "Калачанов"
    assert result.data["source_assignee"] == "Kalachanov.V.V"


class _PersonScopedRuntime:
    def __init__(self, rows=None, resolved="Kalachanov.V.V"):
        self.resolve_calls = []
        self.resolved = resolved
        self.adapter = _LiveTaskAdapterStub(rows or [])

    async def _member_resolve(self, args):
        self.resolve_calls.append(dict(args))
        return CapabilityResult(
            answer=f"Пользователь подтверждён: {self.resolved}.",
            data={
                "external_id": self.resolved,
                "member_login": self.resolved,
                "source": "REAL_AS21",
            },
        )


@pytest.mark.asyncio
async def test_person_scoped_text_search_uses_generic_member_resolver():
    task = _task_stub("WMB-30000", space="WMB", title="Нужная фраза")
    runtime = _PersonScopedRuntime([_live_row(task)])
    result = await build_task_search_text(runtime)({
        "phrase": "Нужная",
        "reference": "Калачанов",
        "space": "WMB",
    })
    assert runtime.resolve_calls == [{"reference": "Калачанов", "space": "WMB"}]
    assert result.data["source_assignee"] == "Kalachanov.V.V"


@pytest.mark.asyncio
async def test_person_scoped_status_search_uses_generic_member_resolver():
    task = _task_stub("WMB-30000", space="WMB")
    runtime = _PersonScopedRuntime([_live_row(task)])
    result = await build_task_search_status(runtime)({
        "status": "open",
        "reference": "Калачанов",
        "space": "WMB",
    })
    assert runtime.resolve_calls == [{"reference": "Калачанов", "space": "WMB"}]
    assert result.data["source_assignee"] == "Kalachanov.V.V"


@pytest.mark.asyncio
async def test_person_scoped_aging_uses_generic_member_resolver():
    task = _task_stub("WMB-30000", space="WMB", age_days=12)
    runtime = _PersonScopedRuntime([_live_row(task)])
    result = await build_task_aging(runtime)({
        "threshold_days": "7",
        "reference": "Калачанов",
        "space": "WMB",
    })
    assert runtime.resolve_calls == [{"reference": "Калачанов", "space": "WMB"}]
    assert result.data["source_assignee"] == "Kalachanov.V.V"
