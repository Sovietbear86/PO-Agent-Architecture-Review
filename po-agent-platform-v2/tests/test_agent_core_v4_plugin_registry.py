from __future__ import annotations

import inspect
import types

import pytest

from po_agent.harness.agent_core_v4 import AgentCoreV4Runtime, CapabilitySpecV4, SkillCatalogV4, SkillSpecV4
from po_agent.harness.agent_core_v4_completion import CompletionRequirement, SkillCompletionContract
from po_agent.harness.agent_core_v4_reliable import ReliableAgentCoreV4Runtime
from po_agent.harness.agent_core_v4_robust import RobustReliableAgentCoreV4Runtime, RobustSkillNativePlannerV4
from po_agent.harness.agent_core_v4_pluginized import PluginizedRobustReliableAgentCoreV4Runtime
from po_agent.harness.v4_plugin_registry import (
    CapabilityBindingV4,
    UIContractV4,
    V4PluginError,
    V4PluginRegistry,
    V4SkillPlugin,
    discover_v4_plugins,
)


class _RuntimeStub:
    async def _dummy_handler(self, arguments):
        return arguments

    def _legacy(self, capability_id):
        async def handler(arguments):
            return {"legacy": capability_id, **arguments}
        return handler


def _dummy_plugin(plugin_id: str = "test.dummy55", skill_id: str = "dummy.55") -> V4SkillPlugin:
    capability_id = f"{skill_id}.execute"
    return V4SkillPlugin(
        plugin_id=plugin_id,
        skills=(
            SkillSpecV4(
                skill_id,
                "Synthetic 55th-style skill used only to prove the extension surface.",
                ("Call the registered dummy capability.",),
                (capability_id,),
                completion=(CompletionRequirement(capability_id, data_keys=("ok",)),),
            ),
        ),
        capabilities=(
            CapabilitySpecV4(capability_id, "Synthetic typed capability.", {"value": "required"}),
        ),
        bindings=(CapabilityBindingV4(capability_id, handler_method="_dummy_handler"),),
        ui={
            skill_id: UIContractV4(
                "dummy_result",
                preferred_widget="dummy_widget",
                required_fields=("ok",),
            )
        },
    )


def test_builtin_plugins_discover_deterministically():
    registry = discover_v4_plugins()
    assert registry.plugin_ids == tuple(sorted(registry.plugin_ids))
    assert "builtin.core.a188" in registry.plugin_ids
    assert "builtin.catalog.tasks" in registry.plugin_ids
    skill_ids = tuple(skill.id for skill in registry.skills())
    assert skill_ids == tuple(sorted(skill_ids))
    assert "tasks.search" in skill_ids
    assert "tasks.lookup_then_assignee" in skill_ids
    assert "sprints.list" in skill_ids
    assert "task.lookup" in skill_ids
    assert "task.search_text" in skill_ids


def test_builtin_registry_has_complete_handler_bindings():
    registry = discover_v4_plugins()
    specs = registry.capability_specs()
    # The A190 baseline had 15 capabilities. The catalog is intentionally
    # extensible, so the assertion protects the baseline instead of freezing the
    # registry size and blocking every future plugin wave.
    assert len(specs) >= 15
    assert {
        "member.resolve",
        "task.search",
        "task.lookup",
        "sprint.current",
        "task.search_text",
        "task.search_attachments",
    } <= set(specs)


def test_dummy_55_can_be_added_without_agent_core_change():
    before = discover_v4_plugins()
    dummy = _dummy_plugin()
    after = before.with_plugin(dummy)

    # Registry -> compact catalog -> detailed skill contract.
    catalog = SkillCatalogV4(after.skills(), after.capability_specs())
    assert "dummy.55" in {item["id"] for item in catalog.compact()}
    detail = catalog.load("dummy.55")
    assert detail["id"] == "dummy.55"
    assert [item["id"] for item in detail["capabilities"]] == ["dummy.55.execute"]

    # Handler resolution is an independent plugin contract. Bind only the
    # synthetic extension so this minimal stub is not required to implement
    # the built-in A188 production handler surface.
    handlers = V4PluginRegistry((dummy,)).bind_handlers(_RuntimeStub())
    assert callable(handlers["dummy.55.execute"])

    # Registry -> deterministic completion contract declaration.
    dummy_skill = next(skill for skill in after.skills() if skill.id == "dummy.55")
    assert dummy_skill.completion == (
        CompletionRequirement("dummy.55.execute", data_keys=("ok",)),
    )
    completion = SkillCompletionContract(dummy_skill.id, dummy_skill.completion)
    assert completion.skill_id == "dummy.55"

    # Registry -> presentation metadata, with no Agent Core source edit.
    assert after.ui_contracts()["dummy.55"].preferred_widget == "dummy_widget"
    assert after.ui_contracts()["dummy.55"].required_fields == ("ok",)


def test_duplicate_skill_fails_closed():
    first = _dummy_plugin("test.one", "dummy.same")
    second = V4SkillPlugin(
        plugin_id="test.two",
        skills=(
            SkillSpecV4(
                "dummy.same",
                "second skill with duplicate id",
                ("Call the second capability.",),
                ("dummy.second.execute",),
            ),
        ),
        capabilities=(
            CapabilitySpecV4("dummy.second.execute", "Synthetic typed capability.", {}),
        ),
        bindings=(
            CapabilityBindingV4("dummy.second.execute", handler_method="_dummy_handler"),
        ),
    )
    with pytest.raises(V4PluginError, match="duplicate skill id"):
        V4PluginRegistry((first, second))


