# A221 — Full V4 Canonical-54 A/B/C Certification Matrix

**Verdict: `AGENT_CORE_V4_FULL_54_ABC_RED_A221`**
**First failing canonical row: 10 (`task.search_release`)**
**First failing boundary: A (Agent) — skill resolution path / release-validation contract routing**

---

## 1. Summary

Stopped at the first confirmed RED (row 10) per the assignment STOP rule ("If a blocking RED is proven, stop at that first failing boundary and preserve all completed matrix rows so the next re-gate resumes rather than restarts").

- **9/54** canonical rows certified GREEN (8 `GREEN_SOURCE_READY` + 1 `GREEN_SOURCE_CONDITIONAL`).
- **1 RED** (row 10).
- **44 NOT_RUN** (rows 11-54 + Phases 8-13).
- **0 production code changes.** All resumable artifacts preserved.

---

## 2. Baseline integrity (Phase 0) — GREEN

- Branch `feat/core8-real-query-hardening-v2`, HEAD `62ea3ac` (docs-only drift from A220 `5c23ac5`: `GIGACODE_NEXT_ACTION.md` + `V4_DOD_LOCK.md`).
- 29 core adapter + planner baseline file hashes recorded in the progress artifact and stable vs A220.
- Live registry: **68 skills / 13 plugins / 0 duplicates**; canonical **54/54 covered**; missing list = `[]`; no dummy plugin in production discovery.
- Base/robust planner signature parity: **1 passed**.
- `dummy-55` extensibility: **13/13** (test-only context).
- Services healthy: agent `8212`, task-api `8241` (system py3), MCP `3000`, UI `5175` — all HTTP 200.
- **Finding F2:** checkpoint **branch** `checkpoint/v4-canonical54-green-a220` is absent from local and remote **branch/ref** lookups (confirmed via ref lookup, not tag list). Effective baseline = `5c23ac5` (A220 GREEN).

---

## 3. Canonical manifest (Phase 1) — GREEN

`a221_canonical54_manifest.json`:
- exactly **54 rows**;
- **0 duplicate** canonical requirement;
- every row mapped to **exactly one** primary live V4 skill;
- legacy/alias names merged to current dot-style V4 skill;
- **6 post-48 additions** present exactly once;
- **14 legitimate extra skills excluded** from the canonical denominator (tested separately as retained regression).

Denominator = 54, all rows mapped → traffic allowed.

---

## 4. Matrix — Group 1: task discovery/search (Phase 2)

| Row | Requirement | Live skill | Source class | Result | Oracle B parity |
|-----|-------------|------------|--------------|--------|-----------------|
| 1 | exact task lookup | `task.lookup` | SOURCE_READY | GREEN_SOURCE_READY | DMS-380 point-read exact (Закрыт, Semavin.M.M) |
| 2 | phrase search | `task.search_text` | SOURCE_READY | GREEN_SOURCE_READY | 2/2 [DMS-267, DMS-380] |
| 3 | attachments | `task.search_attachments` | SOURCE_READY | GREEN_SOURCE_READY | 3 tasks / 16 files (WMB-30000×5, WMB-29890×1, WMB-29995×10) |
| 4 | Excel attachments | `task.search_excel` | SOURCE_READY | GREEN_SOURCE_READY | WMB-30000×5 + WMB-29995×6 (11 .xlsx exact) |
| 5 | PDF attachments | `task.search_pdf` | SOURCE_READY | GREEN_SOURCE_READY | WMB-29890×1 + WMB-29995×2 (3 .pdf exact) |
| 6 | MSG attachments | `task.search_msg` | SOURCE_CONDITIONAL | GREEN_SOURCE_CONDITIONAL | REAL_EMPTY: 0 .msg across 16 files |
| 7 | assignee filter | `task.search_assignee` | SOURCE_READY | GREEN_SOURCE_READY | Zhdanov.A.Ni DMS 7/7 exact |
| 8 | status filter | `task.search_status` | SOURCE_READY | GREEN_SOURCE_READY | DMS terminal 146/146 exact |
| 9 | sprint filter | `task.search_sprint` | SOURCE_READY | GREEN_SOURCE_READY | DMS-SPRNT-3 73/73 exact |
| 10 | release filter | `task.search_release` | SOURCE_CONDITIONAL | **RED** | see §5 |

