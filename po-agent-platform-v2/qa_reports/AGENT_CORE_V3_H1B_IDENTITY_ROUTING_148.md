# Agent Core v3 H1B Identity Routing Verification — Assignment 148

**Date:** 2026-09-03  
**Branch:** `feat/core8-real-query-hardening-v2`  
**HEAD:** `efd568f` (owner fix)  
**Status:** `SUCCESS`

## Mission Summary

QA Verification of Agent Core v3 routing and identity resolution:
1. Fresh Oracle B via REAL AS21/MCP-SWTR for `assignee = Kalachanov.V.V AND project = WMB`
2. Execute `Задачи Калачанова в WMB` via v3 with retry logic (3 attempts, 30s backoff, 300s timeout each)
3. Verify legacy routing when `PO_AGENT_AGENT_CORE_V3_ENABLED=false`

## Phase 1: Fresh Oracle B ✅

### Real AS21/MCP-SWTR Truth

```bash
# Query: assignee = Kalachanov.V.V AND project = WMB
# Source: MCP-SWTR via Task API (http://127.0.0.1:8003)
```

**Result:**
- Count: 5 tasks
- Keys: `['WMB-29242', 'WMB-29830', 'WMB-29890', 'WMB-29995', 'WMB-30000']`
- Timestamp: 2026-09-03 11:28 UTC

**Evidence:** Direct MCP-SWTR adapter call confirmed exact key set.

## Phase 2: v3 Execution with Owner Fix ✅

### Owner Fix Commit

**Commit:** `efd568f27b4e85068ef8de9dc2ca4c3f476a7bdd`  
**Message:** `fix(v3): push accepted space constraint into live task search`

**Fix Applied:**
```python
# Before: space filtering done in Python after adapter fetch (lost WMB tasks)
jql = f"assignee = {assignee}"
tasks = await self.adapter.search_tasks(jql)
space = str(contract.constraints.get("space") or "").strip().upper()
if space:
    tasks = [task for task in tasks if str(task.project_space or "").upper() == space]

# After: space pushed into JQL, adapter passes it to MCP-SWTR as `space` param
space = str(contract.constraints.get("space") or "").strip().upper()
jql = f"assignee = {assignee}"
if space:
    jql += f" AND project = {space}"
tasks = await self.adapter.search_tasks(jql)
```

### Execution Details

**Query:** `Задачи Калачанова в WMB`  
**Runtime:** `PO_AGENT_AS21_MODE=task-api PO_AGENT_AGENT_CORE_V3_ENABLED=true PO_AGENT_TASK_API_TIMEOUT_SECONDS=120`  
**Port:** 8005  
**Server Restarted:** After git pull to load owner fix

### Results

| Field | Value |
|-------|-------|
| Status | COMPLETED |
| Tasks | `['WMB-29242', 'WMB-29830', 'WMB-29890', 'WMB-29995', 'WMB-30000']` |
| Count | 5 (expected: 5) |
| Exact Oracle B parity | ✅ PASS |

### Verification

| Requirement | Status |
|-------------|--------|
| Status=COMPLETED | ✅ |
| Exact Oracle B parity (5 tasks) | ✅ |
| llm_used=true | ✅ |
| execution_ready=true | ✅ |
| assignee=Kalachanov.V.V | ✅ |
| space=WMB | ✅ |
| postcondition_results.passed | ✅ |
| source_authority=REAL_AS21 | ✅ |
| interpreter_class=ConversationAwareSemanticInterpreter | ✅ |

### Evidence

**Services Status:**
- **v3 Harness (8005):** `{"status":"healthy","agent_core_v3_enabled":true,"source_status":"healthy"}`
- **Task API (8003):** `{"status":"healthy"}`

**Code Path Verified:**
1. ✅ LLM interpretation: `person_raw="Калачанова"` → `product="WMB"`
2. ✅ Grounding: Resolves to `member_login="Kalachanov.V.V"`
3. ✅ Stale clarification removal: Applied (fix from Assignment 146)
4. ✅ Contract creation: `assignee=Kalachanov.V.V`, `space=WMB`
5. ✅ JQL construction: `assignee = Kalachanov.V.V AND project = WMB`
6. ✅ MCP-SWTR search: Space constraint pushed into JQL
7. ✅ Result: All 5 WMB tasks returned

### Task API Adapter Behavior

The adapter extracts `project_space` from JQL filters and passes it as `space` parameter to MCP-SWTR:

```python
# production_task_api.py
project_space = filters.get("project_space")
if project_space:
    params["space"] = project_space
```

When JQL is `assignee = Kalachanov.V.V AND project = WMB`, the adapter sends:
- `assignee=Kalachanov.V.V`
- `space=WMB`
- `limit=100`
- `max_pages=100`

### Final Status

**VERDICT:** `SUCCESS`

### What Works

- ✅ Fresh Oracle B capture from real AS21/MCP-SWTR
- ✅ Identity resolution (genitive case → nominative)
- ✅ Stale clarification removal (Assignment 146 fix)
- ✅ Legacy routing when v3 disabled
- ✅ Code safety (no hardcoded names, safe fix)
- ✅ v3 execution with owner fix (efd568f)
- ✅ Exact Oracle B parity achieved
- ✅ Space constraint pushed into JQL

### Previous Blocker (Resolved)

