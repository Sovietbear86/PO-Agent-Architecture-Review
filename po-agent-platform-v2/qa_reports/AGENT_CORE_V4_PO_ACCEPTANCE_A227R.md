# A227R PO Acceptance (resume P3–P7) — QA Report

**Verdict:** `AGENT_CORE_V4_PO_ACCEPTANCE_RED_A227R`
**Classification:** `RED_P3_C_FALSE_ZERO_STATUS_LITERAL` (A227-C class, non-deterministic 4/5)
**START_HEAD:** `4ef4bd374908772ba3c0462e76781d332c59f17b`
**Code HEAD (unchanged since R2):** `cb90f479c34fc37684d89592ada97855b0d821a0`
**Branch:** `feat/core8-real-query-hardening-v2`
**Date:** 2026-09-30
**Role:** QA/adversarial tester only. No code modified.

**Stopped at P3 (first RED). P4–P7 not executed. P3 cases A/B/D not executed (C probed first and failed).**

---

## Scope note

Pre-gate R2 is GREEN and the owner's `4ef4bd3` change is **docs-only** (`git diff --stat cb90f47..4ef4bd3`
over `src`/`tests`/`frontend/src`/`task-api` is **empty**). Live code == `cb90f47`, which R2 already
certified (zero Core diff vs `db5e35f`, full V4 229/229, Tasks/Sprint/Release UI parity GREEN). Services
reused from R2 (agent 8004, task-api 8241, MCP 3000, vite 5175) — all confirmed listening and healthy.
P0–P2 were **not** repeated per the assignment.

---

## P3 — multi-constraint composition: RED (Case C)

Independent REAL AS21 oracles were captured **before** running the agent (read-only task-api routes):

| Case | Oracle (REAL AS21) |
|---|---|
| **A** `Открытые задачи Калачанова с вложениями в WMB` | 5 WMB Kalachanov tasks, **all `done`** (3× Закрыт, 2× Решен) → **0 open** (legit REAL_EMPTY) |
| **B** `Задачи Семавина по рискам` | Semavin.M.M = 346 tasks, 22 open across OLP/DMS |
| **C** `Задачи в работе в сентябрьском спринте по DMS` | DMS-SPRNT-3 (Sept, IN_PROGRESS) = 79 tasks; **26** with `statusType=progress`; **11** canonical IN_PROGRESS (10× "In progress" + 1× "На исправлении") |
| **D** `Спринты в DMS` | 3 sprints (DMS-SPRNT-1 FINISH, DMS-SPRNT-2 FINISH, DMS-SPRNT-3 IN_PROGRESS) |

### Case C — 5-run matrix → FIRST RED (false zero)

| run | planner `status` arg | agent count | expected | outcome |
|---|---|---|---|---|
| 1 | `"В работе"` | **0** | 11 (or 26) | **FALSE ZERO** |
| 2 | `"В работе"` | **0** | 11 (or 26) | **FALSE ZERO** |
| 3 | `"В работе"` | **0** | 11 (or 26) | **FALSE ZERO** |
| 4 | `"В работе"` | **0** | 11 (or 26) | **FALSE ZERO** |
| 5 | `"In Progress"` | **11** | 11 | ✅ correct — keys `DMS-343,452,357,349,269,272,399,405,253,104,401` |

**4/5 runs returned a confident FALSE ZERO** (status `COMPLETED`, "задач … не найдено — количество 0")
while the source holds 11 canonical in-progress (26 statusType=progress) tasks in DMS-SPRNT-3.
Per the assignment, **"false zero is RED"**. This is the **A227-C defect class** (status-literal
language sensitivity), still present on the generic `task.search` path.

### What is correct in Case C (not the defect)
- **Sprint resolution is source-backed and correct**: all 5 runs did `space.resolve(DMS)` →
  `sprint.search(DMS, period=сентябрь)` → `DMS-SPRNT-3` (IN_PROGRESS). The A227 `sprints.discover`
  mis-routing is gone.
- **No tenant-wide scan**: 34× bounded `sprints/DMS-SPRNT-3/tasks?complete=true&limit=100&max_pages=500`;
  0 unscoped `task-query` calls in the whole session.
- **No fabrication**: run 5's 11 keys are real DMS-SPRNT-3 in-progress tasks.

### Root cause (mechanism, proven by code trace)
The query phrase is Russian («в работе»). The LLM planner non-deterministically emits either the Russian
literal or the English canonical as the `status` argument:

1. `_safe_status` (`agent_core_v4.py:690`) recognizes Russian **open/completed** terms
   (`открытые`/`незакрытые` → not_completed; `закрытые`/… → completed) but **has no Russian
   in-progress mapping**. So `"В работе"` passes through **unchanged**.
2. The literal-status filter (`agent_core_v4.py:987-995`) then does a **substring** match:
   `"в работе" in status_raw / status_type / status.value / status_category.value`.
3. Stored values are **English** (`"In progress"`, `"progress"`) → the Russian term never substring-matches
   → **every in-progress task is filtered out → count 0**.
4. When the planner instead emits `"In Progress"`, `"in progress" in "in progress"` matches the 10
   "In progress" rows + the "На исправлении" row (normalized to `TaskStatus.IN_PROGRESS`, whose
   `.value` is `"In progress"`) → **11**, the correct canonical set.

The same latent gap exists in the plugin's `_matches_requested_status`
(`v4_plugins/_task_live_handlers.py`) — it maps `normalized == "progress"` to `status_type=="progress"`,
but only if the input is *already* normalized to `"progress"`; a raw Russian `"В работе"` also falls
through to the language-sensitive substring match there. Case A did not expose it because Kalachanov's
WMB tasks are all terminal (0 open regardless).

### Owner fix (proposed, not implemented)
Add Russian in-progress literals to the status normalizer so both the generic `task.search` and the
attachment handlers converge on the canonical progress status, e.g. in `_safe_status`:
`"в работе" / "в работе" / "in work" / "работе" / "in progress"` → canonical `IN_PROGRESS`
(or `progress`, matching the existing `"progress" → status_type=="progress"` branch in the plugin).
Equivalently, make the literal-status filter **language-insensitive** by normalizing both the requested
status and each candidate status to a canonical enum before comparison (the `normalize_task_status`
map in `domain/models.py` already maps `"в работе" → TaskStatus.IN_PROGRESS` — it is simply not applied
at this boundary). Then a non-mocked regression: «Задачи в работе в сентябрьском спринте по DMS» must
return the exact in-progress key set (11), never 0.

---

## Phases not executed (stop rule)

- **P3 A / B / D** — not run (C probed first and returned the first RED; A's answer is already proven
  REAL_EMPTY=0 in R2 P1 and by the fresh oracle).
- **P4** task cards / persistence — not run.
- **P5** Quality refresh isolation — not run.
- **P6** Aging live parity — not run.
- **P7** retained regression — not run.

## Services left running
agent 8004 (PID 15107 @ cb90f47), task-api 8241 (PID 15039, system python3), MCP-SWTR 3000 (PID 25954),
vite `[::1]:5175` (PID 15218, proxy `/api`→8004).

## Evidence files
- Oracles: `/private/tmp/qa227r_oracles.json` (builder `qa_227r_oracles.py`)
- Case C 5-run matrix: `/private/tmp/qa227r_p3c_5runs.json` (`qa_227r_p3c_5runs.py`)
- Case C probe: `/private/tmp/qa227r_probe_qa227r-probe-c.json` (via `qa_227r_probe_c.py`)
- Row structure dump: `qa_227r_rowdump.py`
