"""Pluginized production overlay for the A188-certified V4 runtime.

The proven planner, source handlers, identity governance and deterministic
completion machinery remain unchanged. This overlay replaces only registration:
skill/capability declarations and handler lookup come from the trusted plugin
registry instead of the central runtime maps.
"""
from __future__ import annotations

from typing import Any

from .agent_core_v4 import SkillCatalogV4
from .agent_core_v4_robust import RobustReliableAgentCoreV4Runtime
from .v4_plugin_registry import UIContractV4, V4PluginRegistry, discover_v4_plugins


class PluginizedRobustReliableAgentCoreV4Runtime(RobustReliableAgentCoreV4Runtime):
    """A188 behavior with registry-driven skill/capability extension surface."""

    def __init__(self, *args: Any, plugin_registry: V4PluginRegistry | None = None, **kwargs: Any) -> None:
        # Build the certified runtime first so every lower-layer reliability/source
        # behavior is preserved. Registration is then replaced as one bounded seam.
        super().__init__(*args, **kwargs)

        registry = plugin_registry or discover_v4_plugins()
        capability_specs = registry.capability_specs()
        catalog = SkillCatalogV4(registry.skills(), capability_specs)
        handlers = registry.bind_handlers(self)

        # Atomic registration cutover: planner/runtime semantics are unchanged.
        self._v4_plugin_registry = registry
        self._capability_specs = capability_specs
        self.catalog = catalog
        self._skill_contracts = self._build_skill_contracts()
        self._handlers = handlers
        self._ui_contracts = registry.ui_contracts()

    @property
    def plugin_ids(self) -> tuple[str, ...]:
        return self._v4_plugin_registry.plugin_ids

    def ui_contract(self, skill_id: str) -> UIContractV4 | None:
        """Expose presentation metadata without coupling UI to orchestration core."""
        return self._ui_contracts.get(skill_id)

    def ui_contracts(self) -> dict[str, UIContractV4]:
        return dict(self._ui_contracts)
