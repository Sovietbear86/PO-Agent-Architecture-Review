# GIGACODE.md

## Project Overview

This is a multi-technology task tracker project with intelligent agent capabilities for team performance analysis. The project has been refactored to unify MCP (Model Context Protocol) architecture and fix 500 errors on UI queries.

### Current State

- **Root directory**: Multi-implementation project root
- **`task-api/`**: Contains all three implementations (Python FastAPI, Java Spring Boot, JavaScript React)
- **`mcp-swtr/`**: SWTR MCP Server using FastMCP framework
- **Two Agent Implementations**:
  - `s21-task-agent`: Basic task management agent
  - `s21_team_performance`: Advanced team performance analysis agent

### Technology Stack (by implementation)

| Implementation | Language | Framework | Purpose |
|---------------|----------|-----------|---------|
| **Python** | Python 3.11+ | FastAPI | REST API backend with /docs endpoint |
| **Java** | Java 17+ | Spring Boot 3 + Spring Web | REST API backend |
| **JavaScript** | TypeScript | React 18+ + Vite | SPA frontend |
| **SWTR MCP** | Python 3.11+ | FastMCP | SWTR REST API integration |

---

## Directory Structure

```
MyTestProject_1/
├── .gigacode/             # GigaCode configuration
│   ├── agents/            # Agent skill definitions
│   ├── skills/            # Built-in skills
│   └── settings.json      # MCP server configuration (s21_agent only)
├── .gigaide/              # GigaCode IDE configuration
├── .idea/                 # IntelliJ IDEA project files
├── mcp-swtr/              # SWTR MCP Server (Python/FastMCP)
│   ├── mcp_server.py      # Main MCP server (56 tools for SWTR)
│   └── api-docs.json      # API documentation
├── s21-task-agent/        # Basic task agent package
│   ├── AGENT.md
│   └── config/            # Agent configuration
├── task-api/              # Task tracker implementation directory
│   ├── app/               # Python FastAPI application
│   │   ├── routers/       # API route handlers (tasks, jira, swtr_sync)
│   │   ├── models/        # Pydantic models
│   │   ├── schemas/       # Request/Response schemas
│   │   ├── services/      # Business logic
│   │   └── repositories/  # Data access layer
│   ├── src/               # React TypeScript source
│   │   ├── components/    # React components (AgentChat, TaskForm, etc.)
│   │   ├── hooks/         # Custom React hooks
│   │   ├── types/         # TypeScript types
│   │   └── api/           # API client
│   ├── s21_team_performance/  # Team performance agent
│   │   ├── agent.py       # Main agent with skill routing
│   │   ├── skills/        # 9 analysis skills
│   │   ├── models/        # AnalysisResult, TeamMember, etc.
│   │   └── services/      # TaskService, metrics
│   ├── tests/             # Python pytest tests
│   ├── config/            # Agent configuration (team_members.yaml, etc.)
│   ├── main.py            # FastAPI entry point
│   ├── package.json       # Node.js dependencies
│   ├── requirements.txt   # Python dependencies
│   ├── pom.xml            # Maven build configuration
│   └── README.md          # Implementation documentation
├── s21_mcp_proxy.py       # Stdio-to-HTTP proxy for s21_agent
├── s21_agent_mcp_server.py # FastAPI server for s21_agent (port 3001)
├── jira_mcp_server.py     # Jira MCP Server (HTTP, port 3000)
├── swtr_client.py         # Standalone SWTR client
├── sync_sprint_tasks.py   # Sync tasks from SWTR sprints
├── ARCHITECTURE_ANALYSIS.md  # Architecture analysis and refactoring plan
├── REFACTORING_SUMMARY.md    # Detailed refactoring summary
├── BRIEF Java.md          # Java Spring Boot requirements
├── BRIEF JavaScript.md    # React SPA requirements
├── BRIEF Python.md        # Python FastAPI requirements
├── JIRA_MCP_SETUP.md      # Jira MCP setup guide
├── MCP_ERROR_FIX.md       # MCP error documentation
└── mcp-gigacode-config.json  # MCP server configuration
```

