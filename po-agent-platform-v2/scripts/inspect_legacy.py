#!/usr/bin/env python3
"""
Legacy Discovery Tool for PO Agent Platform v2.

This script analyzes the legacy project (s21-task-agent and task-api)
to identify components that can be reused for the new v2 implementation.

Usage:
    python inspect_legacy.py [--output-dir PATH]
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "task-api"))


class LegacyComponent:
    """Represents a legacy component for analysis."""

    def __init__(
        self,
        name: str,
        path: str,
        type_: str,
        responsibility: str,
        reuse: str,
        target_module: str,
        risks: list[str] | None = None,
        notes: str = "",
    ):
        self.name = name
        self.path = path
        self.type_ = type_
        self.responsibility = responsibility
        self.reuse = reuse  # YES, PARTIAL, NO
        self.target_module = target_module
        self.risks = risks or []
        self.notes = notes

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "path": self.path,
            "type": self.type_,
            "responsibility": self.responsibility,
            "reuse": self.reuse,
            "target_module": self.target_module,
            "risks": self.risks,
            "notes": self.notes,
        }


class LegacyInspector:
    """Inspects legacy project components."""

    def __init__(self, legacy_base: Path):
        self.legacy_base = legacy_base
        self.components: list[LegacyComponent] = []

    def inspect(self) -> list[LegacyComponent]:
        """Run full inspection."""
        self._inspect_swtr_client()
        self._inspect_mcp_servers()
        self._inspect_agent_components()
        self._inspect_metrics()
        self._inspect_workflow_config()
        self._inspect_team_config()
        self._inspect_api_routes()
        return self.components

    def _inspect_swtr_client(self) -> None:
        """Inspect SWTR client code."""
        swtr_client_path = self.legacy_base / "swtr_client.py"

        if swtr_client_path.exists():
            self.components.append(
                LegacyComponent(
                    name="SWTR Client",
                    path=str(swtr_client_path),
                    type_="transport",
                    responsibility="SWTR REST API client with personal access token",
                    reuse="YES",
                    target_module="adapters.swtr",
                    risks=[
                        "Bearer token authentication may not work (requires PLATFORM_SESSION cookie)",
                        "May need proxy/ SynGX integration",
                        "Transport-only code should be reused, not authentication",
                    ],
                    notes="Extract transport logic only. Do not copy authentication.",
                )
            )

    def _inspect_mcp_servers(self) -> None:
        """Inspect MCP server implementations."""
        mcp_servers = [
            ("s21_mcp_proxy.py", "stdio-to-http proxy for agent"),
            ("jira_mcp_server.py", "Jira MCP server"),
            ("mcp-swtr/mcp_server.py", "SWTR FastMCP server"),
        ]

        for filename, description in mcp_servers:
            path = self.legacy_base / filename
            if path.exists():
                target = (
                    "adapters.swtr"
                    if "swtr" in filename
                    else "adapters.jira" if "jira" in filename else "orchestration"
                )
                self.components.append(
                    LegacyComponent(
                        name=f"MCP Server - {filename}",
                        path=str(path),
                        type_="mcp",
                        responsibility=description,
                        reuse="PARTIAL",
                        target_module=target,
                        risks=[
                            "Old architecture may have overlapping responsibilities",
                            "Stdio-to-HTTP proxy is needed for new design",
                            "Multiple MCP servers caused conflicts in old design",
                        ],
                        notes="Reuse transport only. Avoid overlapping server architecture.",
                    )
                )

    def _inspect_agent_components(self) -> None:
        """Inspect agent components."""
        agent_path = self.legacy_base / "s21-task-agent"
        if agent_path.exists():
            self.components.append(
                LegacyComponent(
                    name="s21-task-agent",
                    path=str(agent_path),
                    type_="agent",
                    responsibility="Task search and analysis agent with skills",
                    reuse="PARTIAL",
                    target_module="orchestration",
                    risks=[
                        "Agent has direct LLM calls for all queries",
                        "Skill routing may need redesign",
                        "Many hardcoded employee names",
                    ],
                    notes="Reuse skill definitions, not agent implementation.",
                )
            )

        team_performance_path = self.legacy_base / "task-api" / "src" / "s21_team_performance"
        if team_performance_path.exists():
            self.components.append(
                LegacyComponent(
                    name="Team Performance Agent",
                    path=str(team_performance_path),
                    type_="metrics",
                    responsibility="Team performance analysis with skills",
                    reuse="PARTIAL",
                    target_module="metrics",
                    risks=[
                        "Metrics calculated by LLM instead of deterministic code",
                        "Duplicated repository access code",
                        "Multiple MCP server calls",
                    ],
                    notes="Extract deterministic formulas, not LLM logic.",
                )
            )

    def _inspect_metrics(self) -> None:
        """Inspect metrics calculations."""
        metrics_configs = [
            ("task-api/config/metrics.yaml", "metrics configuration"),
            ("task-api/config/thresholds.yaml", "thresholds configuration"),
        ]

        for path, description in metrics_configs:
            full_path = self.legacy_base / path
            if full_path.exists():
                self.components.append(
                    LegacyComponent(
                        name=f"Metrics Config - {path}",
                        path=str(full_path),
                        type_="config",
                        responsibility=description,
                        reuse="YES",
                        target_module="config",
                        risks=[],
                        notes="Configuration can be reused with minor modifications.",
                    )
                )

    def _inspect_workflow_config(self) -> None:
        """Inspect workflow configuration."""
        workflow_configs = [
            ("task-api/config/workflow_statuses.yaml", "workflow status mappings"),
            ("task-api/config/status_mapping.yaml", "status mapping"),
        ]

        for path, description in workflow_configs:
            full_path = self.legacy_base / path
            if full_path.exists():
                self.components.append(
                    LegacyComponent(
                        name=f"Workflow Config - {path}",
                        path=str(full_path),
                        type_="config",
                        responsibility=description,
                        reuse="YES",
                        target_module="config",
                        risks=[],
                        notes="Workflow configuration can be directly reused.",
                    )
                )

    def _inspect_team_config(self) -> None:
        """Inspect team configuration."""
        team_path = self.legacy_base / "task-api" / "config" / "team_members.yaml"
        if team_path.exists():
            self.components.append(
                LegacyComponent(
                    name="Team Members Config",
                    path=str(team_path),
                    type_="config",
                    responsibility="Team member definitions with competencies",
                    reuse="PARTIAL",
                    target_module="config",
                    risks=[
                        "Contains PII data (emails, full names)",
                        "May need to use placeholder/ example data",
                    ],
                    notes="Use as reference. Do not include PII in public repo.",
                )
            )

    def _inspect_api_routes(self) -> None:
        """Inspect API routes."""
        main_py = self.legacy_base / "task-api" / "main.py"
        if main_py.exists():
            self.components.append(
                LegacyComponent(
                    name="API Routes",
                    path=str(main_py),
                    type_="api",
                    responsibility="FastAPI routes and application entry",
                    reuse="PARTIAL",
                    target_module="api",
                    risks=[
                        "Old API may have overlapping endpoints",
                        "Direct agent calls in routes",
                        "No proper error handling pattern",
                    ],
                    notes="Reference only. Redesign API for v2.",
                )
            )

    def to_json(self) -> dict[str, Any]:
        """Convert all components to JSON-serializable dict."""
        return {
            "inspection_date": datetime.now().isoformat(),
            "legacy_base": str(self.legacy_base),
            "components": [c.to_dict() for c in self.components],
            "summary": {
                "total": len(self.components),
                "by_type": self._count_by_type(),
                "reuse_by_category": self._count_by_reuse(),
            },
        }

    def _count_by_type(self) -> dict[str, int]:
        """Count components by type."""
        counts: dict[str, int] = {}
        for c in self.components:
            counts[c.type_] = counts.get(c.type_, 0) + 1
        return counts

    def _count_by_reuse(self) -> dict[str, int]:
        """Count components by reuse decision."""
        counts: dict[str, int] = {}
        for c in self.components:
            counts[c.reuse] = counts.get(c.reuse, 0) + 1
        return counts


def generate_reuse_map(components: list[LegacyComponent]) -> str:
    """Generate LEGACY_REUSE_MAP.md content."""
    lines = [
        "# Legacy Reuse Map",
        "",
        "This document maps legacy components to their intended v2 destinations.",
        "",
        "## Legend",
        "",
        "- ✅ **YES** - Can be directly reused",
        "- ⚠️ **PARTIAL** - Requires modification",
        "- ❌ **NO** - Should not be reused (architectural issue)",
        "",
        "---",
        "",
    ]

    for component in components:
        reuse_symbol = {
            "YES": "✅",
            "PARTIAL": "⚠️",
            "NO": "❌",
        }.get(component.reuse, "❓")

        lines.extend(
            [
                f"## {reuse_symbol} {component.name}",
                "",
                f"**Path:** `{component.path}`",
                f"**Type:** {component.type_}",
                f"**Target Module:** `{component.target_module}`",
                "",
                f"**Responsibility:** {component.responsibility}",
                "",
                "**Reuse Decision:** " + component.reuse,
                "",
            ]
        )

        if component.risks:
            lines.append("**Risks:**")
            for risk in component.risks:
                lines.append(f"- {risk}")
            lines.append("")

        if component.notes:
            lines.append(f"**Notes:** {component.notes}")
            lines.append("")

    return "\n".join(lines)


def main():
    """Main entry point."""
    import os

    # Determine legacy base directory
    script_dir = Path(__file__).parent.resolve()
    # Go up 2 levels: scripts/ -> po-agent-platform-v2/ -> project root
    project_root = script_dir.parent.parent

    # Legacy is at project root level (task-api, s21-task-agent, etc.)
    legacy_base = project_root

    print(f"🔍 Inspecting legacy project at: {legacy_base}")
    print("=" * 60)

    inspector = LegacyInspector(legacy_base)
    components = inspector.inspect()

    print(f"\n📋 Found {len(components)} legacy components\n")

    # Print summary
    print("Summary:")
    for component in components:
        reuse_symbol = {
            "YES": "[YES]",
            "PARTIAL": "[PA]",
            "NO": "[NO]",
        }.get(component.reuse, "[?]")
        print(f"  {reuse_symbol} {component.name:40} -> {component.target_module}")

    # Save JSON report
    output_dir = project_root / "po-agent-platform-v2" / "docs" / "architecture"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "legacy_inspection.json"
    with open(json_path, "w") as f:
        json.dump(inspector.to_json(), f, indent=2)
    print(f"\n💾 JSON report saved to: {json_path}")

    # Generate and save reuse map
    reuse_map_path = output_dir / "LEGACY_REUSE_MAP.md"
    with open(reuse_map_path, "w") as f:
        f.write(generate_reuse_map(components))
    print(f"💾 Reuse map saved to: {reuse_map_path}")

    print("\n" + "=" * 60)
    print("✅ Legacy inspection complete!")


if __name__ == "__main__":
    main()
