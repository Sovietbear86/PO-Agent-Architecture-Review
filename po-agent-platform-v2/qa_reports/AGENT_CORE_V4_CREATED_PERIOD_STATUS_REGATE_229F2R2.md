# A229F2R2 — Created-Period + Status Re-Gate

**Verdict:** `AGENT_CORE_V4_CREATED_PERIOD_STATUS_RED_A229F2R2`

**Classification:** `RED_P2_PLANNER_COMPOSITION_INPROGRESS_PERIOD` (planner reliability; plugin status logic proven correct)

**START_HEAD:** `0ed5cf4`
**Checkpoint:** `9d71a79` (A229F1R2 GREEN)
**Date:** 2026-10-04
**STOP at:** P2 (in-progress + created period) — first failing boundary

**Agent:** PID 99530 @ `0ed5cf4`, log `/private/tmp/qa229f2r2_agent.log`
**Oracle:** independent MCP-SWTR direct (`find_units_by_filter`, bypasses task-api), corpus `assigned_to=Kalachanov.V.V AND space=STS`

---

## Summary

| Phase | Requirement | Result |
|-------|-------------|--------|
| P0 | integrity / retained test gate | ✅ GREEN |
| P1 | OPEN + created period, 5/5 exact | ✅ GREEN (5/5, 108/108) |
| P2 | IN_PROGRESS + created period, 3/3 exact | ❌ **RED (3/3 FAILED, first boundary)** |
| P3 | «Новые задачи» no invented status, 3/3 | ⚠️ partial (2/3 FAILED, 1/3 exact) — run for diagnostics |
| P4 | retained A229F1R2 (explicit + relative) | ✅ GREEN (76/76, 32/32) |
| P5 | architecture audit | ✅ GREEN |

The owner's **plugin change is correct**: the `status` filter on `task.search_created` is proven at the capability level (open→108, closed→0, created-only→108/76/32, all exact). The RED is a **planner-composition reliability gap** specific to the *in-progress + created-period* composite, which fails before the capability is ever invoked.

---

## P0 — Integrity (GREEN)

### P0.1 Core files byte-identical to checkpoint `9d71a79`

| File | Blob @ `0ed5cf4` | Blob @ `9d71a79` | Match |
|------|------------------|------------------|-------|
| `contracts.py` | `20d93d5d` | `20d93d5d` | ✅ |
| `agent_core_v4.py` | `52100ca1` | `52100ca1` | ✅ |
| `agent_core_v4_robust.py` | `3bdb4d09` | `3bdb4d09` | ✅ |
| `api/v1/__init__.py` | `8f4b1663` | `8f4b1663` | ✅ |

**4/4 byte-identical.** No Core/planner/runtime/session modifications.

### P0.2 Owner diff audit (vs `9d71a79`)

The `A229F2R → A229F2R2` delta is **test-only** (1 line): `TaskStatus.DONE` → `{TaskStatus.CLOSED, TaskStatus.CANCELLED, TaskStatus.RESOLVED}` in `test_agent_core_v4_task_created_period.py:28`. `git diff 79f5191..0ed5cf4 -- src/` is **empty** — zero production change since A229F2R. The full plugin diff vs checkpoint remains the A229F2 set (plugin-only, 2 files + test), confirmed identical to the DOD lock (`V4_A229F2R2_CORE_DIFF = ZERO`, `V4_A229F2R2_PLUGIN_DIFF = SAME_AS_A229F2`).

### P0.3 Focused created-period tests

**6/6 PASSED** (was 4F/2P in A229F2R):

| Test | Result |
|------|--------|
| `test_created_period_parses_explicit_inclusive_dates` | ✅ |
| `test_created_period_parses_last_two_calendar_days` | ✅ |
| `test_created_period_search_filters_only_source_created_timestamps` | ✅ |
| `test_created_period_search_fails_closed_if_created_at_is_not_source_backed` | ✅ |
| `test_created_period_search_preserves_open_status_constraint` | ✅ |
| `test_created_period_search_preserves_in_progress_status_constraint` | ✅ |

### P0.4 Full V4 blast

**240 passed / 0 failed** (A229F1R2 baseline 238 + 2 new status tests). No regressions.

---

## Independent REAL AS21 Oracle

