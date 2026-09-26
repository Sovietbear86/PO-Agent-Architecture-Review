# A221R3 — Full V4 Canonical-54 A/B/C Certification: Sprint→Attachments Re-gate

**Verdict: `AGENT_CORE_V4_FULL_54_ABC_GREEN_A221R3`**
**Phase 8: 24/24 GREEN** (A221R2 sole RED `sprint_downstream#3` CLOSED)
**Retained A221R2 GREEN:** matrix 54/54, Phase 9 6/6, Browser C 54/54, Phase 11 PASS, Phase 12 p50 10.1s/p95 31.9s/0>60s, Phase 13 13/13

---

## 1. Summary

The owner's sprint-scope fix for the attachment capabilities is **certified end-to-end against live REAL AS21**. The exact A221R2 failing case ("текущий спринт WMB: покажи его задачи с вложениями") went from **0/3 `source_unavailable`** to **5/5 COMPLETED REAL_EMPTY** with the canonical `sprint_id=WMB-SPRNT-2` in the capability args and result data. All P1/P2/P3/P4 gates pass; overall functional certification is **GREEN**.

## 2. P0 — diff/tests

- **START_HEAD:** `3e3e6422189e389654a5e9ca5e0c4fb529fdafaf`.
- Owner fix: `6491f2e` (handler), `eadd41d` (capability specs + skill procedures), `5710bc9` (regression tests).
- **Diff audit (from A221R2 commit `6a811ee`):** production delta limited to `v4_plugins/_task_live_handlers.py` (+sprint_id branch: `get_sprint_tasks(sprint_id, space)` candidate collection, person intersection inside sprint membership, fan-out guard retained) and `v4_plugins/task_catalog.py` (sprint_id added to 4 attachment capability specs; procedures now instruct passing a source-backed sprint_id through without broadening). **No Core/planner/runtime/session-context/adapter/task-api change.**
- Tests: `test_agent_core_v4_attachment_sprint_scope.py` 10/10 (new), full V4 suites **217/217** (incl. planner signature parity). Zero unexplained failures.

## 3. P1 — blocking sprint→attachments composition: GREEN

7 queries (exact A221R2 failed case + 6 natural forms incl. one DMS current-sprint and one explicit sprint-id). Independent Oracle B (fresh, `source_id`-corrected): **WMB-SPRNT-2 = 1 task, 0 files; DMS-SPRNT-3 = 73 tasks, 11 with files** (DMS-335/427/64/425/273/399/412/390/352/401/339).

| Form | Result |
|---|---|
| exact A221R2 case | **5/5 COMPLETED count=0 REAL_EMPTY, sprint_id=WMB-SPRNT-2** (was 0/3 source_unavailable) |
| "вложения в текущем спринте WMB" | COMPLETED 0, WMB-SPRNT-2 |
| "какие задачи текущего спринта WMB имеют вложения" | COMPLETED 0, WMB-SPRNT-2 |
| "покажи вложения по задачам WMB-SPRNT-2" | COMPLETED 0, WMB-SPRNT-2 (5/7; 2 fail-closed LLM plan-validation flakes, F-A221R3-1) |
| "есть ли файлы у задач текущего спринта WMB" | COMPLETED 0, WMB-SPRNT-2 |
| "текущий спринт DMS: покажи вложения по его задачам" | **COMPLETED 11 = Oracle 11** |
| "покажи задачи спринта DMS-SPRNT-3 с вложениями" | **COMPLETED 11, key-set 11/11 EXACT** vs Oracle B |

Requirements verified: source-backed sprint resolution first (sprint.current/sprint.resolve in trajectory); `task.search_attachments`/`task.search_excel` received the canonical sprint_id (+space); candidates came only from sprint membership (audit: **0 WMB space-only task-queries** — the A221R2 broadening is gone); exact parity with independent Oracle B (REAL_EMPTY where source is empty).

## 4. P2 — intersection: GREEN