---

## Building and Running

### Python (FastAPI)

```bash
cd task-api
pip install -r requirements.txt
uvicorn main:app --reload --port 8003
```

**Requirements:** Python 3.11+, pip

**Endpoints:**
- `GET /api/v1/tasks` - List tasks with filtering (status, assignee, limit, offset)
- `GET /api/v1/tasks/{id}` - Get task by UUID
- `POST /api/v1/tasks` - Create task
- `PUT /api/v1/tasks/{id}` - Update task
- `PATCH /api/v1/tasks/{id}/status` - Update task status
- `DELETE /api/v1/tasks/{id}` - Delete task
- `GET /health` - Health check
- `GET /docs` - FastAPI Swagger UI documentation

**Running Tests:**
```bash
cd task-api
pytest
```

**Key requirement:** `/docs` endpoint must be accessible for auto-generated documentation.

---

### Java (Spring Boot)

```bash
cd task-api
mvn spring-boot:run
```

**Requirements:** Java 17+, Maven

**Endpoints (expected):**
- `GET /api/v1/tasks` - List tasks with filtering
- `GET /api/v1/tasks/{id}` - Get task
- `POST /api/v1/tasks` - Create task
- `PUT /api/v1/tasks/{id}` - Update task
- `DELETE /api/v1/tasks/{id}` - Delete task

**Running Tests:**
```bash
cd task-api
mvn test
```

---

### JavaScript (React SPA)

```bash
cd task-api
npm install
npm run dev
```

**Requirements:** Node.js 18+, npm 9+

**Running Tests:**
```bash
cd task-api
npm test -- --run
```

---

### SWTR MCP Server

```bash
cd mcp-swtr
uv run mcp_server.py
```

**Requirements:** Python 3.11+, uv

**Authentication:**
```bash
# Save token to file
mkdir -p ~/.config/swtr
printf '%s' 'YOUR_TOKEN' > ~/.config/swtr/api_key
chmod 600 ~/.config/swtr/api_key

# Or set environment variable
export TOKEN="YOUR_JWT_TOKEN"
export BASE_URL="https://portal.works.prod.sbt/swtr"
```

**Available Tools (56 total):**
- Read: `read_unit`, `find_units`, `get_current_sprint`, `get_sprint_tasks`, `get_unit_comments`, `search_wiki_pages`, `search_test_cases`
- Write: `create_unit`, `update_unit`, `create_unit_comment`, `create_unit_link`

---

### S21 Agent (Team Performance)

The s21_agent is configured in `.gigacode/settings.json`:

```json
{
  "mcpServers": {
    "s21_agent": {
      "command": "python3",
      "args": ["/path/to/s21_mcp_proxy.py"],
      "transport": "stdio"
    }
  }
}
```

**FastAPI Server (port 3001):**
```bash
cd task-api
python3 s21_agent_mcp_server.py
```

**Endpoints:**
- `POST /query` - Natural language query processing
- `GET/POST /health` - Health check

---

## Development Conventions

### Code Style

- **TypeScript**: Strict mode, React 18+ patterns, React Testing Library
- **Java**: Spring Boot 3 conventions, JUnit 5 + MockMvc for tests
- **Python**: PEP 8, pytest for tests

### Testing

| Tech | Framework | Command |
|------|-----------|---------|
| React | Vitest + React Testing Library | `npm test -- --run` |
| Java | JUnit 5 + MockMvc | `mvn test` |
| Python | pytest | `pytest` |

### Data Models

**Task Schema:**
```json
{
  "id": "uuid",
  "title": "string (1-200 chars)",
  "description": "string | null (max 1000 chars)",
  "assignee": "string | null (max 100 chars)",
  "status": "todo | in_progress | done",
  "created_at": "datetime",
  "updated_at": "datetime",
  "deadline": "datetime | null"
}
```

### Validation Rules

