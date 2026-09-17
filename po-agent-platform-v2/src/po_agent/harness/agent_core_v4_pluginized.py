"""Pluginized production overlay for the A188-certified V4 runtime.

The proven planner, source handlers, identity governance and deterministic
completion machinery remain unchanged. This overlay replaces registration with
the trusted plugin registry and contains only generic runtime seams required by
the pluginized production path.
"""
from __future__ import annotations

from typing import Any, Mapping

from .agent_core_v4 import SkillCatalogV4, V4ContractError, V4Observation
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

    def _validate_call_literals(
        self,
        capability_id: str,
        args: Mapping[str, str],
        query: str,
        observations: list[V4Observation],
    ) -> None:
        """Apply morphology-aware grounding to generic human ``reference`` args.

        A195B proved a generic production seam: plugin capabilities such as
        ``task.search_assignee`` expose a natural human argument named
        ``reference``. The reliable base runtime gave morphology-aware validation
        only to ``member.resolve.reference`` while routing every other reference
        through literal-substring grounding. As a result a safe planner
        normalization like ``Александра Жданова`` -> ``Александр Жданов`` was
        rejected before the source-backed handler could confirm the identity.

        The pluginized runtime treats ``reference`` consistently as a natural
        identity reference. The existing conservative person-normalization guard
        remains the admission check and REAL AS21 remains authoritative in the
        downstream capability handler. All other argument guards are delegated
        unchanged to the certified base runtime.
        """
        forwarded = dict(args)
        raw_reference = str(forwarded.get("reference") or "").strip()
        if raw_reference and not raw_reference.startswith("$obs.") and capability_id != "member.resolve":
            if not self._reference_is_safe_normalization(raw_reference, query):
                raise V4ContractError(
                    f"planner person reference is neither query-derived nor uniquely team-scoped: {raw_reference}"
                )
            # The reference has already passed the stricter morphology-aware
            # identity guard. Remove only this key before delegating so the base
            # generic literal branch cannot incorrectly re-apply substring-only
            # validation. Space/sprint/release/task/product guards remain intact.
            forwarded.pop("reference", None)

        super()._validate_call_literals(capability_id, forwarded, query, observations)

    @property
    def plugin_ids(self) -> tuple[str, ...]:
        return self._v4_plugin_registry.plugin_ids

    def ui_contract(self, skill_id: str) -> UIContractV4 | None:
        """Expose presentation metadata without coupling UI to orchestration core."""
        return self._ui_contracts.get(skill_id)

    def ui_contracts(self) -> dict[str, UIContractV4]:
        return dict(self._ui_contracts)