MCP-SWTR direct, `find_units_by_filter`, `assigned_to="Kalachanov.V.V" AND space="STS"`, 29 pages. Corpus **2812** tasks, **0** missing `created_at`. Window for «последние 5 дней» = 00:00 Europe/Moscow of `current_day-4` (2026-09-30) through execution time.

Oracle sets (canonical semantics mirrored from `domain/models.py` + `adapters/task_api.py`):

| Phase | Filter | Count | Note |
|-------|--------|-------|------|
| P1 | open (not_completed) + last5 | **108** | all 108 in-window are `OPEN|statusType=pause` (non-terminal) |
| P2 | in_progress (canonical) + last5 | **0** | the 99 corpus IN_PROGRESS tasks were all created **before** the 5-day window → genuine REAL_EMPTY |
| P3 | created-only + last5 | **108** | (== P1 because every in-window task is open) |
| P4a | created-only 29.09–01.10 | **76** | explicit inclusive range |
| P4b | created-only + last2 | **32** | 00:00 MSK 2026-10-03 → now |

Source drift across all phases: **0** (corpus stable at 2812 pre/post every phase).

---

## P1 — OPEN + created period (GREEN, 5/5)

Query: `Открытые задачи Калачанова в пространстве STS созданные за последние 5 дней`

All 5 runs **COMPLETED runtime_contract**, terminal capability `task.search_created`, **108/108 exact key parity**:

| Run | status | n/108 | parity | created_args | task.search_status? | raw wording |
|-----|--------|-------|--------|--------------|---------------------|-------------|
| 1–5 | COMPLETED | 108 | ✅ | `{"created_period":"последние 5 дней","reference":"Калачанов","space":"STS","status":"not_completed"}` | none | preserved |

Every requirement met: terminal capability = `task.search_created`; raw `created_period` preserved; person + STS + explicit open status (`not_completed`) preserved; **no separate terminal `task.search_status`**; exact parity 5/5; every result satisfies both period and open constraints; 0 false zero / 0 local fallback / 0 tenant-wide scan.

---

## P2 — IN_PROGRESS + created period (RED — first failing boundary)

Query: `Задачи Калачанова в работе в пространстве STS созданные за последние 5 дней`

**3/3 FAILED** (formal run) + **1/1 FAILED** (confirming probe) = **4/4 deterministic**.

```
p2-1 FAILED  caps=[member.resolve]  created=never-called  err=planner failed robust bounded repair: [ValidationError ×4]
p2-2 FAILED  (same)
p2-3 FAILED  (same)
probe        FAILED (same)
```

### Trajectory (diagnostic probe, full dump)

```
turn 1: load_skill  tasks.search
turn 2: call member.resolve {reference: "Калачанов", space: "STS"}   → 200 OK (canonical login)
turn 3: (task.search_created composition) → 4× ValidationError during robust bounded repair
        → FAILED: "planner failed robust bounded repair: ['ValidationError' ×4]"
```

The failure is **at the planner level, before `task.search_created` is invoked** — the owner's status-filter code never runs. 0 local reads, 0 tenant scans, 0 fabrication.

### Discriminating evidence (capability is correct; planner is the gap)

| Query (person + status + STS + last5) | Planner status value | Result |
|----------------------------------------|----------------------|--------|
| `Открытые …` (open) | `not_completed` | ✅ 5/5 COMPLETED 108/108 |
| `Закрытые …` (closed) *(probe)* | `completed` | ✅ COMPLETED **n=0** (correct — all 108 in-window are open) |
| `… в работе …` (in-progress) | in-progress | ❌ **4/4 FAILED** (planner bounded repair) |

- `open` and `closed` (binary not_completed/completed) compose and complete correctly; the `closed` run returning a **correct 0** proves the status filter actually filters (a broken filter would return 108).
- Only the **in-progress** representation of the status fails, and it fails at plan composition, not capability execution.

### Classification

This is a **planner (Qwen3.8-27B) composition reliability gap** on the *in-progress + created-period* composite — the same class as A179 / A219-F3 / A227R2-P3B (person + composite → `bounded repair: ValidationError`). It is a **newly tested query class** (created-period + in-progress status was not expressible as a single call before the A229F2 `status` arg), so it is not a regression of previously-green behavior. The open/closed contrast rules out the new "call with both created_period and status" procedure sentence as the primary cause (it affects open/closed identically, and they pass); the gap is specific to how the model represents the in-progress status value in this composite. A prompt A/B vs the pre-change procedure text was not performed (would require rollback; out of QA-only scope), so a minor contributing effect of the new procedure text cannot be 100% excluded.

