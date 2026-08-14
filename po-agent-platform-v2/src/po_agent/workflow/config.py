"""Workflow configuration loader for PO Agent Platform v2."""

import os
from pathlib import Path
from typing import Any, Optional

import yaml

from po_agent.core.errors import ConfigurationError


class WorkflowConfig:
    """Workflow configuration loaded from YAML."""

    def __init__(self, config: dict[str, Any]):
        self._config = config

    @property
    def statuses(self) -> dict[str, dict[str, Any]]:
        """Get all status definitions."""
        return self._config.get("statuses", {})

    @property
    def analytics(self) -> dict[str, list[str]]:
        """Get analytics status groupings."""
        return self._config.get("analytics", {})

    @property
    def cycle_time(self) -> dict[str, str]:
        """Get cycle time configuration."""
        return self._config.get("cycle_time", {})

    @property
    def wip(self) -> dict[str, list[str]]:
        """Get WIP configuration."""
        return self._config.get("wip", {})

    @property
    def throughput(self) -> dict[str, list[str]]:
        """Get throughput configuration."""
        return self._config.get("throughput", {})

    @property
    def blockage(self) -> dict[str, Any]:
        """Get blockage detection configuration."""
        return self._config.get("blockage", {})

    def get_status_config(self, status: str) -> Optional[dict[str, Any]]:
        """Get configuration for a specific status."""
        return self.statuses.get(status)

    def get_analytics_statuses(self, category: str) -> list[str]:
        """Get status list for an analytics category."""
        return self.analytics.get(category, [])

    def get_cycle_time_config(self, key: str) -> Optional[str]:
        """Get cycle time configuration value."""
        return self.cycle_time.get(key)

    def get_wip_statuses(self, variant: str = "basic") -> list[str]:
        """Get WIP status list for a variant."""
        return self.wip.get(variant, [])

    def get_throughput_statuses(self, type: str) -> list[str]:
        """Get throughput status list."""
        return self.throughput.get(type, [])

    def get_threshold(self, key: str) -> Optional[int]:
        """Get a threshold value."""
        thresholds = self.blockage.get("thresholds", {})
        return thresholds.get(key)


def load_workflow_config(config_path: Optional[str] = None) -> WorkflowConfig:
    """Load workflow configuration from YAML file.

    Args:
        config_path: Optional path to config file. If not provided,
                     looks for config/workflow.yaml relative to working directory.

    Returns:
        WorkflowConfig instance

    Raises:
        ConfigurationError: If config file not found or invalid
    """
    if config_path is None:
        # Try default locations
        default_paths = [
            Path("config") / "workflow.yaml",
            Path(__file__).parent.parent.parent / "config" / "workflow.yaml",
            Path(__file__).parent.parent.parent.parent / "config" / "workflow.yaml",
        ]

        for path in default_paths:
            if path.exists():
                config_path = str(path)
                break
        else:
            raise ConfigurationError(
                "Workflow config not found. Please provide config path or "
                "ensure config/workflow.yaml exists."
            )

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if not config or not isinstance(config, dict):
            raise ConfigurationError(
                f"Invalid workflow config in {config_path}: expected dictionary"
            )

        return WorkflowConfig(config)

    except FileNotFoundError:
        raise ConfigurationError(f"Workflow config not found: {config_path}")
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML in {config_path}: {e}")
    except Exception as e:
        raise ConfigurationError(f"Error loading workflow config: {e}")


def get_workflow_status_mapping() -> dict[str, str]:
    """Get mapping of Russian status names to AS21 status codes."""
    return {
        "открыта": "Open",
        "требуется информация": "Need info",
        "в работе": "In progress",
        "переоткрыта": "Reopened",
        "готово к ревью": "Ready for review",
        "на ревью": "In review",
        "готово к qa": "Ready for QA",
        "тестирование": "QA",
        "решена": "Resolved",
        "закрыта": "Closed",
        "отменена": "Cancelled",
    }
