# JIRA MCP Server Setup

## Overview
JIRA MCP Server allows you to search for WMB* tasks on the corporate SBT system at https://portal.works.prod.sbt

## Current Status
- HTTP MCP Server: Running on port 3000 ✅
- SSE MCP Server: Running on port 8080 ✅  
- JIRA MCP Server: Configured, requires PLATFORM_SESSION cookie from browser ✅

## Authentication Details

The corporate JIRA system at https://portal.works.prod.sbt uses:
- **SynGX proxy** with **OIDC/SSO** authentication
- **PLATFORM_SESSION cookie** from browser (NOT API tokens)
- API Bearer token authentication DOES NOT WORK (returns 401)

## Setup Instructions

### Step 1: Get PLATFORM_SESSION Cookie

1. Open browser to https://portal.works.prod.sbt
2. Open DevTools (F12) -> **Application** tab -> **Cookies** -> **PLATFORM_SESSION**
3. Copy the PLATFORM_SESSION cookie value

### Step 2: Set Cookie in MCP Server

POST to `/set-cookie` endpoint:
```bash
curl -X POST http://localhost:3000/set-cookie \
  -H "Content-Type: application/json" \
  -d '{"platform_session": "YOUR_COOKIE_VALUE"}'
```

Or use Python:
```python
import urllib.request
import json

PLATFORM_SESSION = "YOUR_COOKIE_VALUE"
url = 'http://localhost:3000/set-cookie'
data = json.dumps({'platform_session': PLATFORM_SESSION}).encode()
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req, timeout=10)
print(resp.read().decode())
```

### Step 3: Test Connection

```bash
# Check health
curl http://localhost:3000/health

# List tools
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}'

# Search tasks
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "id": 1,
    "params": {
      "name": "search_tasks",
      "arguments": {
        "jql": "project = WMB ORDER BY created DESC",
        "max_results": 5
      }
    }
  }'
```

## Available MCP Tools

### 1. get_task
Get a task by its Jira key.

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "id": 1,
  "params": {
    "name": "get_task",
    "arguments": {
      "task_key": "WMB-29995"
    }
  }
}
```

### 2. search_tasks
Search for tasks with JQL query.

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "id": 1,
  "params": {
    "name": "search_tasks",
    "arguments": {
      "jql": "project = WMB AND status = In Progress",
      "max_results": 20
    }
  }
}
```

### 3. get_my_tasks
Get tasks assigned to current user.

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "id": 1,
  "params": {
    "name": "get_my_tasks",
    "arguments": {
      "max_results": 20
    }
  }
}
```

## Cookie Expiration

The PLATFORM_SESSION cookie expires frequently and must be refreshed periodically. When you get 401 errors:

1. Open browser to https://portal.works.prod.sbt
2. Get new PLATFORM_SESSION cookie from DevTools
3. POST to `/set-cookie` with the new cookie

## Server Logs

```bash
tail -f /tmp/jira_mcp.log
```

## Restart Server

```bash
lsof -t -i:3000 | xargs kill -9
cd /Users/kalachanov.v.v/Desktop/Мои\ документы/Обучение/GIGACodeCLI/MyTestProject_1/MyTestProject_1
nohup python3 jira_mcp_server.py > /tmp/jira_mcp.log 2>&1 &
```