Checkpoints persisted after row 9 and after row 10.

---

## 5. Row 10 RED — `task.search_release`

- **Query:** "задачи в релизе 24Q1 в WMB"
- **Agent A result:** `NEEDS_CLARIFICATION`, traj=`[release.resolve]`, warning=`v4_capability_clarification`, **options=[] (zero-option)**, `answer=""`.
- **Oracle B:** independently proves release **24Q1 / WMB** (UUID `7a84006f-7823-4052-ae46-b94f5165518e`) has **0 task membership rows** — fix_version linkage uniformly unpopulated (A211/A212/A220). The source fact (membership unpopulated) is proven; the row simply cannot be certified GREEN.
- **Spec-required terminal:** a release-derived row with unpopulated linkage must be **typed `SOURCE_CONDITIONAL`** (`v4_capability_unavailable`), **not** a zero-option clarification.

### Determinism (4/4)
| # | Query | traj | terminal |
|---|-------|------|----------|
| 1 | "задачи в релизе 24Q1 в WMB" | `release.resolve` | NEEDS_CLARIFICATION, options=[], "Не удалось подтвердить релиз «24Q1» по данным REAL AS21." |
| 2 | "покажи задачи в релизе 1.6.0 в OLP" | `release.resolve` | NEEDS_CLARIFICATION, options=[], "…релиз «1.6.0»…" |
| 3 | "какие задачи входят в релиз 24Q1 WMB" | `space.resolve → release.search → release.scope` | **FAILED `v4_capability_unavailable`** (the correct typed SC) |
| 4 | original sweep run | `release.resolve` | same zero-option dead-end |

### Root cause
- The `task.search_release` procedure (`task_catalog.py:116`) **explicitly instructs**: "Resolve/validate the release with `release.resolve`" before calling `task.search_release`.
- `release.resolve` (`core.py:84`) is **task-based**: "Validate a release/version id against REAL AS21 tasks" (a fix_version linkage check).
- Under unpopulated fix_version linkage, task-based validation can **never** confirm a directory-verified release → the `release_id` literal guard rejects it → zero-option clarification (no continuation, not typed SC).
- Probe #3 proves the correct typed `v4_capability_unavailable` is reachable via `release.search → release.scope` — so the defect is specifically the `task.search_release` **resolution path**, not a source or terminal-reachability problem.

### Safety
Fail-closed, **0 fabrication**, **0 tenant scan**. But the terminal is a zero-option clarification with misattributed phrasing (blames the release, not the missing task linkage), which is not the spec-required typed `SOURCE_CONDITIONAL` and offers no continuation.

---

## 6. Findings (all non-blocking)

- **F1 (source limitation):** bare surname "Каликанов" → source `/assignees/resolve?reference=Каликанов` → 409 `matches=[]`. Agent correctly fails closed (typed clarification, no fabrication). Rows 3-6 reps therefore use the canonical login `Kalachanov.V.V`. Not a skill defect.
- **F2 (checkpoint ref):** branch `checkpoint/v4-canonical54-green-a220` absent (local + remote branch/ref); effective baseline `5c23ac5`.
- **F3 (routing, correct):** row 8 initial rep ("открытые задачи в спринте DMS-SPRNT-3") routes via `task.search` (task.search_sprint procedure) with exact data; the pure status-filter rep ("завершённые задачи в DMS") routes to `task.search_status` directly. Both correct; routing is intent-dependent, not a defect.
- **F4 (scoping-efficiency):** 1 person-scoped, unscoped-by-space task-query (`assignee=Kalachanov.V.V`, `limit=100`/`max_pages=100`) from the attachment handler (rows 4/5, task-api log line 10384, preceded by `WMB-30000/files`) — fetches the person's tasks across **all** spaces while ignoring the `space=WMB` constraint. Person-scoped (bounded), **NOT tenant-wide**. Spec's "tenant-wide = 0" requirement is MET; this is a scoping-efficiency finding only.

---

## 7. Phase 11 source/write audit (partial window, task-api log lines 10193-10449)

