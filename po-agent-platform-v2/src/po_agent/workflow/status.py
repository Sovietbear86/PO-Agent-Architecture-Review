"""Workflow status utilities for PO Agent Platform v2."""

from po_agent.domain.models import TaskStatus, StatusCategory
from po_agent.workflow.config import (
    load_workflow_config,
    get_workflow_status_mapping,
    WorkflowConfig,
)

# Global config instance
_workflow_config: WorkflowConfig | None = None


def _get_workflow_config() -> WorkflowConfig:
    """Get workflow config (lazy loaded)."""
    global _workflow_config
    if _workflow_config is None:
        _workflow_config = load_workflow_config()
    return _workflow_config


def normalize_status(raw_status: str) -> str:
    """Normalize a raw status string to AS21 status code.

    Handles both English (AS21) and Russian status names.

    Args:
        raw_status: Raw status string from external source

    Returns:
        Normalized status code (e.g., "Open", "In progress")

    Examples:
        >>> normalize_status("Open")
        'Open'
        >>> normalize_status("Открыта")
        'Open'
        >>> normalize_status("in progress")
        'In progress'
    """
    status_mapping = get_workflow_status_mapping()
    # Create reverse mapping for faster lookup
    reverse_mapping = {v.lower(): v for v in status_mapping.values()}

    # Normalize input
    normalized = raw_status.strip()
    lower_normalized = normalized.lower()

    # Try direct mapping first (Russian)
    if lower_normalized in status_mapping:
        return status_mapping[lower_normalized]

    # Try reverse mapping (English)
    if lower_normalized in reverse_mapping:
        return reverse_mapping[lower_normalized]

    # Check if it's already a valid AS21 status
    try:
        TaskStatus(normalized)
        return normalized
    except ValueError:
        pass

    # Default to Open for unknown statuses
    return "Open"


def is_terminal(status: str) -> bool:
    """Check if status is terminal (no further transitions).

    Args:
        status: AS21 status code

    Returns:
        True if status is terminal (Closed, Resolved, Cancelled)

    Examples:
        >>> is_terminal("Closed")
        True
        >>> is_terminal("Open")
        False
    """
    return status in ("Closed", "Resolved", "Cancelled")


def is_active(status: str) -> bool:
    """Check if status is active work status.

    Args:
        status: AS21 status code

    Returns:
        True if status represents active work

    Examples:
        >>> is_active("In progress")
        True
        >>> is_active("Open")
        False
    """
    config = _get_workflow_config()
    active_statuses = config.get_analytics_statuses("active_work_statuses")
    return status in active_statuses


def is_waiting(status: str) -> bool:
    """Check if status represents waiting/blocking state.

    Args:
        status: AS21 status code

    Returns:
        True if status represents waiting for input

    Examples:
        >>> is_waiting("Need info")
        True
        >>> is_waiting("In progress")
        False
    """
    config = _get_workflow_config()
    waiting_statuses = config.get_analytics_statuses("waiting_statuses")
    return status in waiting_statuses


def is_blocked(status: str) -> bool:
    """Check if task is blocked (waiting for info).

    Args:
        status: AS21 status code

    Returns:
        True if task is blocked

    Examples:
        >>> is_blocked("Need info")
        True
        >>> is_blocked("In progress")
        False
    """
    config = _get_workflow_config()
    blocked_statuses = config.get_analytics_statuses("waiting_statuses")
    return status in blocked_statuses


def get_status_category(status: str) -> StatusCategory:
    """Get the StatusCategory for a given status code.

    Args:
        status: AS21 status code

    Returns:
        StatusCategory enum value

    Examples:
        >>> get_status_category("Open")
        <StatusCategory.BACKLOG: 'backlog'>
        >>> get_status_category("Closed")
        <StatusCategory.COMPLETED: 'completed'>
    """
    config = _get_workflow_config()
    status_config = config.get_status_config(status)

    if status_config is None:
        # Map known Russian statuses
        status_mapping = get_workflow_status_mapping()
        if status in status_mapping.values():
            status_config = config.get_status_config(status)

    if status_config is None:
        return StatusCategory.UNKNOWN

    category_name = status_config.get("category", "unknown")
    try:
        return StatusCategory(category_name)
    except ValueError:
        return StatusCategory.UNKNOWN