| Field | Required | Min Length | Max Length |
|-------|----------|------------|------------|
| title | ✅ | 1 | 200 |
| description | ❌ | 0 | 1000 |
| assignee | ❌ | 0 | 100 |
| status | — | — | todo/in_progress/done |

### Agent Skill Routing

**Simple task searches** (no LLM):
- Pattern: `покажи задачи {member} из спринта {ID}` or `в спринте {ID}`
- Returns: `get_tasks` skill → direct repository access
- Latency: <1 second

**Analytical queries** (with LLM):
- `sprint_health` - Sprint health analysis
- `velocity_analysis` - Velocity metrics
- `flow_metrics` - Flow/Cycle time analysis
- `workload_balance` - Workload balance
- `competency_matching` - Skill matching
- `bottleneck_analysis` - Bottleneck detection
- `forecasting` - Release forecasting
- `release_linkage` - Release tracking

### State Management

- **SPA**: React state + localStorage persistence (key: `task-tracker`)
- **API**: In-memory storage (no database)
- **Python**: TaskRepository singleton with file persistence at `~/.task-tracker/tasks.json`
- **Java**: TaskService with ConcurrentHashMap

---

## API Documentation

### Python FastAPI

The API automatically generates interactive documentation:

1. Start the server: `uvicorn main:app --reload --port 8003`
2. Open browser: `http://localhost:8003/docs`
3. Try endpoints directly in Swagger UI

### Endpoints Details

**List Tasks** - `GET /api/v1/tasks`
- Query params: `status` (optional), `assignee` (optional), `limit` (default: 100), `offset` (default: 0)

**Create Task** - `POST /api/v1/tasks`
- Body: `{title, description?, assignee?}`
- Response: 201 with created task

**Update Task** - `PUT /api/v1/tasks/{id}`
- Body: `{title?, description?, assignee?}`
- Partial updates supported

**Update Status** - `PATCH /api/v1/tasks/{id}/status`
- Body: `{status: "todo" | "in_progress" | "done"}`

---

## SberWorks Task Tracker (SWTR) Integration

### Overview

The project integrates with SberWorks Task Tracker (SWTR) via two MCP servers:

1. **mcp-swtr**: Direct SWTR REST API access (56 tools)
2. **s21_agent**: Natural language queries through FastAPI

### Authentication

**SWTR Authentication:**
- Personal access token from **https://portal.works.prod.sbt/ssd/privileges**
- Save to file: `~/.config/swtr/api_key`
- Or set: `export TOKEN="YOUR_JWT_TOKEN"`

**Jira Authentication:**
- **PLATFORM_SESSION cookie** from browser (NOT API tokens)
- Bearer token authentication DOES NOT WORK (returns 401)
- Set cookie via: `POST /set-cookie` on Jira MCP server

### Sync Scripts

| Script | Purpose |
|--------|---------|
| `sync_sprint_tasks.py` | Sync tasks from SWTR sprints for team members |
| `swtr_sync_cli.py` | CLI tool for SWTR task synchronization |
| `swtr_sync_cli_v2.py` | Updated sync CLI |
| `swtr_sync_cli_v3.py` | Latest sync CLI |

### Running Sync
```bash
cd task-api
python3 sync_sprint_tasks.py --spaces "DMS,OLP,WMB,CRPV,STS" --save
```

### Team Member Filtering

The sync script filters tasks by team members using `s21_team_performance.agent.TeamPerformanceAgent`.

### Allowed Spaces

Currently supported spaces: **WMB**, **OLP**, **DMS**, **CRPV**, **STS**.

---

## Architecture Notes

### MCP Server Configuration

**mcp-gigacode-config.json:**
```json
{
  "mcpServers": {
    "mcp-swtr": { ... },    // Direct SWTR access
    "s21_agent": { ... }    // FastAPI proxy (stdio → HTTP:3001)
  }
}
```

**Current Configuration (.gigacode/settings.json):**
- Only `s21_agent` is configured (mcp-swtr removed)
- Stdio transport for GigaCode compatibility

### Request Flow: UI to SWTR

