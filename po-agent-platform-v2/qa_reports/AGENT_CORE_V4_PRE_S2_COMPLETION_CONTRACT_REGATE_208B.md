# AGENT CORE V4 — Pre-S2 Completion-Contract Re-Gate (A208B) — QA Report

**Assignment:** 208B — Pre-S2 completion-contract re-gate
**Role:** QA / adversarial + service-operator only (no production edits, no Wave S2, no new skills)
**START_HEAD:** `92a645b7041fc64c2f682b649241257484cb531d` (branch `feat/core8-real-query-hardening-v2`)
**Stable rollback checkpoint:** `checkpoint/v4-wave-s1-green@ce64264`
**Supersedes:** A208 RED report `f7e2942` (defect D-A208-1)
**Date:** 2026-09-23

---

## VERDICT

### **AGENT_CORE_V4_PRE_S2_COMPLETION_CONTRACT_GREEN**

Owner fix `98c06bd` (align Wave S1 completion contracts to the compacted observation shape: `task_keys` → `task_key_count`) + test `8f7197f` are **certified at unit level and live across all 60 API runs + 7 Browser C runs**: every previously-failing short-form/explicit-id `sprint.wip`/`sprint.scope` query now completes via **`runtime_contract`** with **zero** `ready_rejected=unsatisfied_completion_contract` and exact source parity. All A208 live closures (blocked↔health parity, raw-status filtering) retained.

**Recommendation: `PROCEED_TO_WAVE_S2_OWNER_IMPLEMENTATION`**

---

## Phase 0 — Pull / diff (`6519b87..92a645b`) — **PASS**

Owner delta limited to: `wave_s1.py` (4 lines: the two completion `data_keys` tuples), `tests/test_agent_core_v4_wave_s1.py` (+33, compaction-compatibility regression), docs/spec. Confirmed: **no Agent Core/planner/runtime edit, `_compact_data` unchanged, no `task_keys` restoration into planner context, no per-query/entity hardcode.**

## Unit-level chain (task_keys → compact_data → task_key_count → contract) — **PROVEN**

Real handler output → real `AgentCoreV4Runtime._compact_data` → real registry contract:

| Check | Result |
|-------|--------|
| Raw wip data has `task_keys`; compacted obs has `task_keys` removed, `task_key_count=1`, `task_keys_sample=['DMS-1']` | ✅ |
| Raw scope data → compacted `task_key_count=3`, no `task_keys` | ✅ |
| Live contracts: `sprint.scope` = (sprint_id, total, **task_key_count**); `sprint.wip` = (sprint_id, wip, **task_key_count**); velocity/throughput unchanged | ✅ |
| `is_skill_satisfied(sprint.wip)` on compacted obs | **True** (was False in A208) |
| `is_skill_satisfied(sprint.scope)` on compacted obs | **True** (was False in A208) |
| **Edge: wip=0** (only backlog+terminal tasks) → wip=0, task_key_count=0 → contract **valid** | ✅ True |

## Phase 1 — Automated tests — **GREEN (10 + 141)**

`test_agent_core_v4_wave_s1.py` + `test_agent_core_v4_task_search_source_status.py`: 10 passed; full `test_agent_core_v4*.py` + `test_v4*.py`: **141 passed**, 0 failures.

## Phase 2 — LLM preflight — **GREEN 3/3**

Planner-sized probes: 2.7 s / 0.8 s / 1.7 s — all within the 60 s budget, `finish_reason=stop`, non-empty content. Timeout unchanged.

## Phase 3 — Exact failing A208 forms (re-run) — **16/16 EXACT ✅ (D-A208-1 CLOSED)**

| Form | Runs | Result |
|------|------|--------|
| `wip спринта по DMS` | 5/5 | COMPLETED `runtime_contract`, **wip=30** of 68, sprint=DMS-SPRNT-3, 10.5–31.5 s |
| `WIP спринта DMS-SPRNT-3` | 3/3 | COMPLETED `runtime_contract`, wip=30 |
| `scope спринта по DMS` | 5/5 | COMPLETED `runtime_contract`, **68/17/51**, unassigned=5 |
| `scope спринта DMS-SPRNT-3` | 3/3 | COMPLETED `runtime_contract`, 68/17/51 |

- **0** `ready_rejected` across all 16 (A208: 4–5 per run).
- Fresh oracle (68 tasks): WIP=30 = 51 non-terminal − 21 backlog (Open 20 + Зарегистрирован 1); completed=17; open=51; unassigned=5 (DMS-349 new + DMS-421/389/104/166) — all exact.
- Success via the contract gate itself (`runtime_contract`), **not** via the contract-less `sprints.discover` bypass.

## Phase 4 — Period / current parity — **12/12 EXACT ✅**

