# A229F2R3 — Fixed in-progress created-period re-gate

**Verdict:** `AGENT_CORE_V4_CREATED_PERIOD_STATUS_GREEN_A229F2R3`

**Classification:** `GREEN_FIXED_IN_PROGRESS_PLUGIN_CAPABILITY_CERTIFIED`

**START_HEAD:** `909bf51`
**Red checkpoint:** `b9259f3` (A229F2R2 — P2 in-progress+period planner RED)
**Green baseline:** `9d71a79` (A229F1R2)
**Date:** 2026-10-04
**No RED boundary — all gates pass.**

**Agent:** 127.0.0.1:8004 on `909bf51`, log `/private/tmp/qa229f2r3_agent.log`
**Oracle:** independent MCP-SWTR direct (`find_units_by_filter`, bypasses task-api), corpus `assigned_to=Kalachanov.V.V AND space=STS`

---

## Summary

| Phase | Requirement | Result |
|-------|-------------|--------|
| P0 | integrity / registry | ✅ GREEN |
| P1 | IN_PROGRESS + period via `task.search_created_in_progress`, 5/5 | ✅ GREEN (5/5, 0/0 REAL_EMPTY) |
| P2 | retained OPEN + period, 3/3, no in-progress routing | ✅ GREEN (3/3, 108/108) |
| P3 | recency-only, no invented status, 5/5 | ✅ GREEN (5/5, 108/108) |
| P4 | retained period controls + fail-closed fixture | ✅ GREEN (76/76, 32/32, fixture PASS) |
| P5 | architecture audit | ✅ GREEN (all 7 checks) |

The A229F2R2 RED (in-progress + created-period failed at the **planner** composition level, before the capability was ever invoked) is **closed**. The owner's plugin-only fix adds a dedicated `task.search_created_in_progress` capability whose canonical in-progress status is **fixed by the plugin binding** (`fixed_arguments={"status":"in_progress"}`), so the planner never has to compose the in-progress status. All gates pass against live REAL AS21.

---

## Owner fix (plugin-only)

Commits `b9259f3..909bf51`:
- `5b2b6d8` fix(plugin): add fixed in-progress created-period capability — new `task.search_created_in_progress` capability + skill + `CapabilityBindingV4(handler_builder=build_task_search_created, fixed_arguments={"status":"in_progress"})` + UI contract in `task_catalog.py`.
- `7268237` test(plugin): prove fixed in-progress created-period binding — 2 new tests (binding fixed_arguments + `_apply_fixed_arguments` override of a conflicting planner value).
- `4f44bb1` fix(plugin): simplify recency guidance for planner stability — rewrites the `task.search_created` skill text so recency is a creation-time constraint, not a workflow-state constraint, and points explicit in-progress + period to the dedicated capability.

Contract honored exactly: handler = existing `build_task_search_created`; fixed plugin argument = `status="in_progress"`; planner supplies only period/person/space; canonical 54 unchanged.

---

## P0 — Integrity / registry (GREEN)

### P0.1 Worktree
Clean (only `GIGACODE.md` = QA memory file, not production code).

### P0.2 Core files byte-identical to `9d71a79`

| File | Blob @ `909bf51` | Blob @ `9d71a79` | Match |
|------|------------------|------------------|-------|
| `contracts.py` | `20d93d5d` | `20d93d5d` | ✅ |
| `agent_core_v4.py` | `52100ca1` | `52100ca1` | ✅ |
| `agent_core_v4_robust.py` | `3bdb4d09` | `3bdb4d09` | ✅ |
| `api/v1/__init__.py` | `8f4b1663` | `8f4b1663` | ✅ |

**4/4 byte-identical.**

### P0.3 Production plugin registry

Instantiated via `discover_v4_plugins()`:
- skill `task.search_created_in_progress` exists ✅
- capability exists, args = `created_period, reference, space` (no `status` — the planner cannot supply one) ✅
- `binding.fixed_arguments == {"status":"in_progress"}` ✅
- `binding.handler_builder is build_task_search_created` ✅
- registry invariant `set(bindings) == set(capabilities)` (no mismatch) ✅
- UI contract present (widget `task_table`) ✅
- **fixed status is authoritative:** building the handler through `V4PluginRegistry._apply_fixed_arguments` and calling it with a deliberately conflicting planner `status="completed"` yields `data.status="in_progress"` ✅

### P0.4 Focused created-period tests
**8/8 passed** (A229F2R2 was 6/6; +2 = the two new fixed-binding tests).

### P0.5 Full V4 blast
**242 passed / 0 failed** (A229F2R2 was 240/240; +2).

---

## Independent REAL AS21 Oracle

MCP-SWTR direct, `assigned_to="Kalachanov.V.V" AND space="STS"`, 29 pages. Corpus **2812** tasks, **0** missing `created_at`. Drift **0** across every phase (2812 pre/post). Window for «последние 5 дней» = 00:00 Europe/Moscow of `current_day-4` (2026-09-30) through execution time.

| Phase | Filter | Count |
|-------|--------|-------|
| P1 (r3_p1) | in-progress (canonical) + last5 | **0** — REAL_EMPTY (all 99 corpus IN_PROGRESS tasks created ≤ 2026-09-08, before the window; the 108 in-window tasks are all `OPEN|pause`) |
| P2 (r3_p2) | open (not_completed) + last5 | **108** |
| P3 (r3_p3) | created-only + last5 | **108** |
| P4a (r3_p4a) | created-only + 29.09–01.10 | **76** |
| P4b (r3_p4b) | created-only + last2 | **32** |

---

## P1 — IN_PROGRESS + period via fixed capability (GREEN, 5/5)

Query: `Задачи Калачанова в работе в пространстве STS созданные за последние 5 дней`