| Check | Result |
|-------|--------|
| local DB/API factual reads (`GET /api/v1/tasks`) | **0** ✓ |
| local DB/cache factual fallback | **0** ✓ |
| unbounded / tenant-wide task scans | **0** ✓ (spec requirement MET) |
| unscoped release membership queries | 0 ✓ |
| unscoped sprint collections | 0 ✓ |
| unscoped versions | 0 ✓ |
| mutations (POST/PUT/PATCH/DELETE) | **0** ✓ |
| source-unavailable → REAL_EMPTY conversions | 0 ✓ |
| person-scoped unscoped-by-space | 1 (F4, non-blocking) |
| total swtr-read | 124 |

---

## 8. Phase 12 latency (PARTIAL — P12 not reached due to RED stop)

Group 1 only (rows 1-9 + the row-10 attempt):
- **all_rows:** n=10, p50=11.6s, p95=37.4s, max=37.5s
- **simple_point_lookup** (row 1): p50/p95=6.4s
- **task_collection** (rows 2-9): n=9, p50=12.5s, p95=37.4s (attachment rows 3-6 slowest at ~29-38s due to per-task file lookups)
- **pathological >60s ordinary cases:** 0
- Categories beyond Group 1 are null (not run until re-gate).

---

## 9. Phases NOT run (STOP rule)

Phases 3-13 were **not executed** because the assignment stops at the first confirmed RED:
- Phase 3 (Group 2, rows 11-20), Phase 4 (Group 3, 21-32), Phase 5 (Group 4, 33-40), Phase 6 (Group 5, 41-48), Phase 7 (Group 6, 49-54)
- Phase 8 (cross-skill composition), Phase 9 (clarification/session), Phase 10 (Browser C full-surface), Phase 11 (full-window audit), Phase 12 (full latency), Phase 13 (retained extras).

P8/P9/P13 runners are prepared but not run (concurrency rule: no parallel agent calls during the matrix).

---

## 10. Owner fix (row 10)

The `task.search_release` release-validation step must not rely on task-based `release.resolve` alone. Recommended (generic, plugin-only):
1. Change the `task.search_release` procedure to validate the release via **`release.search`** (directory-based, works) and call `task.search_release` with the canonical UUID; when membership is empty, emit **typed** `v4_capability_unavailable` (SOURCE_CONDITIONAL), not a zero-option clarification.
2. **OR** make `release.resolve` fall through to directory confirmation (`release.search`) / typed SC when task-based validation finds no linkage, instead of a zero-option clarification.
3. Add a non-mocked regression: under unpopulated fix_version, "задачи в релизе 24Q1 в WMB" must reach typed `v4_capability_unavailable` (not zero-option clarification); the `release.resolve` dead-end must be impossible.
4. (F4, optional) Apply the planner's space constraint to the attachment handler's person task-fetch so the person's tasks are fetched within the stated space.

---

## 11. Artifacts (resumable)

- `po-agent-platform-v2/qa_artifacts/a221_canonical54_manifest.json` (54 rows)
- `po-agent-platform-v2/qa_artifacts/a221_matrix_progress.json` (`RED_STOPPED`, `red_row=10`, 9 GREEN, 29 baseline hashes, resumable)
- `po-agent-platform-v2/qa_artifacts/a221_source_audit.json` (`PASS_WITH_FINDING`)
- `po-agent-platform-v2/qa_artifacts/a221_latency.json` (`PARTIAL`)
- Runners: `qa_221_matrix_runner.py`, `qa_221_matrix_lib.py`, `qa_221_matrix_b1.py`, `qa_221_matrix_b2.py`, `qa_221_p11_audit.py`, `qa_221_p12_latency.py`, `qa_221_p8_runner.py`, `qa_221_p9_runner.py`, `qa_221_p13_runner.py`, `qa_221_p1_manifest.py`
- Browser C spec: `po-agent-platform-v2/frontend/e2e/qa221-browser-c.spec.ts` (54 rows, resumable)
- Log: `/private/tmp/qa221_matrix.log`
- **Next re-gate:** resume from row 10 (re-run after owner fix), continue 11-54, then Phases 8-13. Do not re-run already-certified rows 1-9 unless the owner fix affects them.

---

## 12. Services

agent `8212`, task-api `8241` (system py3), MCP `3000`, UI `5175` — all healthy (HTTP 200) at P0; left running.

**STOP.** Awaiting owner fix for row 10 (`release.resolve` → `release.search` fallthrough / typed SC). No code changed.