```
React UI (port 5173)
  ↓
determineAgentType(query)
  ├─→ "task" → s21_agent MCP (stdio) → FastAPI:3001
  └─→ "team_performance" → s21_agent MCP (stdio) → FastAPI:3001

FastAPI:3001
  ↓
TeamPerformanceAgent.analyze_by_query()
  ├─ determine_skill() → skill name
  ├─ extract_team_members_from_query() → list of logins
  └─ skill.analyze() → AnalysisResult

Skills
  ├─ get_tasks → TaskRepository (in-memory)
  └─ Analytical skills → TaskService → SWTRAdapter → FastAPI:8003

FastAPI:8003
  ↓
TaskRepository → find_all(source="swtr_sprint")
```

### Refactored Behavior

**Before:**
- Simple task searches triggered LLM API calls (3+ seconds)
- Two MCP servers caused conflicts
- 500 errors on UI for complex queries

**After:**
- Simple queries → `get_tasks` skill (no LLM, <1 second)
- Analytical queries → analytical skills (with LLM for insights)
- Single MCP server (s21_agent)
- No more 500 errors from LLM timeouts

---

## Jira/MCP Integration

### Overview

Jira MCP Server (port 3000) provides task search capabilities for WMB* projects.

### Available Tools

1. **get_task(task_key)** - Get task by Jira key
2. **search_tasks(jql, max_results)** - Search tasks with JQL
3. **get_my_tasks(max_results)** - Get current user's tasks

### Authentication

The Jira system uses **PLATFORM_SESSION cookie** from browser:

```bash
# Get cookie from browser DevTools → Application → Cookies → PLATFORM_SESSION

# Set cookie in MCP server
curl -X POST http://localhost:3000/set-cookie \
  -H "Content-Type: application/json" \
  -d '{"platform_session": "YOUR_COOKIE_VALUE"}'

# Test connection
curl http://localhost:3000/health
```

### Server Management

```bash
# Start server
cd /path/to/project
nohup python3 jira_mcp_server.py > /tmp/jira_mcp.log 2>&1 &

# Check logs
tail -f /tmp/jira_mcp.log

# Restart server
lsof -t -i:3000 | xargs kill -9
# Then restart
```

---

## SberWorks Task Tracker (SWTR) Integration

### Overview

The project includes **swtr CLI skill** (standalone Node.js CLI) that implements 56 commands for SberWorks Task Tracker (Sbertraker) REST API.

### Authentication

Personal access token from **https://portal.works.prod.sbt/ssd/privileges**:

```bash
# Save token to file (recommended)
mkdir -p ~/.config/swtr
printf '%s' 'YOUR_TOKEN' > ~/.config/swtr/api_key
chmod 600 ~/.config/swtr/api_key

# Or set environment variable
export SWTR_TOKEN="YOUR_TOKEN"
```

### Usage Examples

```bash
# List all commands
node .agents/skills/swtr/cli.js help

# Read unit details
node .agents/skills/swtr/cli.js read_unit WMB-5166

# Structured search (JSON query)
node .agents/skills/swtr/cli.js find_units --json '{"spaces":["WMB"],"properties":{"and":[{"property":"summary","value":"task","operator":"like"}]},"size":10}'

# TQL search (raw query)
node .agents/skills/swtr/cli.js find_tql --json '{"query":"space = \"WMB\" AND workflow_status NOT IN (\"resolved\",\"closed\")","size":50}'

# Get unit comments
node .agents/skills/swtr/cli.js get_unit_comments --unit_code WMB-29890 --size 20
```

### Important Notes

- **Bearer token does NOT work** for API calls (returns 401/403)
- System requires **PLATFORM_SESSION cookie** for authentication
- Bearer token can be saved to `~/.config/swtr/api_key` but API calls will still fail
- Only **browser-based session** via SynGX proxy works for Jira/SWTR API
- For local task management, use FastAPI server instead

### API Documentation

OpenAPI/Swagger: https://portal.works.prod.sbt/swtr/swagger-ui/index.html

### Key Files

