from __future__ import annotations

import asyncio
from types import SimpleNamespace

from po_agent.harness.agent_core_v4 import SkillCatalogV4
from po_agent.harness.v4_plugin_registry import discover_v4_plugins
from po_agent.harness.v4_plugins.agent_help import build_agent_help


def _runtime():
    registry = discover_v4_plugins()
    catalog = SkillCatalogV4(registry.skills(), registry.capability_specs())
    return SimpleNamespace(catalog=catalog, plugin_ids=registry.plugin_ids), registry


def test_agent_help_plugin_is_registry_discovered():
    _runtime_obj, registry = _runtime()
    assert "builtin.agent.help" in registry.plugin_ids
    ids = {skill.id for skill in registry.skills()}
    assert "agent.help" in ids


def test_agent_help_catalog_is_live_registry_backed_and_complete():
    runtime, registry = _runtime()
    result = asyncio.run(build_agent_help(runtime)({"mode": "skills"}))

    expected_ids = [skill.id for skill in registry.skills()]
    actual_ids = [row["id"] for row in result.data["skills"]]

    assert result.data["mode"] == "skills"
    assert result.data["skill_count"] == len(expected_ids)
    assert actual_ids == expected_ids
    assert result.data["catalog_source"] == "LIVE_V4_SKILL_CATALOG"
    assert result.data["availability_semantics"] == "DECLARED_NOT_EQUAL_SOURCE_READY"
    assert result.data["plugin_count"] == len(registry.plugin_ids)
    assert "agent.help" in actual_ids
    assert "Наличие в каталоге означает" in result.answer


def test_agent_help_ping_is_source_free_and_concise():
    runtime, _registry = _runtime()
    result = asyncio.run(build_agent_help(runtime)({"mode": "ping"}))

    assert result.answer == "Да, я на связи."
    assert result.data == {
        "mode": "ping",
        "available": True,
        "source": "AGENT_RUNTIME",
    }


def test_agent_help_completion_and_ui_contract_are_minimal():
    _runtime_obj, registry = _runtime()
    skills = {skill.id: skill for skill in registry.skills()}
    req = skills["agent.help"].completion[0]
    assert req.capability_id == "agent.help"
    assert req.data_keys == ("mode",)

    ui = registry.ui_contracts()["agent.help"]
    assert ui.result_kind == "meta"
    assert ui.required_fields == ("mode",)
