"""Unified read-only MCP-SWTR client used by the Task API rich-read facade.

The live MCP-SWTR server is an SSE service. Harness-facing read paths must use
this client rather than the legacy subprocess/stdin bridge in SWTRSyncService.
The legacy bridge is intentionally left in place for historical sync code until
it is migrated separately; it must not be used by new Harness read capabilities.
"""
from __future__ import annotations

import os
from typing import Any, Iterable


class SWTRMCPUnavailable(RuntimeError):
    """Raised when the live MCP-SWTR service cannot be reached."""


class SWTRMCPProtocolError(RuntimeError):
    """Raised when MCP-SWTR returns a response that cannot be normalized."""


class SWTRMCPClient:
    """Small read-only FastMCP SSE client.

    The URL is configuration, not a repository-specific filesystem path. The
    MCP server owns AS21 credentials; Task API never receives or exposes them.
    """

    def __init__(self, sse_url: str | None = None) -> None:
        self.sse_url = sse_url or os.getenv(
            "SWTR_MCP_SSE_URL", "http://127.0.0.1:3000/sse"
        )

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
            from fastmcp.client.transports import SSETransport
        except ImportError as exc:  # pragma: no cover - environment contract
            raise SWTRMCPUnavailable(
                "fastmcp is not installed in the task-api environment"
            ) from exc

        try:
            async with Client(SSETransport(url=self.sse_url)) as client:
                tools = await client.list_tools()
        except Exception as exc:  # pragma: no cover - real transport failure
            raise SWTRMCPUnavailable(f"MCP-SWTR unavailable at {self.sse_url}") from exc

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
            from fastmcp.client.transports import SSETransport
        except ImportError as exc:  # pragma: no cover - environment contract
            raise SWTRMCPUnavailable(
                "fastmcp is not installed in the task-api environment"
            ) from exc

        try:
            async with Client(SSETransport(url=self.sse_url)) as client:
                result = await client.call_tool(name, arguments)
        except Exception as exc:  # pragma: no cover - external MCP/tool failure
            # Keep credentials and remote payloads out of the exception text, but
            # retain the exception class so QA can distinguish validation/tool
            # failures from a dead transport without exposing secrets.
            exc_type = type(exc).__name__
            if exc_type in {"ConnectError", "ConnectTimeout", "ReadTimeout", "PoolTimeout"}:
                raise SWTRMCPUnavailable(
                    f"MCP-SWTR transport failed via {self.sse_url}: {exc_type}"
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