| Form | Runs | Result |
|------|------|--------|
| `WIP сентябрьского спринта по DMS` | 3/3 | sprint=DMS-SPRNT-3, wip=30, `runtime_contract` |
| `scope сентябрьского спринта по DMS` | 3/3 | DMS-SPRNT-3, 68/17/51, `runtime_contract` |
| `WIP текущего спринта DMS` | 3/3 | DMS-SPRNT-3, wip=30, `runtime_contract` |
| `scope текущего спринта DMS` | 3/3 | DMS-SPRNT-3, 68/17/51, `runtime_contract` |

All forms resolve to the same authoritative sprint; exact parity with explicit-id forms; 0 rejections.

## Phase 5 — Blocked / status retain — **EXACT ✅**

Fresh oracle (68 tasks, blocked = 2: DMS-352/DMS-379).

| Form | Runs | Result |
|------|------|--------|
| Blocked explicit sprint | 3/3 | `task.search(sprint_id, status=blocked)` → exactly [DMS-352, DMS-379] |
| Blocked period | 2/2 | same exact keys (+space=DMS) |
| Blocked current | 2/2 | same exact keys |
| **sprint.health parity** | 2 runs | `total=68, completed=17, active=13, blocked=2` — **blocked count = 2 = task.search blocked count, same source moment** ✅ |
| `На исправлении` | 3/3 | exactly [DMS-399] |
| In review (known enum) | 1/1 | 6 keys exact |
| not_completed | 1/1 | 51 = 68−17 ✅ |
| completed | 1/1 | 17 ✅ |

## Phase 6 — Full S1 metric sanity — **GREEN ✅**

| Metric | Result |
|--------|--------|
| sprint.velocity (short) | 17, unit `tasks/sprint`, `story_points_available=false` (17 completed at 68-task moment) |
| sprint.throughput (short) | **1.702**, unit `completed_tasks/calendar_day`, elapsed 9.991 d from authoritative start 2026-09-13T21:00Z (=17/9.991) |
| sprint.wip / sprint.scope | P3/P4 above (30; 68/17/51) |

No semantic drift in units/formulas.

## Phase 7 — Retained high-risk regression — **GREEN ✅**

| Probe | Result |
|-------|--------|
| sprint.health (period) | 68/17/13/2 ✅ |
| DMS-380 lookup | Закрыт, Семавин, runtime_contract ✅ |
| task.history DMS-380 | 4 transitions, source labels intact ✅ |
| task.time_in_status DMS-380 | 4 intervals, terminal closure intact ✅ |
| Person+status (Жданов DMS) | 2 = [DMS-371, DMS-1] (live truth) ✅ |
| Unassigned DMS-SPRNT-3 | 5 exact (DMS-349, 421, 389, 104, 166) ✅ |
| Attachments WMB-30000 | 5 files ✅ |
| Same-session t1/t2 | t1 68 tasks; t2 "этом спринте заблокировано" → 2 [DMS-352, DMS-379] — session context + blocked predicate ✅ |
| **Browser C** (7 cases, screenshots in `qa_208b_browser_c/`) | **7/7 COMPLETED**, v4 panel rendered, no error text, no stale source text: wip-short 30/68, velocity 17 (+SP disclaimer), health 68/17/13/2, blocked explicit [352,379], blocked period [352,379], raw-status [DMS-399], scope-short 68/17/51/5 |

Release.search: `/versions` still independently HTTP 502 → remains SOURCE_CONDITIONAL (permitted by spec).

## Phase 8 — Architecture / source audit — **PASS**

- Local factual `GET /api/v1/tasks` (non-swtr) reads: **0**.
- Source calls all bounded/scoped: `sprints` (103), `spaces` metadata (34), per-task (8), task-query (1), assignees/resolve (1). No tenant-wide scan; planner observations remain compacted (no full `task_keys` arrays in context).
- dummy-55 / plugin registry invariant: **13/13 passed**.
- No hardcoded people/spaces/sprint ids/status labels in the diff.
- No fake/frozen/local factual fallback.

## Service health (left running)

| Service | Port | State |
|---------|------|-------|
| PO Agent (HEAD `92a645b`) | 8212 | `/live` 200 (PID 77110) |
| Task API (system python3) | 8241 | `/health` 200 |
| UI (IPv6 `[::1]`) | 5175 | 200 |
| MCP-SWTR | 3000 | connected (60+ live queries served) |
| `/versions` (release dir) | — | HTTP 502 (independent, pre-existing) |
| LLM endpoint (Qwen3.8-27B) | — | healthy; preflight 3/3 (0.8–2.7 s) |

**STOP.** Only this QA report committed; no production code modified; Wave S2 not started.