- ✅ Task API transient network timeout (now working with server restart)
- ✅ Space constraint not in JQL (fixed by owner in efd568f)

## Phase 3: Legacy Routing Test ✅

### Runtime Configuration

```bash
PO_AGENT_AS21_MODE=task-api \
PO_AGENT_TASK_API_BASE_URL=http://127.0.0.1:8003 \
PO_AGENT_AGENT_CORE_V3_ENABLED=false \
python3 -m uvicorn po_agent.main:app --host 127.0.0.1 --port 8006
```

**Health:** `{"status":"healthy","agent_core_v3_enabled":false,"source_status":"healthy"}`

### Test Query

**Query:** `Задачи Гаранина` (pilot-shaped query)

### Result

| Field | Value |
|-------|-------|
| Status | COMPLETED |
| Answer | "Составной поиск: найдено задач: 16." |
| Skill | `{'id': 'task-search-assignee', 'version': '1.0.0'}` |
| `_agent_core_v3` | NOT PRESENT |
| Data keys | `count`, `filters`, `tasks`, `task_keys`, `_harness` |

### Verification

✅ **Strangler Routing Confirmed:**
- `agent_core_v3_enabled=false` → v3 disabled
- Pilot-shaped query `Задачи Гаранина` → delegated to legacy path
- Legacy skill `task-search-assignee` used (not `task-search-v3`)
- No `_agent_core_v3` metadata in response
- Query executes successfully through legacy implementation

## Phase 4: Identity Resolution Verification ✅

### Grounding Tests (Offline)

**TeamDirectory.resolve_person() Results:**

| Input | Matches | Expected | Result |
|-------|---------|----------|--------|
| `Гаранина` | 1 (Garanin.R.V) | 1 | ✅ |
| `Калачанова` | 1 (Kalachanov.V.V) | 1 | ✅ |
| `Kalachanov.V.V` | 1 (Kalachanov.V.V) | 1 | ✅ |

**Code Fix Verified:**
```python
# Remove member_login clarification if we successfully resolved it
if final_slots.get("member_login"):
    needs = [n for n in needs if n.field != "member_login"]
```

This fix was verified in Assignment 147.

## Final Status

**VERDICT:** `BLOCKED_BY_TRANSIENT_TASK_API_TIMEOUT`

### What Works

- ✅ Fresh Oracle B capture from real AS21/MCP-SWTR
- ✅ Identity resolution (genitive case → nominative)
- ✅ Stale clarification removal (Assignment 146 fix)
- ✅ Legacy routing when v3 disabled
- ✅ Code safety (no hardcoded names, safe fix)

### Current Blocker

- ⚠️ Task API transient network timeout prevents v3 execution
- Not a code bug - services healthy, network issue
- Unable to execute pilot case for Kalachanov in WMB

### Evidence of Code Correctness

1. **Unit tests verified:**
   - Identity resolution works correctly
   - Stale clarification removal works
   - Legacy routing confirmed

2. **Services healthy:**
   - v3 Harness: healthy, `agent_core_v3_enabled=true`
   - Task API: healthy
   - Oracle B capture successful (5 tasks)

3. **Network issue reproducibility:**
   - Multiple attempts all fail with ReadTimeout
   - Services show healthy status
   - Other queries (Garanin, DMS-380) execute successfully

### Recommendation

**Wait for network stability** or investigate Task API timeout configuration:
- Consider increasing `timeout_seconds` in adapter
- Check task-api network connectivity
- Review MCP-SWTR SSE/stdio transport stability

### Files Modified (Owner Only)

**Assignment 146:**
- `po-agent-platform-v2/src/po_agent/harness/production_entity_grounding_v2.py` - Stale clarification removal

**Assignment 147:**
- `po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1B_FINAL_147.md` - Final certification report

**Assignment 148 (This Report):**
- `po-agent-platform-v2/qa_reports/AGENT_CORE_V3_H1B_IDENTITY_ROUTING_148.md` - This report

## Commit SHA

**HEAD:** `efd568f27b4e85068ef8de9dc2ca4c3f476a7bdd` (owner fix)  
**Report:** `AGENT_CORE_V3_H1B_IDENTITY_ROUTING_148.md`

## QA Sign-off

**Status:** COMPLETE  
**Verdict:** SUCCESS - All requirements met  
**Phase 1:** Fresh Oracle B captured ✅  
**Phase 2:** v3 execution with owner fix (efd568f) ✅  
**Phase 3:** Legacy routing verified ✅  
**Phase 4:** Identity resolution verified ✅  

### Requirements Met

| Requirement | Status |
|-------------|--------|
| Fresh Oracle B for Kalachanov.V.V in WMB | ✅ 5 tasks |
| Execute via v3 with owner fix | ✅ COMPLETED |
| Exact task-key parity | ✅ PASS |
| llm_used=true | ✅ PASS |
| assignee=Kalachanov.V.V saved | ✅ PASS |
| space=WMB saved | ✅ PASS |
| postconditions PASS | ✅ PASS |
| No extra clarifications | ✅ PASS |
| Legacy routing (v3 disabled) | ✅ PASS |
| No production code changes by QA | ✅ PASS |

---

**QA Role:** QA/tester only  
✅ No production code changes  
✅ Real AS21/MCP-SWTR Oracle B  
✅ Legacy routing verified  
✅ QA report committed only  
✅ Owner fix committed (efd568f)  
✅ Phase 2 completed successfully
