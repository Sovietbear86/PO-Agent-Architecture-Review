"""Agent self-introspection and lightweight conversational help.

This plugin is intentionally source-free and registry-backed:
- skill catalog truth comes from the live V4 SkillCatalogV4 on the runtime;
- it never hardcodes the user-facing skill list;
- a simple presence/ping reply does not touch AS21;
- catalog presence is reported as declaration, not as proof of live source readiness.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from ..agent_core_v4 import CapabilitySpecV4, SkillSpecV4
from ..agent_core_v4_completion import CompletionRequirement
from ..contracts import CapabilityResult
from ..v4_plugin_registry import CapabilityBindingV4, UIContractV4, V4SkillPlugin


def _mode(args: dict[str, str]) -> str:
    value = str(args.get("mode") or "skills").strip().casefold()
    return "ping" if value in {"ping", "presence", "alive", "here"} else "skills"


def build_agent_help(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        mode = _mode(args)

        if mode == "ping":
            return CapabilityResult(
                answer="Да, я на связи.",
                data={
                    "mode": "ping",
                    "available": True,
                    "source": "AGENT_RUNTIME",
                },
                evidence=[],
            )

        catalog = getattr(runtime, "catalog", None)
        if catalog is None or not hasattr(catalog, "skills"):
            raise RuntimeError("V4 skill catalog is unavailable")

        skills = list(catalog.skills())
        rows = [
            {
                "id": skill.id,
                "summary": skill.summary,
                "family": skill.id.split(".", 1)[0] if "." in skill.id else "other",
                "runtime_autocomplete": bool(skill.runtime_autocomplete),
                "catalog_state": "DECLARED",
            }
            for skill in skills
        ]
        families = Counter(row["family"] for row in rows)
        plugin_ids = list(getattr(runtime, "plugin_ids", ()) or ())

        lines = [f"Поддерживаю {len(rows)} навыков:"]
        lines.extend(f"- {row['id']} — {row['summary']}" for row in rows)
        lines.append(
            "Наличие в каталоге означает, что навык объявлен в V4; "
            "доступность конкретного source-backed результата проверяется при выполнении."
        )

        return CapabilityResult(
            answer="\n".join(lines),
            data={
                "mode": "skills",
                "skill_count": len(rows),
                "skills": rows,
                "families": [
                    {"family": key, "count": families[key]}
                    for key in sorted(families)
                ],
                "plugin_count": len(plugin_ids),
                "plugin_ids": plugin_ids,
                "catalog_source": "LIVE_V4_SKILL_CATALOG",
                "availability_semantics": "DECLARED_NOT_EQUAL_SOURCE_READY",
            },
            evidence=[],
        )

    return execute


CAPABILITIES = (
    CapabilitySpecV4(
        "agent.help",
        "Answer lightweight presence/help requests or return the complete live V4 skill catalog without querying AS21.",
        {
            "mode": "optional: skills for full live catalog; ping for simple presence acknowledgement",
        },
    ),
)

SKILLS = (
    SkillSpecV4(
        "agent.help",
        "Answer meta questions about what the agent supports, show the complete live skill catalog, or acknowledge a simple presence check.",
        (
            "For requests like 'покажи полный список навыков', 'что ты умеешь', 'какие навыки поддерживаешь' call agent.help with mode=skills.",
            "For a simple conversational presence check like 'ты тут?' call agent.help with mode=ping.",
            "The skills response must come from the live runtime catalog; never reconstruct or hardcode the skill list.",
            "Do not call REAL AS21 for presence or catalog introspection.",
            "Do not claim that catalog presence proves live source readiness; source-backed availability is checked when that skill is executed.",
        ),
        ("agent.help",),
        completion=(
            CompletionRequirement("agent.help", data_keys=("mode",)),
        ),
    ),
)

BINDINGS = (
    CapabilityBindingV4("agent.help", handler_builder=build_agent_help),
)

UI = {
    "agent.help": UIContractV4(
        "meta",
        preferred_widget="skill_catalog",
        required_fields=("mode",),
    ),
}

PLUGIN = V4SkillPlugin(
    plugin_id="builtin.agent.help",
    skills=SKILLS,
    capabilities=CAPABILITIES,
    bindings=BINDINGS,
    ui=UI,
)
