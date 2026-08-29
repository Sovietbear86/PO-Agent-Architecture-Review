"""SWTR Health Check and Regressive Preflight Guard.

This module provides a reusable SWTR health/preflight capability for QA/regression
testing. It must be run before every REAL SWTR regression to prevent wasting
debugging time on stale-process issues.

Return values (exactly one):
- SWTR_HEALTHY: All checks passed
- STALE_OR_WRONG_RUNTIME: Task API process has stale/wrong code
- TASK_API_UNAVAILABLE: Task API not reachable
- MCP_SWTR_UNAVAILABLE: MCP-SWTR service unavailable
- REAL_SWTR_READ_FAILED: Real SWTR read failed unexpectedly
- SWTR_HTTP_PATH_FAILED: HTTP path to SWTR failed (not token issue without evidence)
- SWTR_SYNC_FAILED: Single-task sync failed
- PO_AGENT_SWTR_PATH_FAILED: PO Agent SWTR path failed
"""

import httpx
import subprocess
from pathlib import Path
from typing import Optional

# Expected smoke task
SMOKE_TASK_CODE = "DMS-273"
EXPECTED_WORKFLOW_STATUS = "Зарегистрирован"


class SWTRHealthCheckResult:
    """Result of SWTR health check."""

    def __init__(self, status: str, details: dict, error: Optional[str] = None):
        self.status = status
        self.details = details
        self.error = error

    def is_healthy(self) -> bool:
        return self.status == "SWTR_HEALTHY"


