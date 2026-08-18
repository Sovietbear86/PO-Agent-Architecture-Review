"""Unified read-only MCP-SWTR client used by the Task API rich-read facade.

The live MCP-SWTR server is an SSE service.  Harness-facing read paths must use
this client rather than the legacy subprocess/stdin bridge in SWTRSyncService.
The legacy bridge is intentionally left in place for historical sync code until
it is migrated separately; it must not be used by new Harness read capabilities.
"""
from __future__ import annotations

import os
from typing import Any


class SWTRMCPUnavailable(RuntimeError):
    """Raised when the live MCP-SWTR service cannot be reached."""


class SWTRMCPProtocolError(RuntimeError):
    """Raised when MCP-SWTR returns a response that cannot be normalized."""


class SWTRMCPClient:
    """Small read-only FastMCP SSE client.

    The URL is configuration, not a repository-specific filesystem path.  The
    MCP server owns AS21 credentials; Task API never receives or exposes them.
    """

    def __init__(self, sse_url: str | None = None) -> None:
        self.sse_url = sse_url or os.getenv(
            "SWTR_MCP_SSE_URL", "http://127.0.0.1:3000/sse"
        )

    async def list_tools(self) -> list[str]:
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

        names: list[str] = []
        for tool in tools or []:
            name = getattr(tool, "name", None)
            if isinstance(name, str):
                names.append(name)
            elif isinstance(tool, dict) and isinstance(tool.get("name"), str):
                names.append(tool["name"])
        return names

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
        except Exception as exc:  # pragma: no cover - real transport failure
            raise SWTRMCPUnavailable(
                f"MCP-SWTR tool {name!r} failed via {self.sse_url}"
            ) from exc

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