def test_duplicate_capability_fails_closed():
    first = _dummy_plugin("test.one", "dummy.one")
    second_original = _dummy_plugin("test.two", "dummy.two")
    second = V4SkillPlugin(
        plugin_id=second_original.plugin_id,
        skills=second_original.skills,
        capabilities=(first.capabilities[0],),
        bindings=(first.bindings[0],),
        ui=second_original.ui,
    )
    with pytest.raises(V4PluginError, match="duplicate capability id"):
        V4PluginRegistry((first, second))


def test_missing_handler_fails_closed():
    plugin = V4SkillPlugin(
        plugin_id="test.missing-handler",
        skills=(SkillSpecV4("dummy.missing", "x", ("x",), ("dummy.missing.execute",)),),
        capabilities=(CapabilitySpecV4("dummy.missing.execute", "x", {}),),
        bindings=(CapabilityBindingV4("dummy.missing.execute", handler_method="_does_not_exist"),),
    )
    registry = V4PluginRegistry((plugin,))
    with pytest.raises(V4PluginError, match="handler is unavailable"):
        registry.bind_handlers(_RuntimeStub())


def test_binding_schema_fails_closed():
    plugin = V4SkillPlugin(
        plugin_id="test.bad-binding",
        skills=(SkillSpecV4("dummy.bad", "x", ("x",), ("dummy.bad.execute",)),),
        capabilities=(CapabilitySpecV4("dummy.bad.execute", "x", {}),),
        bindings=(
            CapabilityBindingV4(
                "dummy.bad.execute",
                handler_method="_dummy_handler",
                legacy_capability_id="also.invalid",
            ),
        ),
    )
    with pytest.raises(V4PluginError, match="exactly one handler binding"):
        V4PluginRegistry((plugin,))


def test_unknown_skill_capability_fails_closed():
    plugin = V4SkillPlugin(
        plugin_id="test.unknown-capability",
        skills=(SkillSpecV4("dummy.bad", "x", ("x",), ("missing.capability",)),),
        capabilities=(CapabilitySpecV4("other.capability", "x", {}),),
        bindings=(CapabilityBindingV4("other.capability", handler_method="_dummy_handler"),),
    )
    with pytest.raises(V4PluginError, match="references unknown capabilities"):
        V4PluginRegistry((plugin,))


def test_ui_contract_for_unknown_skill_fails_closed():
    plugin = _dummy_plugin()
    bad = V4SkillPlugin(
        plugin_id=plugin.plugin_id,
        skills=plugin.skills,
        capabilities=plugin.capabilities,
        bindings=plugin.bindings,
        ui={"not.a.skill": UIContractV4("bad")},
    )
    with pytest.raises(V4PluginError, match="UI contracts reference unknown skills"):
        V4PluginRegistry((bad,))


def test_discovery_rejects_untrusted_package():
    with pytest.raises(V4PluginError, match="untrusted V4 plugin package"):
        discover_v4_plugins("user.supplied.plugins")


def test_discovery_contract_rejects_module_without_typed_plugin(monkeypatch):
    import po_agent.harness.v4_plugin_registry as registry_module

    fake_info = types.SimpleNamespace(name="po_agent.harness.v4_plugins.fake")
    monkeypatch.setattr(registry_module.pkgutil, "iter_modules", lambda *args, **kwargs: [fake_info])
    real_import = registry_module.importlib.import_module

    def fake_import(name):
        if name == "po_agent.harness.v4_plugins.fake":
            return types.SimpleNamespace(__name__=name, PLUGIN=object())
        return real_import(name)

    monkeypatch.setattr(registry_module.importlib, "import_module", fake_import)
    with pytest.raises(V4PluginError, match="must export PLUGIN"):
        discover_v4_plugins()


def test_session_context_interface_parity_across_production_runtime_chain():
    """Cross-cutting Harness arguments must reach every production override.

    This is intentionally an interface-level contract: adding a new generic
    control-plane argument must not silently break one wrapper layer and turn
    all plugin capabilities RED before skill loading.
    """
    runtime_classes = (
        AgentCoreV4Runtime,
        ReliableAgentCoreV4Runtime,
        PluginizedRobustReliableAgentCoreV4Runtime,
    )
    for runtime_cls in runtime_classes:
        signature = inspect.signature(runtime_cls._validate_call_literals)
        assert "session_context" in signature.parameters, runtime_cls.__name__

    planner_signature = inspect.signature(RobustSkillNativePlannerV4.next_decision)
    assert "session_context" in planner_signature.parameters


def test_pluginized_literal_guard_forwards_session_context_to_base(monkeypatch):
    """A validated session entity must survive the pluginized overlay."""
    runtime = object.__new__(PluginizedRobustReliableAgentCoreV4Runtime)
    captured = {}

    def fake_super_guard(self, capability_id, args, query, observations, session_context=None):
        captured["capability_id"] = capability_id
        captured["args"] = dict(args)
        captured["query"] = query
        captured["session_context"] = dict(session_context or {})

    monkeypatch.setattr(ReliableAgentCoreV4Runtime, "_validate_call_literals", fake_super_guard)

    runtime._validate_call_literals(
        "task.search",
        {"sprint_id": "DMS-SPRNT-3", "status": "not_completed"},
        "покажи активные задачи в этом спринте",
        [],
        {"space": "DMS", "sprint_id": "DMS-SPRNT-3"},
    )

    assert captured["capability_id"] == "task.search"
    assert captured["args"]["sprint_id"] == "DMS-SPRNT-3"
    assert captured["session_context"] == {"space": "DMS", "sprint_id": "DMS-SPRNT-3"}