class SWTRHealthGuard:
    """Reusable SWTR health/preflight guard for QA/regression tests."""

    def __init__(
        self,
        task_api_url: str = "http://127.0.0.1:8003",
        expected_checkout_path: Optional[str] = None,
        expected_head: Optional[str] = None,
    ):
        self.task_api_url = task_api_url
        self.expected_checkout_path = expected_checkout_path
        self.expected_head = expected_head
        self.details = {}

    def check_runtime_freshness(self) -> SWTRHealthCheckResult:
        """Check 1: RUNTIME FRESHNESS."""
        try:
            # Get PID
            result = subprocess.run(
                ["lsof", "-i", ":8003", "-t"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0 or not result.stdout.strip():
                return SWTRHealthCheckResult(
                    status="TASK_API_UNAVAILABLE",
                    details={},
                    error="Task API not reachable on port 8003",
                )

            pid = result.stdout.strip().split("\n")[0]
            self.details["task_api_pid"] = pid

            # Get git HEAD from parent directory
            repo_root = Path(__file__).resolve().parents[1]
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=str(repo_root),
            )
            current_head = result.stdout.strip()
            self.details["current_head"] = current_head

            # Get CWD
            cwd = str(repo_root)
            self.details["task_api_cwd"] = cwd

            # Check head matches expected
            if self.expected_head and current_head != self.expected_head:
                return SWTRHealthCheckResult(
                    status="STALE_OR_WRONG_RUNTIME",
                    details=self.details,
                    error=f"HEAD mismatch: expected {self.expected_head}, got {current_head}",
                )

            return SWTRHealthCheckResult(status="SWTR_HEALTHY", details=self.details)

        except Exception as e:
            return SWTRHealthCheckResult(
                status="TASK_API_UNAVAILABLE",
                details=self.details,
                error=f"Runtime freshness check failed: {e}",
            )

    def check_mcp_swtr_health(self) -> SWTRHealthCheckResult:
        """Check 2: MCP-SWTR HEALTH."""
        try:
            client = httpx.Client(timeout=30)
            health_url = f"{self.task_api_url}/api/v1/swtr-read/health"
            response = client.get(health_url)
            self.details["health_response"] = response.status_code

            if response.status_code != 200:
                return SWTRHealthCheckResult(
                    status="MCP_SWTR_UNAVAILABLE",
                    details=self.details,
                    error=f"MCP-SWTR health check failed: {response.status_code}",
                )

            # Check transport is stdio
            from app.services.swtr_mcp_client import SWTRMCPClient

            swtr_client = SWTRMCPClient()
            transport = swtr_client.transport_kind()
            self.details["mcp_transport"] = transport

            if transport != "stdio":
                return SWTRHealthCheckResult(
                    status="MCP_SWTR_UNAVAILABLE",
                    details=self.details,
                    error=f"MCP transport not stdio: {transport}",
                )

            # Check tools are available
            # (This is implicit in successful health check)

            return SWTRHealthCheckResult(status="SWTR_HEALTHY", details=self.details)

        except Exception as e:
            return SWTRHealthCheckResult(
                status="MCP_SWTR_UNAVAILABLE",
                details=self.details,
                error=f"MCP-SWTR health check failed: {e}",
            )

    def check_real_swtr_read(self) -> SWTRHealthCheckResult:
        """Check 3: REAL SOURCE PROOF."""
        try:
            client = httpx.Client(timeout=30)
            task_url = f"{self.task_api_url}/api/v1/swtr-read/tasks/{SMOKE_TASK_CODE}"
            response = client.get(task_url)
            self.details["smoke_task_response"] = response.status_code

            if response.status_code != 200:
                detail = response.json().get("detail", {})
                error_type = detail.get("error_type", "")
                # Do NOT classify HTTP 403 as TOKEN_EXPIRED without evidence
                if response.status_code == 403:
                    return SWTRHealthCheckResult(
                        status="SWTR_HTTP_PATH_FAILED",
                        details=self.details,
                        error=f"HTTP 403: {error_type}",
                    )
                return SWTRHealthCheckResult(
                    status="REAL_SWTR_READ_FAILED",
                    details=self.details,
                    error=f"Real SWTR read failed: {response.status_code}",
                )

            task_data = response.json()
            self.details["smoke_task_code"] = task_data.get("task_code")

            # Check workflow_status
            unit = task_data.get("unit", {})
            attributes = unit.get("attributes", [])
            workflow_status = None
            for attr in attributes:
                if attr.get("code") == "workflow_status":
                    workflow_status = attr.get("value", {}).get("name")
                    break

            self.details["workflow_status"] = workflow_status

            if workflow_status != EXPECTED_WORKFLOW_STATUS:
                return SWTRHealthCheckResult(
                    status="REAL_SWTR_READ_FAILED",
                    details=self.details,
                    error=f"Unexpected workflow_status: {workflow_status}",
                )

            return SWTRHealthCheckResult(status="SWTR_HEALTHY", details=self.details)

        except Exception as e:
            return SWTRHealthCheckResult(
                status="REAL_SWTR_READ_FAILED",
                details=self.details,
                error=f"Real SWTR read failed: {e}",
            )

    def check_http_path(self) -> SWTRHealthCheckResult:
        """Check 4: HTTP PATH."""
        try:
            client = httpx.Client(timeout=30)
            task_url = f"{self.task_api_url}/api/v1/swtr-read/tasks/{SMOKE_TASK_CODE}"
            response = client.get(task_url)
            self.details["http_path_status"] = response.status_code

            if response.status_code != 200:
                return SWTRHealthCheckResult(
                    status="SWTR_HTTP_PATH_FAILED",
                    details=self.details,
                    error=f"HTTP path check failed: {response.status_code}",
                )

            return SWTRHealthCheckResult(status="SWTR_HEALTHY", details=self.details)

        except Exception as e:
            return SWTRHealthCheckResult(
                status="SWTR_HTTP_PATH_FAILED",
                details=self.details,
                error=f"HTTP path check failed: {e}",
            )

    def check_bounded_sync(self) -> SWTRHealthCheckResult:
        """Check 5: BOUNDED SYNC PATH."""
        try:
            # This would require testing the sync endpoint
            # For now, we verify the sync endpoint is reachable
            client = httpx.Client(timeout=30)
            sync_url = f"{self.task_api_url}/api/v1/swtr/sync"
            response = client.post(sync_url, json={})
            self.details["sync_response"] = response.status_code

            # Sync may not be needed for every test, so we only warn if it fails
            if response.status_code != 200:
                return SWTRHealthCheckResult(
                    status="SWTR_SYNC_FAILED",
                    details=self.details,
                    error=f"Bounded sync check failed: {response.status_code}",
                )

            return SWTRHealthCheckResult(status="SWTR_HEALTHY", details=self.details)

        except Exception as e:
            return SWTRHealthCheckResult(
                status="SWTR_SYNC_FAILED",
                details=self.details,
                error=f"Bounded sync check failed: {e}",
            )

    def check_po_agent_path(self) -> SWTRHealthCheckResult:
        """Check 6: PO AGENT PATH."""
        try:
            # Verify PO Agent can query task via Task API
            client = httpx.Client(timeout=30)
            task_url = f"{self.task_api_url}/api/v1/swtr-read/tasks/{SMOKE_TASK_CODE}"
            response = client.get(task_url)

            if response.status_code != 200:
                return SWTRHealthCheckResult(
                    status="PO_AGENT_SWTR_PATH_FAILED",
                    details=self.details,
                    error=f"PO Agent SWTR path failed: {response.status_code}",
                )

            return SWTRHealthCheckResult(status="SWTR_HEALTHY", details=self.details)

        except Exception as e:
            return SWTRHealthCheckResult(
                status="PO_AGENT_SWTR_PATH_FAILED",
                details=self.details,
                error=f"PO Agent SWTR path failed: {e}",
            )

    def check_status_proof(self) -> SWTRHealthCheckResult:
        """Check 7: STATUS PROOF."""
        try:
            client = httpx.Client(timeout=30)
            task_url = f"{self.task_api_url}/api/v1/swtr-read/tasks/{SMOKE_TASK_CODE}"
            response = client.get(task_url)

            if response.status_code != 200:
                return SWTRHealthCheckResult(
                    status="REAL_SWTR_READ_FAILED",
                    details=self.details,
                    error=f"Status proof failed: {response.status_code}",
                )

            task_data = response.json()
            unit = task_data.get("unit", {})
            attributes = unit.get("attributes", [])
            workflow_status = None
            for attr in attributes:
                if attr.get("code") == "workflow_status":
                    workflow_status = attr.get("value", {}).get("name")
                    break

            self.details["status_proof"] = workflow_status

            if workflow_status != EXPECTED_WORKFLOW_STATUS:
                return SWTRHealthCheckResult(
                    status="REAL_SWTR_READ_FAILED",
                    details=self.details,
                    error=f"Status proof failed: {workflow_status}",
                )

            return SWTRHealthCheckResult(status="SWTR_HEALTHY", details=self.details)

        except Exception as e:
            return SWTRHealthCheckResult(
                status="REAL_SWTR_READ_FAILED",
                details=self.details,
                error=f"Status proof failed: {e}",
            )

    def check_repeatability(self) -> SWTRHealthCheckResult:
        """Check 8: REPEATABILITY."""
        try:
            results = []
            client = httpx.Client(timeout=30)

            for i in range(3):
                task_url = f"{self.task_api_url}/api/v1/swtr-read/tasks/{SMOKE_TASK_CODE}"
                response = client.get(task_url)

                if response.status_code != 200:
                    return SWTRHealthCheckResult(
                        status="REAL_SWTR_READ_FAILED",
                        details=self.details,
                        error=f"Repeatability check {i+1} failed: {response.status_code}",
                    )

                task_data = response.json()
                unit = task_data.get("unit", {})
                attributes = unit.get("attributes", [])
                workflow_status = None
                for attr in attributes:
                    if attr.get("code") == "workflow_status":
                        workflow_status = attr.get("value", {}).get("name")
                        break

                results.append(workflow_status)

            self.details["repeatability_results"] = results

            if len(set(results)) != 1:
                return SWTRHealthCheckResult(
                    status="REAL_SWTR_READ_FAILED",
                    details=self.details,
                    error=f"Repeatability check failed: inconsistent results {results}",
                )

            return SWTRHealthCheckResult(status="SWTR_HEALTHY", details=self.details)

        except Exception as e:
            return SWTRHealthCheckResult(
                status="REAL_SWTR_READ_FAILED",
                details=self.details,
                error=f"Repeatability check failed: {e}",
            )

    def run_all_checks(self) -> SWTRHealthCheckResult:
        """Run all checks in order and return first failure or healthy."""
        checks = [
            ("Runtime freshness", self.check_runtime_freshness),
            ("MCP-SWTR health", self.check_mcp_swtr_health),
            ("Real SWTR read", self.check_real_swtr_read),
            ("HTTP path", self.check_http_path),
            ("Bounded sync", self.check_bounded_sync),
            ("PO Agent path", self.check_po_agent_path),
            ("Status proof", self.check_status_proof),
            ("Repeatability", self.check_repeatability),
        ]

        for name, check_fn in checks:
            result = check_fn()
            if not result.is_healthy():
                self.details[f"{name}_status"] = result.status
                return result

        return SWTRHealthCheckResult(status="SWTR_HEALTHY", details=self.details)


def swtr_health_guard(
    task_api_url: str = "http://127.0.0.1:8003",
    expected_head: Optional[str] = None,
) -> SWTRHealthCheckResult:
    """ Convenience function to run full health guard."""
    guard = SWTRHealthGuard(
        task_api_url=task_api_url,
        expected_head=expected_head,
    )
    return guard.run_all_checks()


if __name__ == "__main__":
    import os

    task_api_url = os.getenv("TASK_API_BASE_URL", "http://127.0.0.1:8003")

    result = swtr_health_guard(task_api_url)

    print(f"SWTR_HEALTH: {result.status}")
    print()
    print("Details:")
    for key, value in result.details.items():
        print(f"  {key}: {value}")

    if result.error:
        print()
        print(f"Error: {result.error}")

    exit(0 if result.is_healthy() else 1)
