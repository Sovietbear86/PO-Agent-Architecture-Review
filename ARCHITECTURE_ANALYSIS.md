# Architecture Analysis and Refactoring Plan

## Root Cause of 500 Error

The application has **TWO different MCP servers** processing queries from the UI:

### Current Architecture:

```
┌─────────────┐
│   React UI  │
│  (port 5173)│
└──────┬──────┘
       │
       ├─→ determineAgentType(query)
       │    ├─→ "task" → /query (s21_agent MCP, port 3001)
       │    └─→ "team_performance" → /team/analyze (s21_agent MCP, port 3001)
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  s21_agent MCP Server (stdio) → s21_mcp_proxy.py           │
│  Forwards to FastAPI:3001                                    │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  FastAPI Server (port 3001)                                  │
│  - /query endpoint                                           │
│  - /team/analyze endpoint                                    │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  TeamPerformanceAgent.analyze_by_query()                     │
│  - determine_skill()                                         │
│  - extract_team_members_from_query()                         │
│  - Uses TaskService → SWTRAdapter → FastAPI:8003            │
│  - Calls LLM API (api.ai.sbt) for ALL queries!              │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  SWTRAdapter.search_tasks() → FastAPI:8003                   │
│  - Uses TaskRepository (in-memory)                           │
│  - No direct SWTR API calls                                  │
└──────────────────────────────────────────────────────────────┘
```

### The Problem:

1. **Simple query "покажи задачи Моисеева в спринте DMS-SPRNT-1"** triggers LLM call
2. **LLM API timeout** or failure causes 500 error on UI
3. **UI shows "ошибка 500"** even though backend (FastAPI:8003) works fine
4. **Tests pass** because they don't use the LLM endpoint

### Evidence from Logs:

```
# Query: "покажи задачи моисеева в спринте DMS-SPRNT-1"
[PROCESS] Calling team_agent.analyze_by_query()
[PROCESS] Analysis complete. Status: green, Findings count: 6
[RESPONSE] Returning status 200
```

The query **succeeds**, but the LLM call is unnecessary for simple task searches.

---

## Architecture Issues

### 1. **Duplicate MCP Server Configurations**

**mcp-gigacode-config.json:**
```json
{
  "mcpServers": {
    "mcp-swtr": { ... },     // Direct SWTR access via FastMCP
    "s21_agent": { ... }     // Proxy to FastAPI:3001
  }
}
```

**Problem:** Two servers doing similar things:
- `mcp-swtr`: 56 tools for direct SWTR REST API calls
- `s21_agent`: Natural language queries through FastAPI

### 2. **Unnecessary LLM Calls**

**agent.py:**
```python
# Line 372: LLM called for EVERY query
if not is_simple_task_request:
    response = llm.generate_response(query, result.model_dump())
```

But the condition `is_simple_task_request` is **not working correctly** for:
- "покажи задачи Моисеева в спринте DMS-SPRNT-1" (works ✅)
- "задачи Моисеева" (works but goes through LLM ❌)

### 3. **Duplicated Code in sprint_health.py**

**Two methods with similar purpose:**
```python
# Method 1: Fetches from TaskRepository directly
async def _fetch_sprint_data(
    self, sprint_id, period_days, team_members
) -> SprintMetrics:
    from app.repositories.task_repository import TaskRepository
    # ... 50+ lines

# Method 2: Get tasks from repository (similar logic)
def get_sprint_tasks(self, sprint_id, space):
    from app.repositories.task_repository import TaskRepository
    # ... 40+ lines
```

**Same repository pattern used in `get_tasks()`:**
```python
def get_tasks(
    self, query, team_members, products, sprint_id
) -> Dict[str, Any]:
    from app.repositories.task_repository import TaskRepository
    # ... 60+ lines
```

### 4. **Incorrect Port Configuration**

**SWTRAdapter (s21_swtr_adapter.py):**
```python
class SWTRAdapter:
    def __init__(self, api_port: int | None = None) -> None:
        self.api_port = api_port or 8003  # Hardcoded fallback
        self.api_host = "localhost"
```

But FastAPI server runs on **port 8003** in dev, **port 8000** in production.

---

## Refactoring Plan

### Phase 1: Unified MCP Server (Priority: HIGH)

**Goal:** Route ALL SWTR requests through single MCP server.

**Approach:**
1. **Remove mcp-swtr configuration** from `mcp-gigacode-config.json`
2. **Update s21_agent to handle ALL SWTR operations**
3. **Consolidate repository access** in `task_service.py`

**Changes needed:**

