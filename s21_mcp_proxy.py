#!/usr/bin/env python3
"""
MCP Proxy Server for S21 Task Agent
Converts stdio MCP protocol to HTTP requests to FastAPI server

Сервер работает через stdio (GigaCode) и пересылает запросы на http://localhost:3001/query
"""
import json
import asyncio
import sys
import httpx


class MCPProxy:
    def __init__(self):
        self.base_url = "http://localhost:3001"
        self.next_id = 1

    async def send_request(self, method: str, params: dict = None) -> dict:
        """Send request to FastAPI server and return response."""
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": self.next_id,
                "result": {
                    "tools": [
                        {
                            "name": "query_s21_agent",
                            "description": "Query S21 Task Agent for team tasks. Use this tool for queries like 'покажи задачи Кондратчиковой' or 'покажи задачи Моисеева в спринте DMS-SPRNT-1'",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string", "description": "Natural language query about team tasks"}
                                },
                                "required": ["query"]
                            }
                        }
                    ]
                }
            }
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name == "query_s21_agent":
                query = arguments.get("query", "")
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/query",
                        json={"query": query},
                        timeout=60.0
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    return {
                        "jsonrpc": "2.0",
                        "id": self.next_id,
                        "result": {
                            "content": [
                                {"type": "text", "text": data.get("response", "")}
                            ]
                        }
                    }
            
            return {
                "jsonrpc": "2.0",
                "id": self.next_id,
                "error": {
                    "code": -32601,
                    "message": f"Unknown tool: {tool_name}"
                }
            }
        
        return {
            "jsonrpc": "2.0",
            "id": self.next_id,
            "error": {
                "code": -32601,
                "message": f"Unknown method: {method}"
            }
        }

    async def run(self):
        """Run the proxy server using stdio."""
        print("MCP Proxy started. Waiting for requests...", file=sys.stderr)
        while True:
            try:
                line = await asyncio.to_thread(sys.stdin.readline)
                if not line:
                    break
                
                # Log incoming request
                import datetime
                now = datetime.datetime.now().isoformat()
                print(f"[{now}] MCP Proxy received: {line.strip()}", file=sys.stderr)

                request = json.loads(line.strip())
                method = request.get("method")
                params = request.get("params", {})
                req_id = request.get("id")
                
                self.next_id = req_id
                
                result = await self.send_request(method, params)
                
                # Log outgoing response
                response = json.dumps(result, ensure_ascii=False)
                print(f"[{now}] MCP Proxy sending: {response[:200]}...", file=sys.stderr)

                output = json.dumps(result, ensure_ascii=False) + "\n"
                await asyncio.to_thread(sys.stdout.write, output)
                await asyncio.to_thread(sys.stdout.flush)
                
            except json.JSONDecodeError:
                continue
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": self.next_id,
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }
                output = json.dumps(error_response, ensure_ascii=False) + "\n"
                await asyncio.to_thread(sys.stdout.write, output)
                await asyncio.to_thread(sys.stdout.flush)


async def main():
    proxy = MCPProxy()
    await proxy.run()


if __name__ == "__main__":
    asyncio.run(main())
