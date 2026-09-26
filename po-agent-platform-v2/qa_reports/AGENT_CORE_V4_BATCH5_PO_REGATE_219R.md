# AGENT_CORE_V4 Batch 5 PO Regate — A219R

**Verdict: `AGENT_CORE_V4_BATCH5_PO_GREEN_A219R`**

| Field | Value |
|---|---|
| Date | 2026-09-26 |
| START_HEAD | `4ed98f8` |
| A219 report base | `6d40807` (qa: A219 report) |
| Owner fix commits | `51b2fd3` (plugin: procedural spec + skill procedure text), `7be95ad` (focused test) |
| Branch | `feat/core8-real-query-hardening-v2` |
| Defect under re-gate | D-A219-1: invalid source key → planner detour to `task.lookup` → `capability_not_loaded:task.lookup` → step-budget → `v4_runtime_failure` |

## D-A219-1: CLOSED

The procedural fix (capability spec + skill procedure now state "Do NOT load or call
task.lookup; call po.local_task_draft directly") removes the detour. **0 of 17 invalid-key
runs** (12 official P2 + 1 warm-up + 2 fresh-process controls) performed a `task.lookup`
call. Every run: direct `po.local_task_draft(task_key="DMS-999999")`, typed terminal,
`draft_created=false`, `write_performed=false`, 0 `v4_runtime_failure`, 0 step-budget
exhaustion, no generic failure text.

## Phase 0 — fix-scope audit: PASS

`git diff --stat 6d40807..4ed98f8` = exactly 3 files:

1. `po-agent-platform-v2/src/po_agent/harness/v4_plugins/wave_batch5_po.py` — capability
   spec string + skill procedure list (procedural text only; no handler/logic change)
2. `po-agent-platform-v2/tests/test_agent_core_v4_batch5_po.py` — new focused test
   `test_local_task_draft_contract_owns_source_validation`
3. `GIGACODE_NEXT_ACTION.md` — assignment doc

Zero Agent Core / planner / runtime / session-context / adapter / task-api edits.
Registry before any run: 67 skills / 12 plugins / 0 dups.

## Phase 1 — focused tests: PASS

- `test_agent_core_v4_batch5_po.py` + `test_agent_core_v4_plugin_registry.py` +
  `test_agent_core_v4_planner_signature_parity.py`: **21 passed**
- Full `test_agent_core_v4*.py` + `test_v4*.py`: **205 passed**
- 0 unexplained failures.

## Phase 2 — direct invalid-key regression (blocking): PASS 13/13

12 official runs = 6 NL forms × 2 runs + 1 warm-up, fresh sessions each, agent freshly
restarted on `4ed98f8` (PID 78348):

| Criterion | 13/13 |
|---|---|
| loaded goal = po.local_task_draft | ✓ |
| NO task.lookup call | ✓ (0 occurrences) |
| called directly with task_key=DMS-999999 | ✓ |
| typed terminal, draft_created=false, write_performed=false | ✓ |
| 0 v4_runtime_failure, 0 step-budget, no generic error | ✓ |

### Point-read semantics (bounded, pre-existing adapter behavior)

The spec line "exactly one bounded point read per run" is met at the **fresh-process**
level. Proven with fresh-process controls after a full agent restart (PID 82118):

- `fp1` (first invalid-key run in the process): `api_delta=1` — exactly one
  `GET /api/v1/swtr-read/tasks/DMS-999999` → 404 line in the task-api log; 404 safely
  maps to task=None; typed terminal.
- `fp2` (same process, same key): `api_delta=0` — served from the adapter's
  `_raw_unit_cache` 404→None negative cache.

Root cause of the 0-delta on repeated same-key runs:
`HardenedProductionTaskApiAS21Adapter._raw_unit_cache` (process-lifetime dict,
`hardened_production_task_api.py:129`) introduced in `7c06bc2`
("fix: restore live AS21 sprint and space grounding") — **pre-existing, not part of the
A219R fix** (the fix diff touches only the 3 files above). Behavior is bounded and safe:
at most one point read per key per process, no re-reads, no scans. Non-blocking finding
for the owner (see Findings).

Task-api log evidence: all `DMS-999999` lines are `GET /api/v1/swtr-read/tasks/DMS-999999
HTTP/1.1" 404 Not Found`; total 4 in the window (A219 ×2 across old process, A219R
warm-up ×1, fresh control ×1).

## Phase 3 — valid-key retained: PASS 4/4

Fresh process (PID 82118), unique source key per run so each draft performs its own
bounded point read:

| Run | Key | Custom subject | Result |
|---|---|---|---|
| v1 | DMS-380 | — | COMPLETED, dc=true, REAL_AS21, wp=false, approval=true, api=2 |
| v2 | DMS-434 | — | same |
| v3 | DMS-399 | «Follow-up по релизу 2.5.0» | same; draft title = custom subject |
| v4 | DMS-423 | — | same |

Each run = 2 bounded same-key HTTP lines: `GET /tasks/{key}` (unit) +
`GET /tasks/{key}/files` (attachment metadata) — identical to A219's point-read pattern
(`get_task` always includes attachment metadata); no scans, no lookups.
`draft.requires_approval_for_external_write=true` in all 4.

## Phase 4 — user-only draft retained: PASS 3/3

3 subject-only forms («Подготовить one-pager по DataMarts», «Собрать вопросы для
ретроспективы», «Обновить критерии приёмки»): direct `po.local_task_draft`,
**api_delta=0** (zero AS21 calls), `source=USER_INPUT_ONLY`, `draft_created=true`,
`write_performed=false`.

## Phase 5 — clarification retained: PASS 2/2

- c1 "создай локальный черновик задачи": NEEDS_CLARIFICATION, typed planner-frontier
  marker `v4_ready_without_source_observation`, 0 source calls, no generic error.
- c2 "создай локальную задачу-черновик": NEEDS_CLARIFICATION, typed capability-level
  marker `v4_capability_clarification` (skill loaded, capability raised the
  clarification before executing), 0 source calls, no generic error.

Both satisfy: typed NEEDS_CLARIFICATION + zero source calls + no generic error.

## Phase 6 — compact retained Batch 5 smoke: PASS 4/4 (A219 oracle parity exact)

Fresh bounded DMS oracle: DMS-SPRNT-3, 73 tasks.

| Case | Skill | Result |
|---|---|---|
| attention queue DMS | po.attention_queue | count=108; top = DMS-352/DMS-379 (score 70, reasons blocked+aging_14d) — A219 parity |
| daily brief DMS | po.daily_brief | active 126 / blocked 8 / unassigned 8 / completed 21 / attention 108 — A219 parity |
| status report | po.status_report | total 147 / completed 21 / active 126 / blocked 8 / 14.3%; by_product: DMS 73/18/2, OLP 73/2/6, WMB 1/1/0, CRPV+STS NO_CURRENT_SPRINT null-preserved — A219 parity |
| reminder DMS-379 | po.reminder_draft | fresh key: dc=true, wp=false, requires_approval_for_send=true, REAL_AS21, recipient=bezrukov.p.s |

All 4 COMPLETED, bounded deltas (8/8/8/2), no tenant-wide scans.

## Phase 7 — source/write audit: PASS

Over the full task-api log (9885 lines, A219+A219R window):

- local factual reads (`GET /api/v1/tasks`): **0**
- mutations (POST/PUT/PATCH/DELETE): **0**
- unscoped task-query (no `space=`): **0**
- draft calls = bounded point reads only (DMS-999999 ×4 all 404; DMS-380/434/399/423/379
  unit+files pairs; OLP-33xx/WMB reads = A219 attention-queue attachment lookups, bounded
  by queue size, pre-existing window)
- user-only drafts = 0 source calls (P4)

## Phase 8 — inventory: PASS (unchanged)

- live registry: **67 skills / 12 plugins / 0 dups**; `agent.help` ×1; no dummy plugin in
  production discovery
- canonical coverage: **53/54**; missing = exactly **`[release.forecast]`**

## Findings (non-blocking)

1. **`_raw_unit_cache` negative cache (pre-existing, `7c06bc2`)**: 404→None is cached for
   the agent process lifetime. If a task key that 404'd earlier is later created in AS21,
   the same process will keep serving None until restart. Bounded and fail-safe (no
   fabrication; typed terminal), but the owner may want a bounded TTL or no-negative-cache
   policy for point reads. No action required for A219R GREEN.
2. **Valid-key draft = 2 bounded HTTP lines** (unit + `/files` attachment metadata) per
   `get_task` — consistent with A219; documented here so the "one point read" phrasing is
   read as "one logical task point read".

## Services

| Service | Address | PID |
|---|---|---|
| agent | 127.0.0.1:8212 @ `4ed98f8` | 82118 (fresh for controls) |
| task-api | 127.0.0.1:8241 | 81954 (system py3) |
| MCP-SWTR | 127.0.0.1:3000 | 29268 |
| UI | [::1]:5175 | 47416 |

## Artifacts

- `qa_219r_p2_results.json` / `qa_219r_p2_run.log` — 13-run P2
- `qa_219r_p2c_results.json` / `qa_219r_p2c_run.log` — fresh-process controls
- `qa_219r_p345_results.json` / `qa_219r_p345_run.log` — P3–P5 (9/9)
- `qa_219r_p6_results.json` / `qa_219r_p6_run.log` — P6 smoke
- `qa_219r_start_agent.sh`, runners `qa_219r_p2_runner.py`, `qa_219r_p2c_control.py`,
  `qa_219r_p345_runner.py`, `qa_219r_p6_runner.py`

## Recommendation

**Freeze an immutable Batch 5 checkpoint** (effective base = this GREEN regate on
`4ed98f8`). Next owner action = **isolated Batch 6 `release.forecast` source-contract
work** (the single remaining canonical gap, 53/54).
