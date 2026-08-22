"""Unified read-only MCP-SWTR client used by the Task API rich-read facade.

Harness-facing read paths must use this client rather than the historical
bulk-sync subprocess bridge in SWTRSyncService.  The client supports both remote
SSE and local stdio MCP transports while keeping the public Task API facade
read-only.
"""
from __future__ import annotations

import os
import shlex
from typing import Any, Iterable


class SWTRMCPUnavailable(RuntimeError):
    """Raised when the live MCP-SWTR service cannot be reached."""


class SWTRMCPProtocolError(RuntimeError):
    """Raised when MCP-SWTR returns a response that cannot be normalized."""


class SWTRMCPClient:
    """Small read-only FastMCP client.

    The transport is configuration, not a repository-specific filesystem path.
    MCP server credentials are passed only through the child process environment
    for stdio mode and are never exposed by the Task API response payloads.
    """

    def __init__(
        self,
        sse_url: str | None = None,
        *,
        transport: str | None = None,
    ) -> None:
        self.transport = (transport or os.getenv("SWTR_MCP_TRANSPORT", "sse")).strip().lower()
        self.sse_url = sse_url or os.getenv(
            "SWTR_MCP_SSE_URL", "http://127.0.0.1:3000/sse"
        )
        self.stdio_command = os.getenv("SWTR_MCP_STDIO_COMMAND", "python3")
        self.stdio_args = self._stdio_args()
        self.stdio_cwd = os.getenv("SWTR_MCP_STDIO_CWD") or None

    def transport_kind(self) -> str:
        if self.transport in {"stdio", "sse"}:
            return self.transport
        return "unknown"

    def _stdio_args(self) -> list[str]:
        configured = os.getenv("SWTR_MCP_STDIO_ARGS")
        if configured:
            return shlex.split(configured)
        script = os.getenv("SWTR_MCP_STDIO_SCRIPT")
        return [script] if script else []

    def _stdio_env(self) -> dict[str, str]:
        names = {
            name.strip()
            for name in os.getenv("SWTR_MCP_STDIO_ENV_KEYS", "TOKEN,BASE_URL,PORT").split(",")
            if name.strip()
        }
        env = {name: os.environ[name] for name in names if name in os.environ}
        if "TOKEN" not in env and os.getenv("SWTR_TOKEN"):
            env["TOKEN"] = os.environ["SWTR_TOKEN"]
        if "BASE_URL" not in env and os.getenv("SWTR_MCP_BASE_URL"):
            env["BASE_URL"] = os.environ["SWTR_MCP_BASE_URL"]
        env.setdefault("PORT", "0")
        return env

    def _transport_target(self) -> str:
        if self.transport == "stdio":
            command = " ".join([self.stdio_command, *self.stdio_args]).strip()
            return f"stdio:{command or '<missing command>'}"
        return self.sse_url

    def _build_transport(self) -> Any:
        if self.transport == "stdio" and (not self.stdio_command or not self.stdio_args):
            raise SWTRMCPUnavailable(
                "MCP-SWTR stdio transport requires SWTR_MCP_STDIO_COMMAND "
                "and SWTR_MCP_STDIO_ARGS or SWTR_MCP_STDIO_SCRIPT"
            )

        try:
            from fastmcp.client.transports import SSETransport, StdioTransport
        except ImportError as exc:  # pragma: no cover - environment contract
            raise SWTRMCPUnavailable(
                "fastmcp is not installed in the task-api environment"
            ) from exc

        if self.transport == "stdio":
            return StdioTransport(
                command=self.stdio_command,
                args=self.stdio_args,
                env=self._stdio_env(),
                cwd=self.stdio_cwd,
                keep_alive=False,
            )
        if self.transport == "sse":
            return SSETransport(url=self.sse_url)
        raise SWTRMCPUnavailable(f"Unsupported MCP-SWTR transport {self.transport!r}")

    @staticmethod
    def _tool_to_dict(tool: Any) -> dict[str, Any]:
        if isinstance(tool, dict):
            return dict(tool)
        model_dump = getattr(tool, "model_dump", None)
        if callable(model_dump):
            dumped = model_dump()
            if isinstance(dumped, dict):
                return dumped
        result: dict[str, Any] = {}
        for attr in ("name", "description", "inputSchema", "input_schema"):
            value = getattr(tool, attr, None)
            if value is not None:
                result[attr] = value
        return result

    async def list_tool_descriptors(self) -> list[dict[str, Any]]:
        """Return MCP tool descriptors including input schemas when exposed."""
        try:
            from fastmcp import Client
        except ImportError as exc:  # pragma: no cover - environment contract
            raise SWTRMCPUnavailable(
                "fastmcp is not installed in the task-api environment"
            ) from exc

        try:
            async with Client(self._build_transport()) as client:
                tools = await client.list_tools()
        except Exception as exc:  # pragma: no cover - real transport failure
            raise SWTRMCPUnavailable(
                f"MCP-SWTR unavailable via {self._transport_target()}"
            ) from exc

        descriptors = [self._tool_to_dict(tool) for tool in (tools or [])]
        return [item for item in descriptors if isinstance(item.get("name"), str)]

    async def list_tools(self) -> list[str]:
        descriptors = await self.list_tool_descriptors()
        return [str(item["name"]) for item in descriptors]

    async def tool_input_schema(self, name: str) -> dict[str, Any]:
        """Return one tool input schema or an empty object if none is exposed."""
        descriptors = await self.list_tool_descriptors()
        descriptor = next((item for item in descriptors if item.get("name") == name), None)
        if descriptor is None:
            raise SWTRMCPProtocolError(f"MCP-SWTR tool {name!r} is not available")
        schema = descriptor.get("inputSchema") or descriptor.get("input_schema") or {}
        return dict(schema) if isinstance(schema, dict) else {}

    async def tool_input_properties(self, name: str) -> set[str]:
        """Return declared input property names for one MCP tool."""
        schema = await self.tool_input_schema(name)
        properties = schema.get("properties")
        if not isinstance(properties, dict):
            return set()
        return {str(key) for key in properties}

    async def supported_arguments(
        self,
        name: str,
        candidates: dict[str, Any],
        *,
        required: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Filter optional arguments against the live MCP tool schema."""
        properties = await self.tool_input_properties(name)
        result = dict(required or {})
        for key, value in candidates.items():
            if key in properties and value is not None:
                result[key] = value
        return result

    async def preferred_alias_arguments(
        self,
        name: str,
        groups: Iterable[tuple[Iterable[str], Any]],
        *,
        required: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Choose at most one declared alias for each semantic argument.

        Some MCP descriptors advertise several compatibility aliases such as
        query/q/search/text. Sending all aliases at once can make the downstream
        API reject an otherwise valid request. This helper picks the first alias
        from each ordered group that the live schema declares.
        """
        properties = await self.tool_input_properties(name)
        result = dict(required or {})
        for aliases, value in groups:
            if value is None:
                continue
            selected = next((alias for alias in aliases if alias in properties), None)
            if selected is not None:
                result[selected] = value
        return result

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> list[dict[str, Any]]:
        """Call one MCP tool and normalize its content items to plain dicts."""
        if not name or not isinstance(arguments, dict):
            raise SWTRMCPProtocolError("Invalid MCP tool call")

        try:
            from fastmcp import Client
        except ImportError as exc:  # pragma: no cover - environment contract
            raise SWTRMCPUnavailable(
                "fastmcp is not installed in the task-api environment"
            ) from exc

        try:
            async with Client(self._build_transport()) as client:
                result = await client.call_tool(name, arguments)
        except Exception as exc:  # pragma: no cover - external MCP/tool failure
            # Keep credentials and remote payloads out of the exception text, but
            # retain the exception class so QA can distinguish validation/tool
            # failures from a dead transport without exposing secrets.
            exc_type = type(exc).__name__
            if exc_type in {
                "BrokenPipeError",
                "ConnectError",
                "ConnectTimeout",
                "FileNotFoundError",
                "PermissionError",
                "PoolTimeout",
                "ProcessLookupError",
                "ReadTimeout",
            }:
                raise SWTRMCPUnavailable(
                    f"MCP-SWTR transport failed via {self._transport_target()}: {exc_type}"
                ) from exc
            raise SWTRMCPProtocolError(
                f"MCP-SWTR tool {name!r} failed: {exc_type}"
            ) from exc

        is_error = getattr(result, "is_error", None)
        if is_error is None:
            is_error = getattr(result, "isError", None)
        if is_error is True:
            raise SWTRMCPProtocolError(f"MCP-SWTR tool {name!r} returned an error result")

        content = getattr(result, "content", None)
        if content is None and isinstance(result, dict):
            content = result.get("content")
        if not isinstance(content, list):
            raise SWTRMCPProtocolError("MCP-SWTR returned no content list")

        normalized: list[dict[str, Any]] = []
        for item in content:
            if isinstance(item, dict):
                normalized.append(dict(item))
                continue
            model_dump = getattr(item, "model_dump", None)
            if callable(model_dump):
                dumped = model_dump()
                if isinstance(dumped, dict):
                    normalized.append(dumped)
                    continue
            item_type = getattr(item, "type", None)
            text = getattr(item, "text", None)
            if isinstance(item_type, str):
                row: dict[str, Any] = {"type": item_type}
                if isinstance(text, str):
                    row["text"] = text
                normalized.append(row)
                continue
            raise SWTRMCPProtocolError("Unsupported MCP content item")

        if not normalized:
            raise SWTRMCPProtocolError("MCP-SWTR returned empty content")
        return normalized