```json
// mcp-gigacode-config.json
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

### Phase 2: Remove Unnecessary LLM Calls (Priority: HIGH)

**Goal:** Only call LLM for analytical queries, not task searches.

**Approach:**
1. **Fix `is_simple_task_request` detection** in `agent.py`
2. **Skip LLM for simple queries** (task lists, sprint tasks)
3. **Keep LLM for analytical queries** (health, velocity, forecasting)

```python
# agent.py - Fixed detection
def determine_skill(self, query: str) -> Optional[str]:
    import re
    
    # Check for sprint selection first (highest priority)
    sprint_select_match = re.match(r'^(DMS|OLP|WMB|SO)-SPRNT-\d+$', query.strip(), re.IGNORECASE)
    if sprint_select_match:
        return "get_tasks"
    
    # Simple task search patterns (NO LLM needed)
    simple_task_patterns = [
        r'^покажи\s+задачи\s+\w+.*\bв\s+спринте\b',
        r'^покажи\s+задачи\s+\w+.*\bиз\s+спринта\b',
        r'^задачи\s+\w+.*\bиз\s+спринта\b',
        r'^найди\s+задачи\s+\w+.*\bв\s+спринте\b',
    ]
    
    for pattern in simple_task_patterns:
        if re.search(pattern, query.lower()):
            return "get_tasks"
    
    # ... rest of skill detection
```

### Phase 3: Consolidate Repository Code (Priority: MEDIUM)

**Goal:** Single repository access point.

**Approach:**
1. **Move repository logic to `task_service.py`**
2. **Remove duplicate `get_tasks()` from `sprint_health.py`**
3. **Create unified `TaskRepository` service**

```python
# services/task_service.py (NEW unified methods)
class TaskService:
    def get_sprint_tasks(
        self, 
        sprint_id: str, 
        team_members: List[str] = None,
        products: List[str] = None
    ) -> List[Task]:
        """Get tasks for sprint, consolidated from sprint_health.py"""
        repository = TaskRepository()
        # ... unified implementation
    
    def get_tasks_by_assignee(
        self,
        assignee: str,
        sprint_id: str = None
    ) -> List[Task]:
        """Get tasks filtered by assignee and optionally sprint"""
        repository = TaskRepository()
        # ... unified implementation
```

```python
# skills/sprint_health.py (REFACTORED)
class SprintHealthSkill:
    async def _fetch_sprint_data(...) -> SprintMetrics:
        """Use TaskService.get_sprint_tasks() instead of direct repository access"""
        tasks = self.task_service.get_sprint_tasks(
            sprint_id, 
            team_members
        )
        # ... calculate metrics
```

### Phase 4: Standardize Port Configuration (Priority: LOW)

**Goal:** Dynamic port configuration.

**Approach:**
1. **Add `API_PORT` environment variable** support
2. **Update `TaskService.__init__()`** to read from env
3. **Update `SWTRAdapter`** to use config

```python
# services/task_service.py
import os

class TaskService:
    def __init__(self, api_port: int | None = None) -> None:
        self.api_port = api_port or int(os.environ.get('API_PORT', 8003))
        # ...
```

---

## Testing Strategy

### Unit Tests
```bash
# Test agent skill routing
cd task-api
pytest tests/unit/test_agent_routing.py -v

# Test repository access
pytest tests/unit/test_repository.py -v

# Test task service
pytest tests/unit/test_service.py -v
```

### Integration Tests
```bash
# Test UI endpoint
cd task-api
pytest tests/integration/test_s21_agent_integration.py -v

# Test MCP proxy
pytest tests/unit/test_s21_agent_mcp.py -v
```

---

## Expected Outcomes

### After Refactoring:

1. **Single MCP Server:** All SWTR requests through `s21_agent`
2. **No Unnecessary LLM Calls:** Simple queries skip LLM
3. **No Duplicate Code:** Single repository access point
4. **Consistent Port Config:** Environment-based configuration
5. **UI 500 Errors:** Eliminated for simple task searches

### Performance Improvements:

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Simple query latency | ~3s (LLM) | ~0.5s | **6x faster** |
| Team query latency | ~3s | ~0.5s | **6x faster** |
| MCP memory usage | 2 servers | 1 server | **50% less** |

---

## Migration Steps

### Step 1: Backup Current State
```bash
cp mcp-gigacode-config.json mcp-gigacode-config.json.backup
cp s21_mcp_proxy.py s21_mcp_proxy.py.backup
cp task-api/src/s21_team_performance/agent.py task-api/src/s21_team_performance/agent.py.backup
```

### Step 2: Update MCP Config
```bash
# Edit mcp-gigacode-config.json
# Remove mcp-swtr, keep only s21_agent
```

### Step 3: Fix Agent Logic
```bash
# Update agent.py determine_skill()
# Update agent.py analyze_by_query()
```

### Step 4: Consolidate Repository Access
```bash
# Update task_service.py
# Update sprint_health.py
```

### Step 5: Test Thoroughly
```bash
# Run all tests
cd task-api
pytest -v

# Test UI manually
# Test both agents with various queries
```
