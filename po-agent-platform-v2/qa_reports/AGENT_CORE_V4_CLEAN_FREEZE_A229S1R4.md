# A229S1R4 — cleanup + all-green freeze gate

**Verdict:** `AGENT_CORE_V4_CLEAN_FREEZE_RED_A229S1R4`
**TESTED_HEAD:** `9627263` (full SHA in git log; START_HEAD)
**STOP at:** P1 (first failing boundary recorded below). P2/P3/P4 NOT run per stop rule.

## P0 — setup — GREEN

- `git pull --ff-only` → `9627263` (owner commits since A229S1R3 report: `5b2ff45` test(source): isolate sprint pagination from timestamp enrichment; `8e7e124` chore(env): align local Harness Task API example with 8241; `9627263` spec).
- Tracked worktree: clean except `GIGACODE.md` (QA memory file, same state as A229S1R3 GREEN run).
- **Local `.env` correction was NEEDED:** `po-agent-platform-v2/.env` still pinned `TASK_API_BASE_URL=http://localhost:8003` (line 5; first `AliasChoices` alias — wins) and `PO_AGENT_TASK_API_BASE_URL=http://127.0.0.1:8003` (line 19). Sandbox file guard denied direct `.env` edit (secrets file), so the correction was applied as **explicit process env** on the agent launch: `TASK_API_BASE_URL=http://127.0.0.1:8241` (+ `PO_AGENT_TASK_API_BASE_URL=http://127.0.0.1:8241`). Effective resolution proven via `Settings()` in the same env: `task_api_base_url=http://127.0.0.1:8241`, `as21_mode=task-api`.
- Full stack restarted on `9627263`: MCP 3000 (PID 50900, fresh), task-api 8241 (PID 51031, swtr-read `connected`, 48 tools), agent 8004 (PID 55877, `/health` `status=healthy`, `agent_core_v4_ready=True`, `adapter=task-api`, `source_status=healthy`), vite 5175 (PID 56853).

## P1 — focused stale-test cleanup — **RED (first failing boundary)**

Executed per spec (0 failed required):

| Suite | Result |
|---|---|
| `task-api/tests/test_swtr_read_sprint_collection.py` + `test_swtr_task_relations.py` + `test_swtr_assignee_canonical.py` (spec's `test_swtr_read_canonical.py` = this file) | **40 passed, 0 failed** — the 3 formerly-stale A185 `tql_calls` expectations now pass (owner `5b2ff45` fixtures set `created_at`/`deadline`); new task-type enrichment tests green |
| `po-agent-platform-v2/tests/test_agent_core_v4_task_semantics_hierarchy.py` | 5 passed, 0 failed (within combined run: 14 passed) |
| `po-agent-platform-v2/tests/test_agent_core_v4_task_catalog.py` | **1 failed, 9 passed** |

### First failing boundary (exact)

```
FAILED tests/test_agent_core_v4_task_catalog.py::test_task_semantics_hierarchy_skills_are_extra_plugin_skills_not_canonical54_rows
AssertionError: assert 'task_type' in {'reference': 'required space text'}   (line 182)
```

**Root cause (proven):** the owner's own cleanup refresh (in `9627263`, diff lines 167-173) correctly updated the capability-tuple assertion to the new order
`("space.resolve","sprint.resolve","sprint.search","sprint.current","task.type_analysis")`
but the same test's pre-existing index assumption (line 182, introduced `c129a0e` A229S1R2-era, when the tuple was `("task.type_analysis",)`) reads `type_skill["capabilities"][0]["arguments"]` — which is now `space.resolve` with arguments `{'reference': 'required space text'}`, not the terminal capability. Lines 182-183 (`"task_type"`, `"created_period"` in `capabilities[0]["arguments"]`) were not part of the refresh.

**Production contract is correct:** `catalog.load("task.type_analysis")` → the `task.type_analysis` capability entry (found by id, index 4) has arguments including both `task_type` and `created_period` (verified in-process). Live behavior was already certified in A229S1R3 P3 (6/6 exact, terminal `task.type_analysis` with `task_type=defect` in args). **No production defect — test-logic bug in the owner's refreshed test file** (recurring class: A205-1/A205B/A217C — refreshed test not run to completion before shipping; this gate's "0 failed, no waivers" rule correctly caught it).

**Owner fix (test-only, ~2 lines):** select the terminal capability by id instead of index:
```python
terminal = next(c for c in type_skill["capabilities"] if c["id"] == "task.type_analysis")
assert "task_type" in terminal["arguments"]
assert "created_period" in terminal["arguments"]
```
then re-run the full file (and this assignment) to completion.

### P1 items already verified before the boundary
- `task.type_analysis` remains an extra plugin skill outside canonical 54 (test lines 161-174 pass: set disjointness + new tuple + UI widgets).
- Its capabilities include space/sprint resolvers plus terminal `task.type_analysis` (lines 167-173 pass).
- The three formerly-stale A185 `tql_calls` expectations pass (task-api 40/40).
- New task-type enrichment tests green (task-api 40/40).

## P2 / P3 / P4 — NOT executed (stop at first RED)

## Return (per spec)

- TESTED_HEAD: `9627263`
- REPORT_COMMIT: this commit
- Exact passed counts (executed): task-api focused 40 passed / 0 failed; po-agent focused 14 passed / 1 failed (`test_agent_core_v4_task_catalog.py`); P2/P3/P4 not run
- Effective AS21_MODE: `task-api` (process env, proven via Settings)
- Effective TASK_API_BASE_URL: `http://127.0.0.1:8241` (process env; `.env` file still `:8003` — sandbox guard denied direct edit; owner may update `.env` file line 5 to match the new `.env.example`)
- Local 8003 → 8241 correction needed: **YES** (applied as process env override)

## Services left running (all on 9627263)

- agent 8004 — PID 55877 (log `/private/tmp/qa229s1r4_agent.log`)
- task-api 8241 — PID 51031 (log `/private/tmp/qa229s1r4_taskapi.log`)
- MCP-SWTR 3000 — PID 50900 (log `/private/tmp/qa229s1r4_mcp.log`)
- vite [::1]:5175 — PID 56853 (log `/private/tmp/qa229s1r4_vite.log`)

**Next:** owner 1-line test fix (select terminal capability by id) → A229S1R4 re-run (expect: P1 0 failed, then P2 full all-green, P3 integrity, P4 smoke).
