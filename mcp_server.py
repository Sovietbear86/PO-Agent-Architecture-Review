#!/usr/bin/env python3
"""Simple HTTP MCP Server for Task Tracker."""

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
import json

async def mcp_endpoint(request):
    """Handle MCP endpoint."""
    if request.method == "POST":
        data = await request.json()
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": data.get("id"),
            "result": {
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {},
                    "completions": {},
                    "editing": {},
                    "telemetry": {},
                    "experimental": {}
                },
                "serverInfo": {
                    "name": "Task Tracker MCP Server",
                    "version": "1.0.0"
                }
            }
        })
    else:
        return JSONResponse({
            "message": "Task Tracker MCP Server",
            "version": "1.0.0"
        })

app = Starlette(
    routes=[
        Route("/mcp", endpoint=mcp_endpoint),
    ]
)

if __name__ == "__main__":
    import uvicorn
    print("Starting HTTP MCP Server on http://localhost:3000/mcp")
    uvicorn.run(app, host="127.0.0.1", port=3000)
