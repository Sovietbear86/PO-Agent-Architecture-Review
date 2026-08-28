"""QA fault injection seam for controlled learning loop testing.

This module provides an optional fault injection mechanism that allows QA to
simulate negative results from the AS21 adapter for testing the learning loop
without modifying SWTR data or changing production behavior when disabled.

USAGE:
    Set PO_AGENT_QA_FAULT_INJECTION=1 in environment to enable.

    QA Fault Configuration (via environment):
    - PO_AGENT_QA_FAULT_INJECTION=1
    - PO_AGENT_QA_FAULT_TASK=DMS-271 (task to inject fault for)
    - PO_AGENT_QA_FAULT_STATUS=Unknown (status to inject)
    - PO_AGENT_QA_FAULT_SCOPE=task-lookup (skill/query scope)

    The injected fault:
    - Only affects the first authoritative read for the configured task
    - Recovery (second read) bypasses the fault and reads REAL SWTR
    - Never fabricates positive answers or fake evidence
    - Recovery evidence must come only from REAL SWTR
    - Trace metadata records: qa_fault_injected, qa_fault_scope, qa_fault_consumed

SAFETY:
    - Disabled by default (no impact on normal production)
    - Must be explicitly enabled via environment variable
    - Only affects configured task/scope
    - Recovery always reads from REAL SWTR
    - No modification of SWTR, prompts, skill catalog, or learned policies
"""
from __future__ import annotations

import os
from typing import Any


# Track which tasks have had their fault consumed (for idempotency)
_consumed_faults: set[str] = set()


def is_qa_fault_injection_enabled() -> bool:
    """Check whether QA fault injection is enabled in resolved QA config.

    Use the same configuration path as fault application so environment and
    .env fallback semantics cannot diverge. The resolved config remains
    disabled by default.
    """
    return bool(get_qa_fault_config()["enabled"])


def get_qa_fault_config() -> dict[str, str | None]:
    """Get current QA fault injection configuration from environment or .env file."""
    import os
    from pathlib import Path

    # Try to read from environment first
    env_enabled = os.getenv("PO_AGENT_QA_FAULT_INJECTION", "").strip() == "1"
    env_task_code = os.getenv("PO_AGENT_QA_FAULT_TASK", "").strip().upper() or None
    env_injected_status = os.getenv("PO_AGENT_QA_FAULT_STATUS", "Unknown").strip() or "Unknown"
    env_fault_scope = os.getenv("PO_AGENT_QA_FAULT_SCOPE", "").strip() or ""

    # If not in env, try to read from .env file
    if not env_enabled or not env_task_code:
        project_root = Path(__file__).resolve().parents[3]  # po-agent-platform-v2
        env_file = project_root / ".env"

        if env_file.exists():
            try:
                with open(env_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip()

                            if key == "PO_AGENT_QA_FAULT_INJECTION" and value.strip() == "1":
                                env_enabled = True
                            elif key == "PO_AGENT_QA_FAULT_TASK":
                                env_task_code = value.strip().upper() or None
                            elif key == "PO_AGENT_QA_FAULT_STATUS":
                                env_injected_status = value.strip() or "Unknown"
                            elif key == "PO_AGENT_QA_FAULT_SCOPE":
                                env_fault_scope = value.strip() or ""
            except Exception:
                pass

    if not env_enabled:
        return {
            "enabled": False,
            "task_code": None,
            "injected_status": "Unknown",
            "fault_scope": "",
        }

    return {
        "enabled": True,
        "task_code": env_task_code,
        "injected_status": env_injected_status,
        "fault_scope": env_fault_scope,
    }


def is_qa_fault_consumed(task_code: str) -> bool:
    """Check if fault for this task has been consumed."""
    return task_code.upper() in _consumed_faults


def consume_qa_fault(task_code: str) -> None:
    """Mark fault as consumed for this task."""
    _consumed_faults.add(task_code.upper())


def reset_qa_faults() -> None:
    """Reset consumed faults (for restart testing)."""
    _consumed_faults.clear()


def apply_qa_fault_if_applicable(
    source_data: dict[str, Any],
    original_status: str,
    original_status_raw: str,
    task_code: str,
) -> tuple[str, str, dict[str, Any] | None]:
    """Apply QA fault injection if configured and not yet consumed.

    Args:
        source_data: Original source data from SWTR
        original_status: Original normalized status
        original_status_raw: Original raw status
        task_code: Task code being processed

    Returns:
        Tuple of (status, status_raw, fault_metadata or None)
    """
    config = get_qa_fault_config()

    if not config["enabled"]:
        return original_status, original_status_raw, None

    # Only apply to configured task
    if config["task_code"] and task_code.upper() != config["task_code"].upper():
        return original_status, original_status_raw, None

    # Only apply on first read (not after restart)
    if is_qa_fault_consumed(task_code.upper()):
        return original_status, original_status_raw, None

    # Inject fault
    # Use injected status as raw value - this will be invalid and return UNKNOWN
    # when normalized, creating a negative result for learning loop
    fault_status_raw = config["injected_status"]
    fault_status = "Unknown"  # Will be UNKNOWN due to invalid status_raw

    # Create metadata for trace
    fault_metadata = {
        "qa_fault_injected": True,
        "qa_fault_scope": config["fault_scope"] or "task-lookup",
        "qa_fault_task": task_code.upper(),
        "qa_fault_original_status": original_status,
        "qa_fault_injected_status": fault_status,
    }

    consume_qa_fault(task_code.upper())

    return fault_status, fault_status_raw, fault_metadata
