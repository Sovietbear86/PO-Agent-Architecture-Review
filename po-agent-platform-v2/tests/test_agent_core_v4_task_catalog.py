from __future__ import annotations

import asyncio

from po_agent.harness.agent_core_v4 import SkillCatalogV4
from po_agent.harness.v4_plugin_registry import V4PluginRegistry, discover_v4_plugins
from po_agent.harness.v4_plugins.task_catalog import CANONICAL_TASK_SKILL_IDS, PLUGIN


A191_CANONICAL_TASK_SKILLS = {
    "task.lookup",          # #1
    "task.summary",         # #11
    "task.quality",         # #12
    "task.acceptance",      # #14
    "task.blockers",        # #19
}

EXPECTED_WAVE_T_SKILLS = {
    "task.search_text",             # #2
    "task.search_attachments",      # #3
    "task.search_excel",            # #4
    "task.search_pdf",              # #5
    "task.search_msg",              # #6
    "task.search_assignee",         # #7
    "task.search_status",           # #8
    "task.search_sprint",           # #9
    "task.search_release",          # #10
    "task.missing_requirements",    # #13
    "task.dependencies",            # #15
    "task.history",                 # #16
    "task.time_in_status",          # #17
    "task.aging",                   # #18
    "task.similar",                 # #20
}


class _LegacyRuntimeStub:
    def _legacy(self, capability_id):
        async def handler(arguments):
            return {"legacy_capability_id": capability_id, "arguments": arguments}
        return handler

    def __getattr__(self, name):
        if name.startswith("_"):
            async def handler(arguments):
                return {"handler_method": name, "arguments": arguments}
            return handler
        raise AttributeError(name)


def test_task_wave_plugin_is_discovered_without_core_edit():
    registry = discover_v4_plugins()
    assert "builtin.catalog.tasks" in registry.plugin_ids
    assert set(CANONICAL_TASK_SKILL_IDS) == EXPECTED_WAVE_T_SKILLS
    skill_ids = {skill.id for skill in registry.skills()}
    assert EXPECTED_WAVE_T_SKILLS <= skill_ids


def test_task_wave_plus_a191_represents_all_twenty_canonical_task_rows():
    registry = discover_v4_plugins()
    skill_ids = {skill.id for skill in registry.skills()}
    canonical = A191_CANONICAL_TASK_SKILLS | EXPECTED_WAVE_T_SKILLS
    assert len(canonical) == 20
    assert canonical <= skill_ids


def test_task_wave_capabilities_bind_only_through_registry_contract():
    # Canonical task skills may be composite: skill ids are not handler ids.
    # Validate that every capability referenced by every Wave-T skill is bound
    # by the complete registry.
    registry = discover_v4_plugins()
    handlers = registry.bind_handlers(_LegacyRuntimeStub())
    by_id = {skill.id: skill for skill in registry.skills()}
    referenced = {
        capability_id
        for skill_id in EXPECTED_WAVE_T_SKILLS
        for capability_id in by_id[skill_id].capabilities
    }
    assert referenced <= set(handlers)
    assert all(callable(handlers[capability_id]) for capability_id in referenced)


def test_specialized_attachment_bindings_enforce_fixed_type():
    by_id = {binding.capability_id: binding for binding in PLUGIN.bindings}
    assert by_id["task.search_excel"].fixed_arguments["attachment_type"] == "excel"
    assert by_id["task.search_pdf"].fixed_arguments["attachment_type"] == "pdf"
    assert by_id["task.search_msg"].fixed_arguments["attachment_type"] == "msg"
    assert by_id["task.search_excel"].handler_builder is not None
    assert by_id["task.search_pdf"].handler_builder is not None
    assert by_id["task.search_msg"].handler_builder is not None


def test_task_wave_progressive_catalog_exposes_procedure_and_typed_capabilities():
    registry = discover_v4_plugins()
    catalog = SkillCatalogV4(registry.skills(), registry.capability_specs())
    compact_ids = {item["id"] for item in catalog.compact()}
    assert EXPECTED_WAVE_T_SKILLS <= compact_ids

    release = catalog.load("task.search_release")
    assert [capability["id"] for capability in release["capabilities"]] == [
        "release.resolve",
        "task.search_release",
    ]
    assert release["procedure"]

    assignee = catalog.load("task.search_assignee")
    assert [capability["id"] for capability in assignee["capabilities"]] == [
        "task.search_assignee",
    ]
    assignee_args = assignee["capabilities"][0]["arguments"]
    assert "status" in assignee_args
    assert "never drop that constraint" in " ".join(assignee["procedure"])

    assert [capability["id"] for capability in catalog.load("task.search_excel")["capabilities"]] == ["task.search_excel"]


def test_task_wave_completion_contracts_are_declared_not_runtime_hardcoded():
    by_id = {skill.id: skill for skill in discover_v4_plugins().skills()}
    for skill_id in EXPECTED_WAVE_T_SKILLS:
        assert by_id[skill_id].completion, f"missing completion contract: {skill_id}"

    assert by_id["task.search_assignee"].completion[0].covers_resolved_constraints is False
    assert by_id["task.search_sprint"].completion[0].covers_resolved_constraints is True
    assert by_id["task.search_release"].completion[0].covers_resolved_constraints is True


def test_specialized_attachment_skills_use_narrow_typed_capabilities():
    by_id = {skill.id: skill for skill in discover_v4_plugins().skills()}
    assert by_id["task.search_attachments"].capabilities == ("task.search_attachments",)
    assert by_id["task.search_excel"].capabilities == ("task.search_excel",)
    assert by_id["task.search_pdf"].capabilities == ("task.search_pdf",)
    assert by_id["task.search_msg"].capabilities == ("task.search_msg",)
    assert "attachment_type=excel" in " ".join(by_id["task.search_excel"].procedure)
    assert "attachment_type=pdf" in " ".join(by_id["task.search_pdf"].procedure)
    assert "attachment_type=msg" in " ".join(by_id["task.search_msg"].procedure)


def test_task_wave_ui_contracts_cover_every_new_canonical_skill():
    ui = discover_v4_plugins().ui_contracts()
    assert EXPECTED_WAVE_T_SKILLS <= set(ui)
    assert ui["task.search_text"].preferred_widget == "task_table"
    assert ui["task.search_attachments"].preferred_widget == "attachment_table"
    assert ui["task.history"].preferred_widget == "task_history"
    assert ui["task.time_in_status"].preferred_widget == "task_status_timeline"
    assert ui["task.similar"].preferred_widget == "similar_task_list"


def test_task_wave_source_conditional_history_skills_are_not_faked():
    by_id = {skill.id: skill for skill in discover_v4_plugins().skills()}
    assert "source history is unavailable" in " ".join(by_id["task.history"].procedure)
    assert "source timestamps" in " ".join(by_id["task.time_in_status"].procedure)
