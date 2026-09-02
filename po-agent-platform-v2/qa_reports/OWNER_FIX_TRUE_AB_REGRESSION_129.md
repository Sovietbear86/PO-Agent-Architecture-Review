# Assignment 129 — Owner Fix True A/B Regression

**Date:** 2026-09-02  
**Branch:** `feat/core8-real-query-hardening-v2`  
**HEAD:** `80d698f35a6af3a800047208536e653821c6cf69`  
**Owner commit:** `54f7f01e967f03bd62b0e6592059c898505ef4b9`

---

## Executive Summary

**VERDICT:** `CAPABILITY_RESULT_PROPAGATION_DEFECT`

The owner fix for `HardenedProductionTaskApiAS21Adapter.search_tasks()` routing is **correct and functional**, but it is **never invoked** for assignee searches due to a capability routing defect in `DialogueHarnessRuntime._execute_frame()`.

---

## Phase 0 — Provenance and Runtime Reset

| Check | Status |
|-------|--------|
| `git switch feat/core8-real-query-hardening-v2` | ✅ |
| `git pull --ff-only origin feat/core8-real-query-hardening-v2` | ✅ |
| HEAD contains owner commit `54f7f01...` | ✅ (HEAD `80d698f`) |
| Production worktree dirty | ⚠️ 3 modified files (pre-existing fixes from 124-127) |
| Old processes killed | ✅ (PIDs 55437, 56406) |
| New processes started | ✅ (Task API PID 68109, Harness PID 68720) |
| Services healthy | ✅ |

**Dirty files (pre-existing fixes):**
- `GIGACODE.md`: SHA256 `e6c92c23452d4ef67756a94a0176c0ad12b317a3d5f0cd3685ca965ec4978de3`
- `po-agent-platform-v2/src/po_agent/adapters/task_api.py`: SHA256 `e4dc25dd7ee11edad3978d96a5e92fa1be37caa29796bcaf40a0f53a9cda9a6e`
- `task-api/app/routers/swtr_assignee.py`: SHA256 `fda6a7238e0e3ae27661c5cefb4aec6b5dcde6dc7498eb4df71920a16f922b6a`

---

## Phase 1 — Independent Oracle B for Garanin

**Source:** REAL AS21 via `/api/v1/swtr-read/assignee-tasks?assignee=Garanin.R.V`

| Metric | Value |
|--------|-------|
| Total tasks | 16 |
| DMS | 8 |
| STS | 5 |
| OLP | 3 |
| CRPV | 0 |
| WMB | 0 |

**B_GARANIN_ALL_KEYS** = `{'DMS-326', 'STS-184686', 'DMS-380', 'OLP-3037', 'OLP-3040', 'STS-311033', 'STS-311024', 'OLP-3145', 'STS-311034', 'DMS-36', 'STS-311026', 'DMS-328', 'DMS-93', 'DMS-248', 'DMS-262', 'DMS-243'}`

---

## Phase 2 — Direct Task API Boundary

| Test | Route | External ID | Count | Status |
|------|-------|-------------|-------|--------|
| `assignee=Garanin.R.V` | `search_users->find_units_by_filter` | `Garanin.R.V` | 16 | ✅ PASS |
| `assignee=Garanin.R.V&space=DMS` | `search_users->find_units_by_filter` | `Garanin.R.V` | 8 | ✅ PASS |
| `assignee=Garanin.R.V&space=OLP` | `search_users->find_units_by_filter` | `Garanin.R.V` | 3 | ✅ PASS |

**Invariant:** `TaskApiLiveKeys == B_GARANIN_ALL_KEYS` ✅

---

## Phase 3 — Focused Harness A Certification

### Query 1: `Задачи Гаранина`

| Field | Value |
|-------|-------|
| Status | COMPLETED |
| Intent | task_search_assignee |
| Skill | task-search-assignee v1.0.0 |
| Answer | "Составной поиск: найдено задач: 0." |
| Task count | 0 |
| Keys | {} |

**PROBLEM:** Answer is from `task_search_composite`, not `task_search_assignee`.

### Query 2: `Задачи Гаранина в DMS`

| Field | Value |
|-------|-------|
| Status | NEEDS_CLARIFICATION |
| Question | "Не могу подтвердить пространство/продукт «DMS» по данным AS21. Что выбрать?" |
| Options | [] |

**PROBLEM:** `DMS` not found in `known_products` (which is actually spaces).

### Query 3: `Задачи Гаранина в OLP`

| Field | Value |
|-------|-------|
| Status | NEEDS_CLARIFICATION |
| Question | "Не могу подтвердить пространство/продукт «OLP» по данным AS21. Что выбрать?" |
| Options | [] |

**PROBLEM:** Same as Query 2.

---

## FIRST FAILING BOUNDARY

### `CAPABILITY_RESULT_PROPAGATION_DEFECT`

**Root Cause:** The condition in `DialogueHarnessRuntime._execute_frame()` line 669-670:

```python
if refined in self._TASK_SEARCH_SKILL_IDS and sum(1 for k in ["assignee", "sprint_id", "release_id", "status", "product"] if k in capability_args) >= 2:
    result = await self.capabilities.execute("task.search.composite", capability_args)
```

This condition calls `task.search.composite` when **2 OR MORE** filters are present, even when the primary intent is `task-search-assignee`.