- `swtr_client.py` - Python client wrapper for SWTR REST API
- `.agents/skills/swtr/` - Node.js CLI skill
- `~/.config/swtr/api_key` - Personal access token storage

---

## Development Notes

### Database
- **Location**: `~/.task-tracker/tasks.json`
- **Format**: JSON array of task objects
- **Persistence**: Tasks persist across server restarts

### Testing
```bash
# Python
cd task-api
pytest

# JavaScript
cd task-api
npm test -- --run
```

### API Changes
To add new API endpoints:
1. Create schema in `app/schemas/`
2. Add router in `app/routers/`
3. Implement service in `app/services/`
4. Update repository if needed

---

## Agent Integration Guide

### Team Performance Agent

**Location**: `task-api/src/s21_team_performance/`

**Skills**:
1. `sprint_health` - Sprint velocity, predictability, blockers
2. `velocity_analysis` - Team velocity over time
3. `flow_metrics` - Cycle time, throughput, WIP
4. `workload_balance` - Team member load distribution
5. `competency_matching` - Skill match for tasks
6. `bottleneck_analysis` - Process bottleneck detection
7. `forecasting` - Release date prediction
8. `release_linkage` - Feature-to-release tracking
9. `get_tasks` - Task search (no LLM)

**Usage**:
```bash
# Query agent
POST /query
{
  "query": "покажи задачи Иванова из спринта DMS-SPRNT-1"
}

# Team performance analysis
POST /team/analyze
{
  "skill": "sprint_health",
  "params": {
    "sprint_id": "DMS-SPRNT-1",
    "team_members": ["Ivanov.A.B"]
  }
}
```

---

## MCP Server Configuration

### Current Configuration

**`.gigacode/settings.json`**:
```json
{
  "mcpServers": {
    "s21_agent": {
      "command": "python3",
      "args": ["/path/to/s21_mcp_proxy.py"],
      "transport": "stdio"
    }
  }
}
```

**`mcp-gigacode-config.json`** (backup):
- Contains both `mcp-swtr` and `s21_agent` configurations
- Can be restored if needed

### Stdio-to-HTTP Proxy

**s21_mcp_proxy.py**: Converts stdio MCP protocol to HTTP requests to FastAPI:3001

**FastAPI Server (s21_agent_mcp_server.py)**: Listens on port 3001

---

## Known Issues and Solutions

### 500 Errors on UI Queries

**Problem**: Simple task searches caused LLM timeouts (3+ seconds)

**Solution**: 
1. Implemented skill routing that distinguishes simple vs analytical queries
2. Simple queries (get_tasks) skip LLM entirely
3. Analytical queries (sprint_health, velocity, etc.) use LLM

**Result**: 6x faster for simple queries, no more 500 errors

### MCP Server Conflicts

**Problem**: Two MCP servers (`mcp-swtr` and `s21_agent`) processed queries differently

**Solution**: 
1. Removed `mcp-swtr` from `.gigacode/settings.json`
2. Unified all SWTR operations through `s21_agent`
3. Standardized repository access in `sprint_health.py`

**Result**: Single source of truth for SWTR operations

### Code Duplication

**Problem**: Three methods in `sprint_health.py` with duplicate repository access logic

**Solution**:
1. Created unified `_get_sprint_tasks_for_members()` method
2. Removed 50+ lines of duplicate code
3. Single repository access point

**Result**: 50% less code, maintainable single source

---

## Files Reference

### Key Configuration Files

| File | Purpose |
|------|---------|
| `mcp-gigacode-config.json` | MCP server configuration (backup) |
| `.gigacode/settings.json` | Current MCP configuration |
| `task-api/requirements.txt` | Python dependencies |
| `task-api/package.json` | Node.js dependencies |
| `task-api/tsconfig.json` | TypeScript configuration |
| `task-api/pom.xml` | Maven build configuration |
| `task-api/config/team_members.yaml` | Team member definitions |

### Key Source Files

