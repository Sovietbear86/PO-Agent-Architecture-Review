"""Trusted plugin registry for the V4 skill-native runtime.

This module is deliberately outside Agent Core orchestration.  It owns declarative
skill/capability registration, handler binding and optional presentation metadata.
A new skill can be added through the trusted ``v4_plugins`` namespace without
changing planner/runtime trajectory code.
"""
from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass, field
from types import ModuleType
from typing import Any, Mapping

from .agent_core_v4 import CapabilityHandlerV4, CapabilitySpecV4, SkillSpecV4

TRUSTED_PLUGIN_PACKAGE = "po_agent.harness.v4_plugins"


class V4PluginError(RuntimeError):
    """Fail-closed plugin contract/discovery error."""


@dataclass(frozen=True)
class UIContractV4:
    """Presentation hint only; never controls source execution."""

    result_kind: str
    preferred_widget: str | None = None
    required_fields: tuple[str, ...] = ()
    states: tuple[str, ...] = (
        "LOADING",
        "SUCCESS_WITH_DATA",
        "REAL_EMPTY",
        "SOURCE_UNAVAILABLE",
        "ERROR",
    )

    def compact(self) -> dict[str, Any]:
        return {
            "result_kind": self.result_kind,
            "preferred_widget": self.preferred_widget,
            "required_fields": list(self.required_fields),
            "states": list(self.states),
        }


@dataclass(frozen=True)
class CapabilityBindingV4:
    """Declarative binding from capability id to an existing runtime handler."""

    capability_id: str
    handler_method: str | None = None
    legacy_capability_id: str | None = None

    def validate(self) -> None:
        if not self.capability_id.strip():
            raise V4PluginError("empty capability binding id")
        choices = int(bool(self.handler_method)) + int(bool(self.legacy_capability_id))
        if choices != 1:
            raise V4PluginError(
                f"capability {self.capability_id} must declare exactly one handler binding"
            )


@dataclass(frozen=True)
class V4SkillPlugin:
    """Stable plugin-facing contract.

    ``skills`` carry procedural/completion contracts, ``capabilities`` carry typed
    capability metadata, ``bindings`` attach them to already governed handlers,
    and ``ui`` carries optional frontend hints.
    """

    plugin_id: str
    skills: tuple[SkillSpecV4, ...]
    capabilities: tuple[CapabilitySpecV4, ...]
    bindings: tuple[CapabilityBindingV4, ...]
    ui: Mapping[str, UIContractV4] = field(default_factory=dict)


class V4PluginRegistry:
    """Deterministic, fail-closed registry for trusted V4 plugins."""

    def __init__(self, plugins: tuple[V4SkillPlugin, ...]) -> None:
        self._plugins = tuple(sorted(plugins, key=lambda item: item.plugin_id))
        self._skills: dict[str, SkillSpecV4] = {}
        self._capabilities: dict[str, CapabilitySpecV4] = {}
        self._bindings: dict[str, CapabilityBindingV4] = {}
        self._ui: dict[str, UIContractV4] = {}
        seen_plugins: set[str] = set()

        for plugin in self._plugins:
            if not plugin.plugin_id.strip():
                raise V4PluginError("plugin_id must be non-empty")
            if plugin.plugin_id in seen_plugins:
                raise V4PluginError(f"duplicate plugin id: {plugin.plugin_id}")
            seen_plugins.add(plugin.plugin_id)

            for capability in plugin.capabilities:
                if capability.id in self._capabilities:
                    raise V4PluginError(f"duplicate capability id: {capability.id}")
                self._capabilities[capability.id] = capability

            for binding in plugin.bindings:
                binding.validate()
                if binding.capability_id in self._bindings:
                    raise V4PluginError(f"duplicate capability binding: {binding.capability_id}")
                self._bindings[binding.capability_id] = binding

            for skill in plugin.skills:
                if skill.id in self._skills:
                    raise V4PluginError(f"duplicate skill id: {skill.id}")
                self._skills[skill.id] = skill

            for skill_id, contract in plugin.ui.items():
                if skill_id in self._ui:
                    raise V4PluginError(f"duplicate UI contract for skill: {skill_id}")
                self._ui[skill_id] = contract

        if set(self._bindings) != set(self._capabilities):
            missing = sorted(set(self._capabilities) - set(self._bindings))
            extra = sorted(set(self._bindings) - set(self._capabilities))
            raise V4PluginError(f"capability binding mismatch: missing={missing}, extra={extra}")

        for skill in self._skills.values():
            missing = sorted(set(skill.capabilities) - set(self._capabilities))
            if missing:
                raise V4PluginError(
                    f"skill {skill.id} references unknown capabilities: {missing}"
                )
        unknown_ui = sorted(set(self._ui) - set(self._skills))
        if unknown_ui:
            raise V4PluginError(f"UI contracts reference unknown skills: {unknown_ui}")

    @property
    def plugin_ids(self) -> tuple[str, ...]:
        return tuple(plugin.plugin_id for plugin in self._plugins)

    def skills(self) -> tuple[SkillSpecV4, ...]:
        return tuple(self._skills[key] for key in sorted(self._skills))

    def capability_specs(self) -> dict[str, CapabilitySpecV4]:
        return {key: self._capabilities[key] for key in sorted(self._capabilities)}

    def ui_contracts(self) -> dict[str, UIContractV4]:
        return {key: self._ui[key] for key in sorted(self._ui)}

    def bind_handlers(self, runtime: Any) -> dict[str, CapabilityHandlerV4]:
        handlers: dict[str, CapabilityHandlerV4] = {}
        for capability_id in sorted(self._bindings):
            binding = self._bindings[capability_id]
            if binding.handler_method:
                handler = getattr(runtime, binding.handler_method, None)
                if handler is None or not callable(handler):
                    raise V4PluginError(
                        f"capability {capability_id} handler is unavailable: {binding.handler_method}"
                    )
            else:
                handler = runtime._legacy(binding.legacy_capability_id)  # governed legacy facade
            handlers[capability_id] = handler
        return handlers

    def with_plugin(self, plugin: V4SkillPlugin) -> "V4PluginRegistry":
        """Return a new registry; useful for bounded tests and future controlled loading."""
        return V4PluginRegistry(self._plugins + (plugin,))



def _load_plugin_from_module(module: ModuleType) -> V4SkillPlugin:
    plugin = getattr(module, "PLUGIN", None)
    if not isinstance(plugin, V4SkillPlugin):
        raise V4PluginError(
            f"trusted plugin module {module.__name__} must export PLUGIN: V4SkillPlugin"
        )
    return plugin


def discover_v4_plugins(package_name: str = TRUSTED_PLUGIN_PACKAGE) -> V4PluginRegistry:
    """Discover plugins only under the trusted application namespace.

    Arbitrary filesystem paths and user-provided import names are intentionally not
    supported. Modules are imported in sorted order so catalog construction is
    deterministic across restarts.
    """
    if package_name != TRUSTED_PLUGIN_PACKAGE:
        raise V4PluginError(f"untrusted V4 plugin package: {package_name}")
    package = importlib.import_module(package_name)
    package_path = getattr(package, "__path__", None)
    if package_path is None:
        raise V4PluginError(f"trusted V4 plugin package has no package path: {package_name}")

    modules = sorted(
        info.name
        for info in pkgutil.iter_modules(package_path, package.__name__ + ".")
        if not info.name.rsplit(".", 1)[-1].startswith("_")
    )
    if not modules:
        raise V4PluginError("no trusted V4 plugins discovered")
    plugins = tuple(_load_plugin_from_module(importlib.import_module(name)) for name in modules)
    return V4PluginRegistry(plugins)