- **sprint + person + attachments:** "покажи вложения по задачам Семавина в текущем спринте DMS" → COMPLETED count=1, keys=[**DMS-390**], assignee Semavin.M.M, sprint_id=DMS-SPRNT-3 — **exact** vs Oracle (Semavin ∩ DMS-SPRNT-3 ∩ files = {DMS-390}; 325-task all-spaces corpus NOT used).
- **sprint + Excel:** "какие задачи текущего спринта DMS имеют Excel-файлы" → COMPLETED count=1 [DMS-412] within DMS-SPRNT-3. Under the product's own deterministic classifier (`adapters/task_api.py:219`: `.csv`/`.ods`/spreadsheet MIME → EXCEL), DMS-412's `query_log_...csv` is the only spreadsheet-family file in the sprint — intersection exact within sprint membership. The CSV↔"Excel" boundary is a **pre-existing product contract** (not part of this fix) → F-A221R3-2, owner decision.

## 5. P3 — retained canonical attachment smoke (rows 3-6 only): GREEN

- row 3 attachments, row 4 Excel, row 5 PDF: `GREEN_SOURCE_READY` (prior exact behavior); row 6 MSG: `GREEN_SOURCE_CONDITIONAL` retained. No behavior regression from the fix. Rows 1-2 and 7-54 not re-run per spec.

## 6. P4 — audit delta (window 11550→end): PASS

- `local_factual_reads=0`, `local_fallback_reads=0`, `mutations=0`, `truly_unscoped_task_query=0`, **`WMB space-only broadening = 0`**.
- Bounded sprint membership proven: sprint task-collection calls target only WMB-SPRNT-2/DMS-SPRNT-3; file point-reads = sprint membership (73 + 1) + certified person-scoped WMB rows (6, from P3 row 3-4 person reps) + 1 QA-oracle 400 probe. Fan-out guard retained (no >250-candidate fan-out). No `source_unavailable`→REAL_EMPTY conversion (REAL_EMPTY here is source-proven: 0 files at source for WMB-SPRNT-2).

## 7. Findings (non-blocking)

- **F-A221R3-1 (LLM planner reliability, known class):** f3 form flaked 2/7 with `planner failed robust bounded repair: ValidationError` (Qwen3.8 plan-decoding class, A179/A186/A200 lineage). All flakes fail closed (generic-safe error, no fabrication, no source_unavailable, pre-capability); every completed run is source-exact. Not introduced by the fix.
- **F-A221R3-2 (CSV/ODS → EXCEL classifier, pre-existing):** `adapters/task_api.py:219` maps `.csv`/`.ods` to `AttachmentType.EXCEL`. Strictly, a .csv is not an Excel file; the product contract treats the spreadsheet family as one category. Owner decision whether to narrow the EXCEL category to xlsx/xls* only.
- **F-A221R3-3 (QA-oracle gotcha, artifact-only):** the task-api sprint route rows carry the canonical key in `source_id`, not `key` (my first A221R3 oracle used `key`→None→400s and reported false 0-files for DMS). Corrected oracle used `source_id`; raw `/files` payload nests name/type under `filePathParsedDto`/`fileMetadataDto`.

## 8. Retained results (per spec, not re-run)

Matrix 54/54 (A221R2 + rows 3-6 re-confirmed); Phase 9 6/6; Browser C 54/54 (incl. R49=432, R6 source-confirmed); Phase 11 PASS (refined); Phase 12 p50 10.1s/p95 31.9s/0>60s; Phase 13 13/13.

## 9. Artifacts

- `qa_artifacts/a221r3_p1.json`, `a221r3_p2.json`, `a221r3_oracleB.json`, `a221r3_source_audit.json`.
- `qa_artifacts/a221_p8_composition.json` — sprint_downstream#3 flipped to pass with full regate record; P8 24/24.
- `qa_artifacts/a221_matrix_progress.json` — status DONE, verdict `AGENT_CORE_V4_FULL_54_ABC_GREEN_A221R3`, `a221r3` block, phases p8=GREEN.

## 10. Services

agent `8212` (PID 49196 @ `3e3e642`), task-api `8241` (81954, system py3), MCP `3000` (29268), UI `5175` [::1] (47416) — all healthy. No code changed by QA.

## 11. Recommendation

**Freeze immutable full-functional checkpoint** (`checkpoint/v4-full-functional-green-a221r3`). Next owner phase per spec: **UI widget/state/lineage remediation**. Optional owner decisions: F-A221R3-2 (CSV/ODS ↔ EXCEL category boundary), F-A221R3-1 (LLM structured-output hardening, A179 lineage).
