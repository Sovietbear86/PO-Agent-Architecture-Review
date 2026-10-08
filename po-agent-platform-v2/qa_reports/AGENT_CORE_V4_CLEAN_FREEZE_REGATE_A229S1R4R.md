# A229S1R4R — clean freeze re-gate

**Verdict:** `AGENT_CORE_V4_CLEAN_FREEZE_GREEN_A229S1R4R`
**TESTED_HEAD:** `afb6fa1` (`afb6fa1` = full head of `feat/core8-real-query-hardening-v2` at test time)
**Previous RED:** `AGENT_CORE_V4_CLEAN_FREEZE_RED_A229S1R4` — test-only boundary `test_agent_core_v4_task_catalog.py:182` (`capabilities[0]` index assumption)
**Owner fix certified:** `cd76390` test(v4): select terminal task type capability by id — exactly the recommended fix; delta `9627263..afb6fa1` = spec + this gate's test fix only (0 production code).

## P1 — focused stale-test cleanup — **GREEN (0 failed)**

| Suite | Result |
|---|---|
| `tests/test_agent_core_v4_task_catalog.py` + `tests/test_agent_core_v4_task_semantics_hierarchy.py` | **15 passed, 0 failed** |
| `task-api/tests/test_swtr_read_sprint_collection.py` + `test_swtr_task_relations.py` + `test_swtr_assignee_canonical.py` | **40 passed, 0 failed** |

Verified: `task.type_analysis` remains an extra plugin skill outside canonical 54; its capabilities include the space/sprint resolvers + terminal `task.type_analysis`; the formerly-stale A185 `tql_calls` expectations pass; task-type enrichment tests green.

## P2 — full all-green gate — **GREEN (0 failed, no waivers)**

- All `test_agent_core_v4*.py` + all `test_v4*.py`: **248 passed, 0 failed**
- Task API SWTR read/query/assignee suites (`test_swtr_read_facade`, `test_swtr_read_sprint_collection`, `test_swtr_task_relations`, `test_swtr_task_query_partial`, `test_swtr_task_query_release`, `test_swtr_assignee_canonical`, `test_swtr_assignee_timestamps`, `test_swtr_health_guard`, `test_swtr_mcp_client`): **57 passed, 0 failed**
- Frontend `npm run build` (tsc && vite): **exit 0**

## P3 — architecture integrity — **GREEN**

- **Core 6/6 byte-identical** vs A229S1R3 production head `161f2a0123767eafb84e9c49040b167466da8b81` (sha256 blob-hash): `agent_core_v4.py`, `agent_core_v4_robust.py`, `agent_core_v4_reliable.py`, `agent_core_v4_completion.py`, `v4_plugin_registry.py`, `llm/real.py` (canonical path `src/po_agent/llm/real.py`).
- Canonical 54 unchanged (`SKILL_CATALOG` 54 entries, resolvable profile identical to A229S1R3).
- Skill inventory unchanged: **72 skills, unique**, same set as A229S1R3 (delta since then is test/spec only).
- No phrase router or hardcoded person/space/sprint result in the cleanup delta; no local task-store fallback in the sprint/type path (certified A229S1R3, Core untouched since).
- Cleanup delta `161f2a0..afb6fa1`: **0 production-code files** (only `GIGACODE_NEXT_ACTION.md`, `.env.example`, two test files, QA reports).

## P4 — minimal REAL AS21 + Web UI smoke — **GREEN**

Stack on TESTED_HEAD: agent 8004 (PID 61894, `EXPECTED_HEAD=afb6fa1`, process env `TASK_API_BASE_URL=http://127.0.0.1:8241` — local `.env` guard-denied, override as in A229S1R4), task-api 8241 (PID 51031, swtr-read connected, 48 tools), MCP-SWTR 3000 (PID 50900), vite 5175 (PID 56853).

1. **`Покажи открытые задачи Семавина в последнем спринте по OLP с типом дефект`** (fresh conversation): COMPLETED, `runtime_contract`, 91.5 s. Trajectory `space.resolve → sprint.current(OLP) → task.type_analysis(task_type=defect, reference=Семавин, space=OLP, status=not_completed, sprint_id=OLP-SPRNT-9)`. **4/4 EXACT** vs fresh source oracle (OLP-SPRNT-9, 78 rows complete/membership_proven): `[OLP-2974, OLP-3241, OLP-3357, OLP-3392]`; `source_assignee=Semavin.M.M`; `unknown_type_count=0`; **no `source_unavailable`**.
2. **Overview KPIs**: independent `po.status_report` probe = active 82 / completed 29 / blocked 5 / 26.1% (total 111). Fresh browser session: 4 cards populated at ~85 s with **exact same values**; POST audit shows exactly the 3 snapshot queries (`Покажи очередь внимания`, `Сделай daily brief`, `Сделай status report`) — **no `Дай обзор и риски`**; Attention Queue + Daily Brief rendered.
3. **`Покажи иерархию задачи DMS-267`**: COMPLETED, exact retained chain `CRPV-90180 → DMS-253 → DMS-267`, depth 2, epic DMS-349 (A229S1R2 parity).
4. **Task drawer** (via /tasks, `Задачи Семавина в спринте OLP-SPRNT-9` → 19 cards): opened OLP-3236 — title rendered, description/intelligence queries fired (`Покажи задачу OLP-3236`, `Кратко что нужно сделать по задаче OLP-3236`), **no raw JSON/ProseMirror leak**.

**Audit:** 0 unexpected 4xx/5xx (browser + task-api log), 0 console/page errors, frontend proxy-only (0 direct :8241/:3000 browser calls), 0 mutations (0 non-GET on task-api), 0 local `/api/v1/tasks` reads, 0 fully-unscoped task-query (33/33 space- or assignee-scoped), 0 `v4_runtime_failure`/TypeError in agent log.

Screenshots: `/private/tmp/qa229s1r4r/overview_kpi.png`, `/private/tmp/qa229s1r4r/tasks_drawer.png`.

## Return (per spec)

- **TESTED_HEAD:** `afb6fa1`
- **REPORT_COMMIT:** this commit
- **Exact passed counts:** P1 15 + 40 = 55 passed / 0 failed; P2 248 (V4) + 57 (task-api SWTR) passed / 0 failed; frontend build exit 0
- **Effective AS21_MODE:** `task-api` (process env)
- **Effective TASK_API_BASE_URL:** `http://127.0.0.1:8241` (process env override; local `.env` still `:8003` — sandbox guard denied direct edit; owner may align the `.env` file to the new `.env.example`)

## Recommendation

**Freeze `checkpoint/v4-task-semantics-hierarchy-green-a229s1r4` on `afb6fa1`.** All gates green with zero failures and no waivers; both A229S1R3 manual regressions remain closed; full test surface is all-green. Owner may sync the certified delta to public/community, then return to A229R1 latency verification.

## Services left running (all on afb6fa1)

- agent 8004 — PID 61894 (log `/private/tmp/qa229s1r4r_agent.log`)
- task-api 8241 — PID 51031 (log `/private/tmp/qa229s1r4_taskapi.log`)
- MCP-SWTR 3000 — PID 50900 (log `/private/tmp/qa229s1r4_mcp.log`)
- vite [::1]:5175 — PID 56853 (log `/private/tmp/qa229s1r4_vite.log`)
