# A227R2 — P3-C re-gate, then resume — QA Report

**Verdict:** `AGENT_CORE_V4_PO_ACCEPTANCE_RED_A227R2`
**Classification:** `RED_P3_B_PLANNER_COMPOSITION_RELIABILITY` — **pre-existing, NOT a regression from the owner's plugin fix** (proven by A/B test on pre-fix `cb90f47`).
**START_HEAD:** `b5c0f9655cbbc62e1cc133c94302f5724b4da137`
**A227 baseline:** `db5e35f1b378b6ffde0c10085af8b68e4bf1e6b5`
**Branch:** `feat/core8-real-query-hardening-v2`
**Date:** 2026-09-30
**Role:** QA/adversarial tester only. No code modified.

**Stopped at P3-B (first RED). P4–P7 not executed per spec ("If all P3 GREEN, continue" / "If RED … STOP").**

**Headline:** the owner's status-normalization fix is **correct and P3-C is GREEN (5/5 + control)**. The sole
blocker, P3-B, is a **pre-existing planner-reliability defect** that reproduces identically on the pre-fix
code — it is out of scope for this plugin-only fix.

---

## P0 — focused integrity: GREEN

### P0.1 worktree
Pulled clean. Tracked worktree clean.

### P0.2 exact zero diff vs A227 baseline — PROVEN
`git diff db5e35f..b5c0f96` over the stable Core/LLM files is **empty**:
`agent_core_v4.py`, `agent_core_v4_reliable.py`, `agent_core_v4_robust.py`, `agent_core_v4_pluginized.py`,
`llm/real.py`, `test_agent_core_v4_reliable.py`, `test_agent_core_v4_robust_protocol.py` — all byte-identical
to the A227 baseline.

The owner's fix is **plugin-only** (changed vs baseline):
- `v4_plugins/core.py` — new `build_task_search` wrapper: normalizes a domain-recognized IN_PROGRESS literal
  (`normalize_task_status(raw) == TaskStatus.IN_PROGRESS`, e.g. Russian "в работе") to the canonical
  `TaskStatus.IN_PROGRESS.value` ("In progress") **before** calling the untouched core `_task_search`.
- `v4_plugins/_task_live_handlers.py` — same IN_PROGRESS normalization in `build_task_search_status` and
  `_matches_requested_status` (attachment composition); `status` surfaced on attachment results.
- `v4_plugins/task_catalog.py` — `status` arg + "preserve status" wording on the 4 attachment/search
  capabilities. **`task.search_text` spec is unchanged** (verified: `search_text` absent from the diff).
- `tests/test_agent_core_v4_attachment_sprint_scope.py`, new `tests/test_agent_core_v4_plugin_status_normalization.py`.

`normalize_task_status("в работе")` and `("in progress")` both → `TaskStatus.IN_PROGRESS` (models.py:182)
→ value `"In progress"`, so the localized and English literals converge on the same governed predicate.

### P0.3 focused tests + blast radius — GREEN
- Focused (plugin status normalization, attachment sprint/status, reliable/robust, wave_s2): **37/37 passed**.
- Full V4 blast radius (`tests/test_agent_core_v4*.py tests/test_v4*.py`): **231/231 passed**.

### P0.4 services
Agent restarted on `b5c0f96` (plugin changed); task-api 8241, MCP 3000, vite 5175 reused (verified
byte-identical since `cb90f47`). Liveness + source health 200 (48 MCP tools).

---

## P3-C first — 5/5 exact parity: GREEN (the fix works)

Query: `Задачи в работе в сентябрьском спринте по DMS`
Fresh independent REAL AS21 oracle (captured immediately before runs): **DMS-SPRNT-3 = 79 tasks**,
statusType `{pause:25, progress:26, done:28}`; canonical IN_PROGRESS set = **11 tasks**
(raw names "In progress"×10 + "На исправление"×1) =
`DMS-104,253,269,272,343,349,357,399,401,405,452`.

| run | planner `status` arg | count | exact key parity | false zero |
|---|---|---|---|---|
| 1–4 | `"В работе"` (Russian) | **11** | **True** (exact 11) | False |
| 5 | `"In Progress"` (English) | **11** | **True** (exact 11) | False |
| control (timestamped window) | `"В работе"` | **11** | **True** | False |

- **Russian `В работе` and English `In Progress` converge on the same 11 canonical IN_PROGRESS keys** — the
  A227R false-zero defect is **closed**.
- All 6: source-backed Sept sprint resolution (`space.resolve(DMS)` → `sprint.search(period=сентябрь)` →
  DMS-SPRNT-3), terminal task collection, `sprint_id`+`status` preserved, `runtime_contract` completion.
- **No tenant-wide scan**: a timestamped log-window control shows P3-C's actual source calls are only
  `spaces/DMS/sprints` + `sprints/DMS-SPRNT-3/tasks?complete=true&limit=100&max_pages=500` (bounded).
  (The 29 accumulated `task-query` lines in the long-lived task-api log are **not** from P3-C — they are
  assignee-scope lookups from other traffic, all bounded by `assignee=`/`space=`.)

---

## P3 remaining

### P3-A `Открытые задачи Калачанова с вложениями в пространстве WMB` — GREEN (3/3 + probe)
Fresh oracle: 5 WMB Kalachanov tasks, **all terminal** (3× Закрыт, 2× Решен) → 0 open.
Agent: 3/3 COMPLETED, terminal `task.search_attachments(space=WMB, reference=Kalachanov.V.V,
status=not_completed)`, **count=0, source=REAL_AS21** — a valid, grounded REAL_EMPTY (not a false zero),
all constraints preserved. No repair-loop failure, no tenant scan.