All 5 runs **COMPLETED**, terminal capability `task.search_created_in_progress`, **0/0 exact key parity** (legitimate REAL_EMPTY):

| Run | terminal | observed status | n/0 | planner emitted status? | local/tenant |
|-----|----------|-----------------|-----|-------------------------|--------------|
| 1–5 | ✅ | `in_progress` | 0/0 | **no** | 0/0 |

Every requirement met:
- planner selects/loads `task.search_created_in_progress` ✅
- terminal capability = `task.search_created_in_progress` ✅
- planner arguments = `{"created_period":"последние 5 дней","reference":"Калачанова","space":"STS"}` — raw period + person + STS ✅
- planner did **not** emit status (not in the capability's arg set; fixed by binding) ✅
- executed handler observation shows fixed `status="in_progress"` ✅
- exact key/count parity 5/5 including legitimate REAL_EMPTY=0 ✅
- **must not broaden to all open tasks** — count=0 (not the 108 open) ✅
- 0 false zero / 0 local fallback / 0 tenant-wide scan ✅
- **0 bounded-repair failures** (the A229F2R2 RED class) before the fixed capability call ✅

`period_kind=last_5_calendar_days`, `source=REAL_AS21`, window `2026-09-30T00:00+03:00 → now`.

---

## P2 — Retained OPEN + period (GREEN, 3/3)

Query: `Открытые задачи Калачанова в пространстве STS созданные за последние 5 дней`

All 3 runs **COMPLETED**, terminal `task.search_created`, **108/108 exact parity**, observed `status="not_completed"`, planner emitted `status="not_completed"`, raw period + STS preserved. **No accidental routing to `task.search_created_in_progress`** — the capability list on every run is only `{space?/member}.resolve + task.search_created`. Drift 0.

---

## P3 — Recency-only wording (GREEN, 5/5)

Query: `Новые задачи Калачанова в STS за последние 5 дней`

All 5 runs **COMPLETED**, terminal `task.search_created`, **108/108 exact parity**:
- recency interpreted as `created_period="последние 5 дней"` ✅
- **no workflow status invented solely from «новые»** — observed status `null`, planner emitted no status ✅
- exact created-period parity for all completed runs ✅
- **5/5 deterministic** (the A229F2R2 P3 non-determinism — 2/3 planner bounded-repair — is closed by `4f44bb1` simplified recency guidance) ✅

---

## P4 — Retained period controls (GREEN)

| Run | Query | Oracle | Result |
|-----|-------|--------|--------|
| P4a | `… созданные за период с 29.09.2026 по 01.10.2026` | 76 | ✅ COMPLETED 76/76, `created_period="с 29.09.2026 по 01.10.2026"` (raw) |
| P4b | `… созданные за последние 2 дня` | 32 | ✅ COMPLETED 32/32, `created_period="последние 2 дня"` (raw) |
| P4c | missing authoritative `created_at` fixture | — | ✅ FAIL-CLOSED |

**P4c fixture control** (direct capability probe via the registry's `_apply_fixed_arguments` seam): with `_canonical_created_at_from_source=False`, **both** `task.search_created_in_progress` and `task.search_created` raise `AS21SourceUnavailable` (fail closed); with a source-backed `created_at` both complete. Confirms the new capability inherits the source-backed-timestamp fail-closed contract.

---

## P5 — Architecture audit (GREEN)

| Check | Result |
|-------|--------|
| canonical 54 unchanged (`skill_catalog.py`) | ✅ no diff vs `9d71a79` |
| extra skill/capability only | ✅ only `v4_plugins/task_catalog.py` (the in-progress capability) + `v4_plugins/_task_live_handlers.py` (A229F2R2 status filter) — both plugin files |
| 0 Agent Core/planner/runtime/session changes | ✅ (P0.2 + empty `src/` diff beyond the 2 plugin files) |
| no surname/space/day-count hardcode | ✅ `Калачанов`/`STS`/`5 дней`/`в работе` appear only in LLM-facing capability/skill **description text**, never in deterministic logic |
| no phrase-specific router | ✅ no `if/elif` on query text, no `startswith/includes` routing branch in the diff |
| fixed status uses generic plugin binding seam | ✅ `CapabilityBindingV4(handler_builder=build_task_search_created, fixed_arguments={"status":"in_progress"})`; `V4PluginRegistry._apply_fixed_arguments` (fixed wins over planner) |
| public/community repo remains unsynced until GREEN | ✅ `V4_A229F2R3_PUBLIC_SYNC = BLOCKED_UNTIL_GREEN`; only `origin` remote configured (no community remote, nothing pushed) |

---

## Source audit (all 15 live runs)

0 local `/api/v1/tasks` fallback reads · 0 tenant-wide scans · 38 scoped `swtr-read` GETs (all `space=STS&assignee=Kalachanov.V.V`). Every completed result `source=REAL_AS21`.

---

## Verdict & recommendation

**`AGENT_CORE_V4_CREATED_PERIOD_STATUS_GREEN_A229F2R3`** — all six gates pass against live REAL AS21. The A229F2R2 in-progress+period planner RED is closed by a plugin-only fixed-status capability; the plugin status filter, open/created-period retained paths, recency-only semantics, and fail-closed contract are all retained.

- Recommend checkpoint `checkpoint/v4-created-period-status-green-a229f2r3`.
- Owner may now sync the certified plugin change to the public/community repo (currently `BLOCKED_UNTIL_GREEN`).
- Return to the stabilized release-hardening roadmap.

---

## Services left running

- Agent V4: 127.0.0.1:8004 on `909bf51`, log `/private/tmp/qa229f2r3_agent.log`
- Task API: 127.0.0.1:8241
- MCP-SWTR SSE: 127.0.0.1:3000
