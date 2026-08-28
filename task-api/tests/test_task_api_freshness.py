"""Preflight test for Task API runtime freshness verification.

This module verifies that the Task API process under test is actually running
the expected current checkout/code before running real HTTP SWTR regressions.

Failure classification distinguishes:
- TASK_API_NOT_RUNNING
- STALE_OR_WRONG_RUNTIME
- MCP_SWTR_UNAVAILABLE
- SWTR_HTTP_PATH_FAILED
- PREFLIGHT_PASS
"""

import httpx
import pytest

from app.routers.swtr_read import _TASK_CODE_RE


class TaskAPIFreshnessError(Exception):
    """Base exception for Task API freshness preflight errors."""

    def __init__(self, message: str, failure_class: str):
        super().__init__(message)
        self.failure_class = failure_class


class TaskAPINotRunning(TaskAPIFreshnessError):
    """Task API is not reachable on the configured endpoint."""

    def __init__(self):
        super().__init__(
            "Task API is not running or not reachable",
            "TASK_API_NOT_RUNNING",
        )


class StaleOrWrongRuntime(TaskAPIFreshnessError):
    """Task API is running but serving stale/wrong code."""

    def __init__(self, detail: str):
        super().__init__(
            f"Task API is running but serving stale/wrong code: {detail}",
            "STALE_OR_WRONG_RUNTIME",
        )


class MCP_SWTRUnavailable(TaskAPIFreshnessError):
    """MCP-SWTR is unavailable and cannot serve requests."""

    def __init__(self):
        super().__init__(
            "MCP-SWTR is unavailable",
            "MCP_SWTR_UNAVAILABLE",
        )


class SWTRHTTPPathFailed(TaskAPIFreshnessError):
    """HTTP path to SWTR failed for non-stale reasons."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(
            f"SWTR HTTP path failed: {status_code} - {detail}",
            "SWTR_HTTP_PATH_FAILED",
        )


def task_api_freshness_preflight(
    base_url: str = "http://127.0.0.1:8003",
    smoke_task_code: str = "DMS-273",
    expected_workflow_status: str = "Зарегистрирован",
    expected_task_code: str = "DMS-273",
) -> dict:
    """Run Task API runtime freshness preflight.

    Args:
        base_url: Task API base URL
        smoke_task_code: Task code to use for smoke test
        expected_workflow_status: Expected workflow_status value
        expected_task_code: Expected task code in response

    Returns:
        dict with verification results

    Raises:
        TaskAPIFreshnessError: If any check fails
    """
    # Normalize task code
    if not _TASK_CODE_RE.fullmatch(smoke_task_code.upper().strip()):
        raise StaleOrWrongRuntime(f"Invalid task code format: {smoke_task_code}")

    try:
        # 1. Task API is reachable
        health_url = f"{base_url}/api/v1/swtr-read/health"
        health_response = httpx.get(health_url, timeout=5)
        if health_response.status_code != 200:
            raise TaskAPINotRunning()
    except (httpx.RequestError, httpx.HTTPStatusError):
        raise TaskAPINotRunning()

    try:
        # 2. GET /api/v1/swtr-read/tasks/{smoke_task_code}
        task_url = f"{base_url}/api/v1/swtr-read/tasks/{smoke_task_code}"
        task_response = httpx.get(task_url, timeout=30)

        if task_response.status_code != 200:
            detail = task_response.json().get("detail", {})
            if task_response.status_code == 403:
                error_type = detail.get("error_type", "")
                if "ACCESS_DENIED" in error_type.upper():
                    # HTTP 403 ACCESS_DENIED is NOT automatically TOKEN_EXPIRED
                    # It could be stale runtime with cached credentials
                    raise SWTRHTTPPathFailed(
                        task_response.status_code,
                        f"Access denied (not necessarily token expired): {detail}",
                    )
            raise SWTRHTTPPathFailed(task_response.status_code, detail)

        task_data = task_response.json()

        # 3. Verify smoke task code
        if task_data.get("task_code") != expected_task_code:
            raise StaleOrWrongRuntime(
                f"Expected task_code={expected_task_code}, got {task_data.get('task_code')}"
            )

        # 4. Verify workflow_status
        unit = task_data.get("unit", {})
        attributes = unit.get("attributes", [])
        workflow_status = None
        for attr in attributes:
            if attr.get("code") == "workflow_status":
                workflow_status = attr.get("value", {}).get("name")
                break

        if workflow_status != expected_workflow_status:
            raise StaleOrWrongRuntime(
                f"Expected workflow_status={expected_workflow_status}, got {workflow_status}"
            )

        # 5. Verify PID is captured (optional, not required to be specific value)
        # This is recorded in the caller, not in preflight itself

        return {
            "task_api_pid": None,  # Set by caller
            "runtime_path": None,  # Set by caller
            "head": None,  # Set by caller
            "health": 200,
            "smoke_task_code": smoke_task_code,
            "smoke_task_http_status": 200,
            "workflow_status": workflow_status,
            "preflight_verdict": "PREFLIGHT_PASS",
        }

    except (httpx.RequestError, httpx.HTTPStatusError) as exc:
        if isinstance(exc, httpx.HTTPStatusError):
            if exc.response.status_code == 403:
                detail = exc.response.json().get("detail", {})
                error_type = detail.get("error_type", "")
                if "ACCESS_DENIED" in error_type.upper():
                    raise SWTRHTTPPathFailed(exc.response.status_code, detail)
        raise MCP_SWTRUnavailable() from exc


def test_task_api_freshness_preflight_integration(
    task_api_url: str = "http://127.0.0.1:8003",
) -> None:
    """Run preflight and assert True.

    This is a simple wrapper for external callers.

    Args:
        task_api_url: Task API base URL

    Raises:
        AssertionError: If preflight fails
    """
    result = task_api_freshness_preflight(task_api_url)
    assert result["preflight_verdict"] == "PREFLIGHT_PASS"


if __name__ == "__main__":
    # Standalone execution
    import os

    base_url = os.getenv("TASK_API_BASE_URL", "http://127.0.0.1:8003")
    try:
        result = task_api_freshness_preflight(base_url)
        print("PREFLIGHT PASS")
        print(f"  task_api_pid: {result.get('task_api_pid')}")
        print(f"  runtime_path: {result.get('runtime_path')}")
        print(f"  head: {result.get('head')}")
        print(f"  health: {result.get('health')}")
        print(f"  smoke_task_code: {result.get('smoke_task_code')}")
        print(f"  workflow_status: {result.get('workflow_status')}")
        exit(0)
    except TaskAPIFreshnessError as exc:
        print(f"PREFLIGHT FAIL: {exc.failure_class}")
        print(f"  {exc}")
        exit(1)