### P3-D `Спринты в DMS` — GREEN (3/3 + probe)
Fresh oracle: 3 sprints (DMS-SPRNT-3 IN_PROGRESS, DMS-SPRNT-1 FINISH, DMS-SPRNT-2 FINISH).
Agent: 3/3 COMPLETED, terminal `sprint.list(space=DMS)`, **count=3**, grounded rich non-task table with
codes/statuses/periods. Exact match to oracle.

### P3-B `Задачи Семавина по рискам` — **RED (first failing gate) → STOP**

Requirement: source-backed identity, compositional task/risk path, no fabricated rows, **5/5 correct**.

**Observed (code under test `b5c0f96`):** non-deterministic. Three 5-run batches:

| batch | COMPLETED | FAILED | failure signature |
|---|---|---|---|
| 1 | 2/5 | 3/5 | `V4ContractError: planner failed robust bounded repair` (`ValidationError`×4) |
| 2 | 0/5 | 5/5 | same; runs 4–5 were 0.02 s = `ConnectError`×4 (LLM endpoint `api.ai.sbt` transiently unreachable) |
| 3 (after LLM recovered) | 0/5 | 5/5 | `ValidationError`×4, trajectory `load_skill → member.resolve → [invalid task.search_text]` |

**Characterization (proven):**
1. **Not a false zero.** When B *does* complete, it returns `count=0` via `task.search_text(phrase=риски,
   reference=Семавин)`. The source confirms Semavin.M.M has **0** of 346 tasks with "риск"/"risk" in
   title/description → count=0 is a **legitimate REAL_EMPTY**, and the 2/5 that completed were factually
   correct.
2. **The failure is a planner bounded-repair failure**, `V4ContractError: planner failed robust bounded
   repair` (`warnings=['v4_runtime_failure']`). The LLM intermittently emits a schema-invalid next action
   (the `task.search_text` call) after `member.resolve`, and the 4-attempt repair cannot recover. Safe
   fail-closed: typed failure, **no fabrication, no source corruption**.
3. **Pre-existing, NOT a regression from the plugin fix — A/B tested.** Restarted the agent on **pre-fix
   `cb90f47`** and re-ran B 5×: **1/5 COMPLETED + 4/5 FAILED** with the identical
   `V4ContractError: planner failed robust bounded repair` signature. The fix does not touch the planner,
   the repair protocol, the validator, or `task.search_text` (spec unchanged). → The B failure is the
   **pre-existing person+composite planner-reliability class** (A179 / A219-F3 / A227-F3 / A200 lineage).
4. **Environmental amplifier:** batch 2's instant failures were `ConnectError` (LLM endpoint outage window,
   the A205R class); the P3-C control succeeded with LLM 200s immediately after, confirming recovery.

**B is not 5/5 correct → RED → STOP** (P4–P7 not executed).

---

## Final source audit (whole session)
- **0 local-store factual reads** (no non-`swtr-read` `GET /api/v1/tasks|sprints|releases`).
- **0 unauthorized mutations** (no POST/PUT/DELETE to swtr-read; only `POST /api/v1/query`).
- **0 fully-unscoped tenant scans** (every `task-query` carries `space=` or `assignee=`; P3-C bounded sprint route).

---

## Phases not executed (stop rule)
P4 (task cards/persistence), P5 (Quality refresh isolation), P6 (Aging live parity), P7 (retained
regression/source audit) — **not run** because P3-B is RED.

## Services left running
agent 8004 (PID 94541 @ b5c0f96, restored after the A/B test), task-api 8241 (PID 15039), MCP-SWTR 3000
(PID 25954), vite `[::1]:5175` (PID 15218).

## Evidence files
- P3-C oracle + 5-run matrix: `/private/tmp/qa227r2_p3c/` (`qa_227r2_p3c.py`)
- P3-C timestamped window control: `qa_227r2_p3c_window.py`
- P3-A/B/D oracles + probes: `/private/tmp/qa227r2_p3abd/` (`qa_227r2_p3abd_probe.py`)
- P3-B 5-run matrices: `/private/tmp/qa227r2_p3b/` (`qa_227r2_p3b.py`); b5c0f96 backup
  `/private/tmp/qa227r2_p3b_b5c0f96_results.json`
- **P3-B pre-fix A/B test**: `/private/tmp/qa227r2_p3b_prefix/` (`qa_227r2_p3b_prefix.py`, run on cb90f47)
- P3-B false-zero check: `qa_227r2_p3b_falsezero.py`; P3-A/D 3× confirm: `/private/tmp/qa227r2_p3ad/`

---

## Recommendation

The **owner's status-normalization fix is correct**: P0 (zero Core diff + 231/231) and **P3-C 5/5 (+ control
6/6)** are GREEN — the A227R Russian-literal false zero is closed, with Russian/English converging on the
canonical IN_PROGRESS set and no tenant scan. **Do not revert the fix.**

The sole blocker, **P3-B, is a pre-existing planner-reliability defect** (proven to reproduce on pre-fix
`cb90f47`), not a regression. Before re-gating, the owner should harden the planner for **person+composite**
queries (constrained/structured-output decoding or a deterministic fallback for the `member.resolve →
task.search_text` pattern, and a non-mocked regression for "Задачи Семавина по рискам"), per the A179 /
A219-F3 / A227-F3 lineage. Then re-run P3-B to 5/5 and resume P4–P7.

Because the acceptance gate requires **all** of P3 to be GREEN and B is not, the verdict is RED — with the
explicit finding that this is **not** attributable to the under-test fix.
