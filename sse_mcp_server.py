#!/usr/bin/env python3
"""SSE MCP Server for Task Tracker."""

from starlette.applications import Starlette
from starlette.responses import StreamingResponse
from starlette.routing import Route
import json
import asyncio

def make_event(method: str, params: dict) -> str:
    """Create an SSE event."""
    data = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params
    }
    return f"data: {json.dumps(data)}\n\n"

def make_initial_metadata() -> str:
    """Create initial metadata event."""
    data = {
        "jsonrpc": "2.0",
        "params": {
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {},
                "completions": {},
                "editing": {},
                "telemetry": {},
                "experimental": {}
            }
        }
    }
    return f"data: {json.dumps(data)}\n\n"

async def sse_endpoint(request):
    """Handle SSE MCP endpoint."""
    async def event_generator():
        """Generate MCP events."""
        # Initial metadata response
        yield make_initial_metadata()
        
        # Health check notification
        yield make_event(
            "notifications/health",
            {
                "status": "healthy",
                "serverInfo": {
                    "name": "Task Tracker SSE MCP Server",
                    "version": "1.0.0"
                }
            }
        )
        
        # Keep connection alive
        while True:
            await asyncio.sleep(30)
            yield ": keepalive\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )

async def mcp_post_endpoint(request):
    """Handle MCP POST endpoint for tool calls."""
    data = await request.json()
    return {
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
                "name": "Task Tracker SSE MCP Server",
                "version": "1.0.0"
            }
        }
    }

app = Starlette(
    routes=[
        Route("/sse", endpoint=sse_endpoint),
        Route("/sse", endpoint=mcp_post_endpoint, methods=["POST"]),
    ]
)

if __name__ == "__main__":
    import uvicorn
    print("Starting SSE MCP Server on http://localhost:8080/sse")
    uvicorn.run(app, host="127.0.0.1", port=8080)
