# Assignment 051 — Clean-Tree Oracle Exact-Set Retest

## Assignment Status

**051_VERDICT = BLOCKED**

**START_HEAD = 9702ab7a54e1856f46a73ba0c7ecd22f2921dfd9**

**REPORT_COMMIT = PENDING**

## Phase 0 — Clean Tracked Tree Guard

### Git Status

```bash
$ git status --short
M   po-agent-platform-v2/src/po_agent/main.py
??  GIGACODE.md
??  PO-Agent-Architecture-Review/
??  mcp-swtr-wrapper.sh
??  mcp-swtr/
??  qa_assignments/qa_035_full_matrix.py
```

### Tracked Changes

```bash
$ git diff --name-only
po-agent-platform-v2/src/po_agent/main.py

$ git diff --cached --name-only
(empty)
```

### Clean-Tree Violation

| Check | Status | Evidence |
|-------|--------|----------|
| `po-agent-platform-v2/src/po_agent/main.py` modified | YES | Unstaged tracked change |
| Production code change | YES | `src/po_agent/main.py` is production runtime |
| Clean tree guard | FAIL | Local tracked runtime patch present |

### Why BLOCKED

**BLOCKED is correct because:**
1. Tracked production code file `po-agent-platform-v2/src/po_agent/main.py` has unstaged modifications
2. The modification adds `SWTR_TOKEN` export to `os.environ` for stdio MCP transport
3. Per clean-tree guard rules: "If any tracked production/config/test/runner/prompt/roadmap/wrapper file is modified or staged, stop"
4. Cannot proceed with oracle retest when local runtime patch is present

### Untracked Files (permitted per clean-tree guard)

- `GIGACODE.md` — not a runtime dependency
- `PO-Agent-Architecture-Review/` — external directory
- `mcp-swtr-wrapper.sh` — local wrapper (not used as runtime dependency)
- `mcp-swtr/` — external MCP-SWTR installation
- `qa_assignments/qa_035_full_matrix.py` — not a runner

**UNTRACKED_RUNTIME_DEPENDENCY_USED = NO**

## Evidence Summary

### Current State

| Metric | Value |
|--------|-------|
| `START_HEAD` | 9702ab7a54e1856f46a73ba0c7ecd22f2921dfd9 |
| `CLEAN_TREE_GUARD` | FAIL |
| `LOCAL_TRACKED_RUNTIME_PATCH_PRESENT` | YES |
| `UNTRACKED_RUNTIME_DEPENDENCY_USED` | NO |

### Tracked Production Changes

| File | Change Type | Location |
|------|-------------|----------|
| `po-agent-platform-v2/src/po_agent/main.py` | Modified | Line 132-138 (SWTR_TOKEN export) |

### Permitted Untracked Files

- `GIGACODE.md` — GIGACODE.md (not runtime)
- `PO-Agent-Architecture-Review/` — external directory
- `mcp-swtr-wrapper.sh` — wrapper script (not used as runtime dep)
- `mcp-swtr/` — external MCP-SWTR installation
- `qa_assignments/qa_035_full_matrix.py` — not a runner

## Required Footer

```
ASSIGNMENT_ID = CORE8_ORACLE_CLEAN_TREE_EXACT_SET_RETEST_051
START_HEAD = 9702ab7a54e1856f46a73ba0c7ecd22f2921dfd9
REPORT_COMMIT = PENDING
CLEAN_TREE_GUARD = FAIL
LOCAL_TRACKED_RUNTIME_PATCH_PRESENT = YES
UNTRACKED_RUNTIME_DEPENDENCY_USED = NO
TRACKED_CHANGED_FILES = po-agent-platform-v2/src/po_agent/main.py
051_VERDICT = BLOCKED
ORACLE_PATH_PROVEN = BLOCKED
READY_TO_RERUN_017_V2 = BLOCKED
READY_TO_RESUME_GATE_E = NO
```

## Manual Action Required

To unblock assignment 051, the owner must:

1. Commit or revert the tracked change in `po-agent-platform-v2/src/po_agent/main.py`:
   ```bash
   # Either commit:
   git add po-agent-platform-v2/src/po_agent/main.py
   git commit -m "feat: export SWTR_TOKEN to os.environ for stdio MCP transport"
   
   # Or revert:
   git checkout po-agent-platform-v2/src/po_agent/main.py
   ```

2. Then re-run assignment 051 from a clean tree:
   ```bash
   git switch feat/core8-real-query-hardening-v2
   git pull --ff-only origin feat/core8-real-query-hardening-v2
   ```

## Report Location

Report created at: `qa_reports/CORE8_ORACLE_CLEAN_TREE_EXACT_SET_RETEST_051.md`