**The plugin `status` filter is proven correct** — the defect is not in the owner's plugin code.

---

## P3 — «Новые задачи» without invented status (partial, diagnostic)

Query: `Новые задачи Калачанова в STS за последние 5 дней`

| Run | status | n/108 | created_args |
|-----|--------|-------|--------------|
| 1 | ❌ FAILED | — | planner bounded repair ValidationError |
| 2 | ❌ FAILED | — | planner bounded repair ValidationError |
| 3 | ✅ COMPLETED | 108/108 | `{"created_period":"последние 5 дней","reference":"Калачанов","space":"STS"}` (no status) |

The successful run (p3-3) is exactly correct: creation-period semantics preserved, **no workflow status invented from «новые»**, exact created-only parity (108/108). The 2 failures are the same planner bounded-repair class. Note the owner's new procedure sentence literally names this wording («новые задачи … за последние N дней» / do not invent `New`); the 2/3 non-determinism is consistent with that instruction making the model hesitate on «новые». P3 was run for diagnostics only (after the P2 stop boundary).

---

## P4 — Retained A229F1R2 (GREEN)

| Run | Query | Oracle | Result |
|-----|-------|--------|--------|
| P4a | `… созданные за период с 29.09.2026 по 01.10.2026` | 76 | ✅ COMPLETED 76/76, `created_period="с 29.09.2026 по 01.10.2026"` (raw) |
| P4b | `… созданные за последние 2 дня` | 32 | ✅ COMPLETED 32/32, `created_period="последние 2 дня"` (raw) |

Fixture control for missing authoritative `created_at` (fail-closed) is retained and unit-proven in P0.3 (`test_created_period_search_fails_closed_if_created_at_is_not_source_backed` ✅). Retained semantics intact.

---

## P5 — Architecture audit (GREEN)

| Check | Result |
|-------|--------|
| canonical 54 unchanged (`skill_catalog.py`) | ✅ no diff |
| plugin-only extension | ✅ only `v4_plugins/_task_live_handlers.py` (+12) + `v4_plugins/task_catalog.py` (+6) |
| 0 Core/planner/runtime/session changes | ✅ (P0.1 + empty `src/` diff beyond the 2 plugin files) |
| no surname/STS/5-day special route | ✅ no `Kalachanov`/`STS` literals in code (only a generic example in the LLM-facing skill text) |
| no phrase router | ✅ no deterministic phrase→behavior branch |
| bounded source read | ✅ `_live_query` limit=100/max_pages=100, space+assignee scoped; live audit `tenant_scan=0` on every run |
| existing generic status matcher reused | ✅ `build_task_search_created` calls the **pre-existing** `_matches_requested_status` (not added by this diff) |

---

## Audit (all live runs)

0 local `/api/v1/tasks` fallback reads · 0 tenant-wide scans · 0 mutations. All `task-query` reads scoped `space=STS&assignee=Kalachanov.V.V`. Every completed result `source=REAL_AS21`, `period_kind` correct.

---

## Owner action (proposed, not implemented)

The plugin is correct and needs no change. The blocking gap is **planner reliability for the in-progress + created-period composite** (P2, 4/4 deterministic):

1. Harden the planner for `task.search_created` carrying an in-progress status + `created_period` — e.g. constrained/structured output for the decision, or a deterministic fallback that emits `task.search_created{reference, space, created_period, status=<in-progress>}` when the query contains an in-progress status + a creation period (the A179/A219-F3/A227R2 lineage fix).
2. Optionally, review the P3 «новые» non-determinism (2/3): the new "do not invent `New`" procedure sentence matches the P3 wording verbatim; consider rephrasing so it does not destabilize plan composition on recency-only queries.
3. Add a non-mocked regression: in-progress + created-period must complete via a single `task.search_created` carrying the in-progress status (no premature/absent call).

Then re-gate **P2 (≥3/3 exact, oracle REAL_EMPTY=0 with status preserved, no broadening to the 108 open)** and re-confirm P1/P3/P4.

---

## Services left running

- Agent V4: 127.0.0.1:8004 (PID 99530 @ `0ed5cf4`), log `/private/tmp/qa229f2r2_agent.log`
- Task API: 127.0.0.1:8241
- MCP-SWTR SSE: 127.0.0.1:3000
- Vite UI: 127.0.0.1:5175