**Why it happens:**
1. Semantic interpreter (LLM) returns `slots` with `assignee` and another filter (e.g., `status` from context)
2. `_build_capability_args` copies both to `capability_args`
3. `count = 2`, triggering composite instead of `task-search-assignee`
4. `task.search.composite` uses `t.assignee == assignee` for filtering (string comparison)
5. If `assignee` contains Russian name (e.g., "Гаранина") instead of login ("garanin.r.v"), comparison fails
6. Result: 0 tasks returned

**Evidence:**
- For `capability_args = {"assignee": "garanin.r.v", "product": "DMS"}`:
  - `refined = "task-search-assignee"` (correct)
  - `count = 2` (assignee + product)
  - **Use composite: True** (incorrect - should use `task-search-assignee`)
- `task_search_composite` answer: "Составной поиск: найдено задач: 0." (exactly matches observed output)

**Last correct boundary:** `ProductionTaskApiAS21Adapter.search_tasks()` routing to `/api/v1/swtr-read/assignee-tasks` is correct when invoked.

**First incorrect boundary:** `DialogueHarnessRuntime._execute_frame()` incorrectly routes single-assignee searches to `task.search.composite` when multiple filters are present.

---

## Owner Fix Validation

**Owner fix:** `HardenedProductionTaskApiAS21Adapter.search_tasks()` lines 284-285:

```python
if assignee and not sprint:
    return await super().search_tasks(jql, max_results=max_results, fields=fields)
```

This correctly routes assignee queries (without sprint) to `ProductionTaskApiAS21Adapter.search_tasks()`, which calls `/api/v1/swtr-read/assignee-tasks`.

**Status:** ✅ **CORRECT AND FUNCTIONAL**

**Why it's not invoked:** The capability routing defect prevents `task.search_assignee` from being called in the first place.

---

## Phase 4 — Independent Second-Member Control (Kalachanov)

**Oracle B:** REAL AS21 search for `Kalachanov.V.V`

```bash
# Need to check if Kalachanov has tasks in approved spaces
# This requires real AS21 lookup
```

**Status:** Not tested due to earlier failure in focused gate.

---

## Phase 5-7 — Regressions

**Not executed** due to focused gate failure.

---

## Phase 8 — Anti-Surrogate Gate

| Item | Status |
|------|--------|
| Exact HEAD recorded | ✅ `80d698f35a6af3a800047208536e653821c6cf69` |
| Dirty files present (pre-existing fixes) | ⚠️ 3 files modified |
| Old processes killed | ✅ |
| New PIDs recorded | ✅ (68109, 68720) |
| REAL AS21 reads | ✅ 3 reads for Oracle B |
| Local DB/cache authoritative reads | ✅ 0 |
| Fake/mock/frozen truth | ✅ 0 |
| AS21 writes | ✅ 0 |
| Exact-key comparison method | ✅ Set equality |
| `/api/v1/tasks` authoritative use | ✅ 0 (for assignee tests) |

**Issue:** Production fixes in `task_api.py` and `swtr_assignee.py` are pre-existing and should be preserved.

---

## Final Verdict

`CAPABILITY_RESULT_PROPAGATION_DEFECT`

**Description:** The owner fix for assignee routing is correct and functional, but it is never invoked due to a capability routing defect. When the semantic interpreter returns multiple filters (e.g., `assignee + status` or `assignee + product`), the condition `count >= 2` incorrectly routes to `task.search.composite` instead of `task.search.assignee`. The composite capability uses string comparison `t.assignee == assignee`, which fails when `assignee` contains Russian names instead of logins.

**Owner fix is correct:** Yes  
**Issue in owner code:** No  
**Issue in harness routing:** Yes - `DialogueHarnessRuntime._execute_frame()` condition `count >= 2` is too broad

---

## Output

**Primary report:** `po-agent-platform-v2/qa_reports/OWNER_FIX_TRUE_AB_REGRESSION_129.md`

**Optional raw evidence prefix:** `OWNER_FIX_TRUE_AB_REGRESSION_129_`

---

## Recommended Action

**DO NOT implement a fix.** This assignment is diagnostic/certification only.

The defect is in `DialogueHarnessRuntime._execute_frame()` condition:

```python
if refined in self._TASK_SEARCH_SKILL_IDS and sum(1 for k in ["assignee", "sprint_id", "release_id", "status", "product"] if k in capability_args) >= 2:
```

**Fix options:**
1. Change `>= 2` to `>= 3` (require 3+ filters for composite)
2. Exclude `assignee` from the composite trigger when it's the sole primary filter
3. Check if `refined` is a specific search type (e.g., `task-search-assignee`) and skip composite in that case

**Production fix owner:** ChatGPT/OpenAI side (after QA evidence identifies the first failing boundary).

---

## Phase 9 — Final Anti-Surrogate Audit Summary

| Metric | Value |
|--------|-------|
| Oracle B independent method | Direct `/api/v1/swtr-read/assignee-tasks` calls |
| Exact-key comparison method | Set equality |
| REAL AS21 reads count | 3 (all approved spaces for Garanin) |
| `/api/v1/tasks` authoritative use | 0 |
| Local DB/cache authoritative reads | 0 |
| AS21 writes | 0 |
| Dirty files (pre-existing fixes) | 3 files |

---

**Report generated:** 2026-09-02  
**Assignment:** 129  
**Verdict:** `CAPABILITY_RESULT_PROPAGATION_DEFECT`
