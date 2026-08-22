"""Operational AS21/SWTR runtime diagnostics.

This module is intentionally outside the product Skill Catalog.  It supports
operators and QA by identifying wiring problems before acceptance runs.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

import httpx


_PO_AGENT_PACKAGE_ROOT = Path(__file__).resolve().parents[3]
_REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
_REQUIRED_SWTR_READ_PATHS = (
    "/api/v1/tasks",
    "/api/v1/swtr-read/health",
    "/api/v1/swtr-read/tasks/{task_code}",
    "/api/v1/swtr-read/sprints/{sprint_id}/tasks",
)
_LEGACY_SWTR_PATHS = (
    "/api/v1/swtr/health",
    "/api/v1/swtr/tasks/{task_code}",
    "/api/v1/swtr/sprints/{sprint_id}/tasks",
)


def _safe_file_path(value: object) -> str | None:
    if not value:
        return None
    return str(Path(str(value)).resolve())


def _expected_package_root() -> Path:
    configured = os.environ.get("PO_AGENT_EXPECTED_PACKAGE_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    cwd = Path.cwd().resolve()
    if (cwd / "src" / "po_agent").exists():
        return cwd
    if (cwd / "po-agent-platform-v2" / "src" / "po_agent").exists():
        return cwd / "po-agent-platform-v2"
    return _PO_AGENT_PACKAGE_ROOT


def _path_state(path: str | None, expected_root: Path) -> str:
    if not path:
        return "MISSING"
    try:
        Path(path).resolve().relative_to(expected_root)
    except ValueError:
        return "WRONG_IMPORT_ROOT"
    return "OK"


def _git_info(path: Path) -> dict[str, Any]:
    def run(*args: str) -> str | None:
        try:
            completed = subprocess.run(
                ("git", "-C", str(path), *args),
                check=True,
                capture_output=True,
                text=True,
                timeout=3,
            )
        except Exception:
            return None
        return completed.stdout.strip() or None

    return {
        "top_level": run("rev-parse", "--show-toplevel"),
        "head": run("rev-parse", "HEAD"),
        "branch": run("rev-parse", "--abbrev-ref", "HEAD"),
        "origin": run("remote", "get-url", "origin"),
    }


def _env_snapshot() -> dict[str, Any]:
    keys = (
        "AS21_MODE",
        "PO_AGENT_AS21_MODE",
        "TASK_API_BASE_URL",
        "PO_AGENT_TASK_API_BASE_URL",
        "PO_AGENT_EXPECTED_PACKAGE_ROOT",
        "PO_AGENT_EXPECTED_HEAD",
        "PYTHONPATH",
        "VIRTUAL_ENV",
    )
    snapshot: dict[str, Any] = {}
    for key in keys:
        value = os.environ.get(key)
        if key == "PYTHONPATH" and value:
            snapshot[key] = value.split(os.pathsep)
        else:
            snapshot[key] = value
    return snapshot


def _module_paths(expected_root: Path) -> dict[str, dict[str, str | None]]:
    import po_agent
    import po_agent.harness.sprint_intelligence as sprint_intelligence

    modules = {
        "po_agent": _safe_file_path(getattr(po_agent, "__file__", None)),
        "po_agent.harness.sprint_intelligence": _safe_file_path(
            getattr(sprint_intelligence, "__file__", None)
        ),
    }
    return {
        name: {
            "path": path,
            "state": _path_state(path, expected_root),
        }
        for name, path in modules.items()
    }


def _suspicious_sys_path_entries() -> list[str]:
    suspicious: list[str] = []
    for entry in sys.path:
        if not entry:
            continue
        resolved = str(Path(entry).resolve())
        if "PO_Agent_Harness" in resolved:
            suspicious.append(resolved)
    return sorted(set(suspicious))


async def _probe_json(client: httpx.AsyncClient, path: str) -> dict[str, Any]:
    try:
        response = await client.get(path)
    except httpx.HTTPError as exc:
        return {
            "reachable": False,
            "status_code": None,
            "error": f"{type(exc).__name__}: {exc}",
        }

    payload: Any = None
    try:
        payload = response.json()
    except ValueError:
        payload = None

    return {
        "reachable": True,
        "status_code": response.status_code,
        "json": payload if isinstance(payload, (dict, list)) else None,
    }


def _path_present(paths: set[str], required: str) -> bool:
    return required in paths or f"{required}/" in paths or required.rstrip("/") in paths


def _classify_task_api(probes: dict[str, Any]) -> dict[str, Any]:
    openapi = probes.get("openapi", {})
    paths = set((openapi.get("json") or {}).get("paths", {})) if openapi.get("reachable") else set()
    missing_paths = [path for path in _REQUIRED_SWTR_READ_PATHS if not _path_present(paths, path)]
    legacy_paths_present = [path for path in _LEGACY_SWTR_PATHS if _path_present(paths, path)]
    swtr_health = probes.get("swtr_read_health", {})
    swtr_status = swtr_health.get("status_code")

    wrong_process = bool(paths and missing_paths)
    legacy_only = bool(legacy_paths_present) and any(path.startswith("/api/v1/swtr-read") for path in missing_paths)
    transport_unavailable = swtr_status in {502, 503}
    not_running = not any(probe.get("reachable") for probe in probes.values())

    state = "healthy"
    if not_running:
        state = "TASK_API_UNREACHABLE"
    elif legacy_only:
        state = "LEGACY_SWTR_ROUTES_ONLY"
    elif wrong_process:
        state = "WRONG_TASK_API_PROCESS"
    elif transport_unavailable:
        state = "SWTR_TRANSPORT_UNAVAILABLE"
    elif swtr_status and swtr_status >= 400:
        state = f"SWTR_READ_HTTP_{swtr_status}"
    elif missing_paths:
        state = "SWTR_READ_ROUTES_UNPROVEN"

    return {
        "state": state,
        "required_paths_present": not missing_paths,
        "missing_paths": missing_paths,
        "legacy_swtr_paths_present": legacy_paths_present,
        "wrong_task_api_process": wrong_process,
        "swtr_transport_unavailable": transport_unavailable,
    }


def _repair_actions(task_api_base_url: str, expected_root: Path) -> list[dict[str, str]]:
    repository_root = expected_root.parent if expected_root.name == "po-agent-platform-v2" else expected_root
    po_agent_dir = shlex.quote(str(expected_root))
    task_api_dir = shlex.quote(str(repository_root / "task-api"))
    base_url = shlex.quote(task_api_base_url)
    return [
        {
            "id": "restart_po_agent_from_current_repo",
            "when": "module_path.state is WRONG_IMPORT_ROOT, adapter is fake, or env aliases are missing",
            "command": (
                f"cd {po_agent_dir} && unset PYTHONPATH && "
                "PO_AGENT_AS21_MODE=task-api "
                f"PO_AGENT_TASK_API_BASE_URL={base_url} "
                f"PO_AGENT_EXPECTED_PACKAGE_ROOT={po_agent_dir} "
                "python3 -m uvicorn po_agent.main:app --host 127.0.0.1 --port 8004"
            ),
        },
        {
            "id": "restart_task_api_from_current_repo",
            "when": "Task API is unreachable, stale, or /api/v1/swtr-read/* routes are absent",
            "command": (
                f"cd {task_api_dir} && "
                "python3 -m uvicorn main:app --host 127.0.0.1 --port 8003"
            ),
        },
        {
            "id": "bounded_oracle_hydration_only",
            "when": "Oracle needs sprint evidence",
            "command": (
                "Hydrate only requested sprint candidate keys and per-task SWTR units; "
                "do not run tenant-wide task sync for narrow oracle proof."
            ),
        },
    ]


async def build_as21_diagnostics(settings: Any) -> dict[str, Any]:
    """Return a non-secret AS21/SWTR runtime diagnostic report."""

    expected_root = _expected_package_root()
    repository_root = expected_root.parent if expected_root.name == "po-agent-platform-v2" else expected_root
    module_paths = _module_paths(expected_root)
    env = _env_snapshot()
    task_api_base_url = settings.task_api_base_url.rstrip("/")
    as21_mode = settings.as21_mode
    git = {
        "expected_package_root": _git_info(expected_root),
        "loaded_package_root": _git_info(_PO_AGENT_PACKAGE_ROOT),
        "cwd": _git_info(Path.cwd()),
    }

    probes: dict[str, Any] = {}
    if as21_mode.strip().lower() in {"task-api", "task_api", "real"}:
        async with httpx.AsyncClient(base_url=task_api_base_url, timeout=5.0) as client:
            probes = {
                "health": await _probe_json(client, "/health"),
                "openapi": await _probe_json(client, "/openapi.json"),
                "swtr_read_health": await _probe_json(client, "/api/v1/swtr-read/health"),
                "tasks_sample": await _probe_json(client, "/api/v1/tasks?limit=1"),
            }

    task_api = _classify_task_api(probes) if probes else {
        "state": "SKIPPED_NON_TASK_API_MODE",
        "required_paths_present": False,
        "missing_paths": list(_REQUIRED_SWTR_READ_PATHS),
        "wrong_task_api_process": False,
        "swtr_transport_unavailable": False,
    }

    wrong_imports = [
        name for name, info in module_paths.items() if info["state"] != "OK"
    ]
    expected_head = os.environ.get("PO_AGENT_EXPECTED_HEAD")
    loaded_head = git["loaded_package_root"].get("head")
    head_mismatch = bool(expected_head and loaded_head and expected_head != loaded_head)
    env_ready = as21_mode.strip().lower() in {"task-api", "task_api", "real"}
    status = "healthy"
    blockers: list[str] = []
    if wrong_imports:
        status = "degraded"
        blockers.append("po_agent_import_root_mismatch")
    if head_mismatch:
        status = "degraded"
        blockers.append("po_agent_git_head_mismatch")
    if not env_ready:
        status = "degraded"
        blockers.append("as21_mode_not_task_api")
    if task_api["state"] != "healthy":
        status = "degraded"
        blockers.append(str(task_api["state"]).casefold())

    return {
        "status": status,
        "blockers": blockers,
        "package_root": str(_PO_AGENT_PACKAGE_ROOT),
        "expected_package_root": str(expected_root),
        "repository_root": str(repository_root),
        "process": {
            "cwd": str(Path.cwd().resolve()),
            "executable": sys.executable,
        },
        "git": git,
        "settings": {
            "as21_mode": as21_mode,
            "task_api_base_url": settings.task_api_base_url,
            "semantic_llm_enabled": settings.semantic_llm_enabled,
        },
        "env": env,
        "module_paths": module_paths,
        "suspicious_sys_path_entries": _suspicious_sys_path_entries(),
        "task_api": task_api,
        "task_api_probes": probes,
        "repair_actions": _repair_actions(task_api_base_url, expected_root),
        "oracle_guidance": {
            "full_task_sync_required": False,
            "required_method": (
                "Use narrow hydrated oracle: sprint candidate keys, then individual "
                "authoritative SWTR task units for only those keys."
            ),
        },
    }