| File | Purpose |
|------|---------|
| `task-api/src/s21_team_performance/agent.py` | Main agent with skill routing |
| `task-api/src/s21_team_performance/skills/sprint_health.py` | Sprint health analysis skill |
| `s21_mcp_proxy.py` | Stdio-to-HTTP proxy |
| `s21_agent_mcp_server.py` | FastAPI server for s21_agent |
| `mcp-swtr/mcp_server.py` | SWTR MCP Server (FastMCP) |
| `jira_mcp_server.py` | Jira MCP Server |

### Documentation Files

| File | Purpose |
|------|---------|
| `ARCHITECTURE_ANALYSIS.md` | Architecture analysis and refactoring plan |
| `REFACTORING_SUMMARY.md` | Detailed refactoring summary |
| `JIRA_MCP_SETUP.md` | Jira MCP setup guide |
| `MCP_ERROR_FIX.md` | MCP error documentation |
| `SWTR_SYNC_GUIDE.md` | SWTR sync guide |

---

## SberWorks Task Tracker (SWTR) Integration

### Overview

The project includes **swtr CLI skill** (standalone Node.js CLI) that implements 56 commands for SberWorks Task Tracker (Sbertraker) REST API.

### Authentication

Personal access token from **https://portal.works.prod.sbt/ssd/privileges**:

```bash
# Save token to file (recommended)
mkdir -p ~/.config/swtr
printf '%s' 'YOUR_TOKEN' > ~/.config/swtr/api_key
chmod 600 ~/.config/swtr/api_key

# Or set environment variable
export SWTR_TOKEN="YOUR_TOKEN"
```

### Usage Examples

```bash
# List all commands
node .agents/skills/swtr/cli.js help

# Read unit details
node .agents/skills/swtr/cli.js read_unit WMB-5166

# Structured search (JSON query)
node .agents/skills/swtr/cli.js find_units --json '{"spaces":["WMB"],"properties":{"and":[{"property":"summary","value":"task","operator":"like"}]},"size":10}'

# TQL search (raw query)
node .agents/skills/swtr/cli.js find_tql --json '{"query":"space = \"WMB\" AND workflow_status NOT IN (\"resolved\",\"closed\")","size":50}'

# Get unit comments
node .agents/skills/swtr/cli.js get_unit_comments --unit_code WMB-29890 --size 20
```

### Important Notes

- **Bearer token does NOT work** for API calls (returns 401/403)
- System requires **PLATFORM_SESSION cookie** for authentication
- Bearer token can be saved to `~/.config/swtr/api_key` but API calls will still fail
- Only **browser-based session** via SynGX proxy works for Jira/SWTR API
- For local task management, use FastAPI server instead

### API Documentation

OpenAPI/Swagger: https://portal.works.prod.sbt/swtr/swagger-ui/index.html

### Key Files

- `swtr_client.py` - Python client wrapper for SWTR REST API
- `.agents/skills/swtr/` - Node.js CLI skill
- `~/.config/swtr/api_key` - Personal access token storage

---

## GigaCode Added Memories
- Jira/SWTR Task Tracker: System at https://portal.works.prod.sbt uses SynGX proxy with OIDC/SSO. API Bearer token from /ssd/privileges returns 401/403 - NOT WORKING. PLATFORM_SESSION cookie only works in browser context. Real task URL: https://portal.works.prod.sbt/swtr/units/all/unit/WMB-XXXXX?space=WMB&tenant=defaul
- Jira MCP Server: HTTP server on port 3000 with /mcp endpoint. Tools: get_task, search_tasks, get_my_tasks. Requires PLATFORM_SESSION cookie.
- Jira MCP Setup: POST /set-cookie with {"platform_session": "COOKIE_VALUE"} to authenticate. Server logs at /tmp/jira_mcp.log.
- FastAPI Task Tracker: Running at http://127.0.0.1:8000 with /docs endpoint. Working local task management with in-memory storage. Singleton TaskRepository pattern required for in-memory persistence between requests.
- swtr CLI: Standalone Node.js skill (v2.2.0) implementing 56 SWTR REST API commands. Bearer token saved to ~/.config/swtr/api_key but API access blocked by SynGX proxy - only browser sessions work.
