# A221R2 — Full V4 Canonical-54 A/B/C Certification: Row-49 Re-gate + Matrix Completion + Phases

**Verdict: `AGENT_CORE_V4_FULL_54_ABC_RED_A221R2`**
**54/54 canonical matrix: GREEN** (40 `GREEN_SOURCE_READY` + 14 `GREEN_SOURCE_CONDITIONAL`, 0 RED)
**First failing boundary: Phase 8 (mandatory composition gate) — `sprint_downstream#3` (current sprint → attachments)**

---

## 1. Summary

- **Row 49 re-gate GREEN** (owner space-only fix certified; 432/432 exact; F-A221R-6 silent-sprint-narrowing also closed).
- **Rows 50-54 GREEN** → **54/54 canonical matrix fully certified GREEN** (rows 1-48 not re-run per instruction; the additive guard change leaves assignee/sprint/space+unassigned consumers unaffected).
- **Phase 8 (mandatory cross-skill composition gate): 23/24 pass, 1 confirmed RED** — `sprint_downstream#3` ("текущий спринт WMB: покажи его задачи с вложениями") deterministically (3/3) fails closed for a **bounded, source-answerable** intent, because `task.search_attachments` has **no `sprint_id` arg** and degrades to an unbounded space-only scan that trips the A196 D2 guard.
- Stopped at the Phase 8 RED per the first-confirmed-RED rule. **Phases 9-13 NOT_RUN** (resumable).
- **0 production code changes by QA.**

Because a **mandatory gate** (Phase 8) has a confirmed defect, the full A/B/C certification is RED even though all 54 canonical rows are GREEN.

---

## 2. Baseline / owner fix verification

- **START_HEAD:** `31362308498f399593e65a8ba7fde4f28a1d63d6`.
- Owner fix: `fd922f4` (prod +4/-2 in `agent_core_v4.py`), `81e209b` (new tests), `975bf51` (aligned the A221R-F1 stale release-catalog test).
- Fix content: guard `if not any((assignee, sprint_id, space))` — now accepts **space-only**, which falls through to the existing bounded `project = "<space>"` branch (`max_results=10000` + space re-filter). Purely additive: assignee/sprint/space+unassigned paths unchanged.
- Unit level: **216 passed, 0 failed** (stale test now aligned; 2 new tests green: space-only bounded+source-backed count=3 exact; empty-args still fails closed).
- Agent restarted on START_HEAD (PID 28438).

### Row 49 re-gate — GREEN (fix certified)
- 4 live probes, all **COMPLETED 432/432** (source total 432, all keys in corpus, `tasks.search` loaded → `task.search(space=DMS)`):
  - "найди все задачи по продукту DMS", "все задачи в DMS", "покажи задачи по продукту DMS", "список всех задач в DMS".
- **F-A221R-6 closed:** the soft phrasing "покажи задачи по продукту DMS" now returns **432** (product-wide), no longer the current-sprint 73-task silent narrowing.
- Formal runner: `row 49: GREEN_SOURCE_READY`.

### Rows 50-54 — GREEN
| Row | Skill | Result |
|-----|-------|--------|
| 50 | release.forecast | GREEN_SOURCE_CONDITIONAL (typed SC, membership=0, no fabricated date) |
| 51 | po.daily_brief | GREEN_SOURCE_READY (cross-product 148/127/21/8/8 exact — see oracle fix) |
| 52 | po.status_report | GREEN_SOURCE_READY |
| 53 | po.reminder_draft | GREEN_SOURCE_READY (draft_created=true, write_performed=false, requires_approval=true) |
| 54 | po.local_task_draft | GREEN_SOURCE_READY (dc=true, wp=false, REAL_AS21, no task.lookup) |

**Matrix total: 54/54 GREEN (40 READY + 14 SC), 0 RED.**

---

## 3. Phase 8 — cross-skill composition (mandatory gate) — RED

24 compositions (8 patterns × 3 fresh forms), sequential. **23 pass, 1 confirmed RED.**

### CONFIRMED RED — `sprint_downstream#3`: "текущий спринт WMB: покажи его задачи с вложениями"
- **Behavior (deterministic 3/3):** `sprint.current` (WMB-SPRNT-2, resolved OK) → `task.search_attachments` → **`source_unavailable`** (48.3s / 38.5s / 34.1s), answer "Источник AS21 временно недоступен. Данные не интерпретируются как пустой результат."
- **Root cause (pinned in code, `_task_live_handlers.py` `build_task_search_attachments`):** the capability's args are `{task_key, space, assignee, reference}` — **no `sprint_id`**. With no task and no person, `_source_assignee_from_args` returns no assignee, so `candidates = _live_rows(space=WMB)` = **all ~2374 WMB tasks** → the A196 D2 guard `if len(candidates) > 250 and not task_key: raise AS21SourceUnavailable` fires.
- **Why it is a RED (not an accepted source limitation):** the source **has** the data for the actual bounded intent — WMB-SPRNT-2 = **1 task** (WMB-108), `WMB-108/files` = **0 files in 0.1s** (direct probe). The query is bounded and answerable ("your current WMB sprint's tasks with attachments"), yet it fails closed because the **sprint constraint cannot be expressed** to the attachment capability. It degrades from a 1-task bounded lookup to a 2374-task space-only scan.
- Safety intact (fail-closed, no fabrication, no empty interpretation) — but a legitimate bounded intent is unfulfilled for a non-source reason.

### Other non-COMPLETED Phase 8 cases (all verified legitimate, not defects)
- `person_sprint_status#2` + `sprint_member_time#3` (Каликанов in OLP-SPRNT-8): **legitimate person-reference typed clarification** ("Не удалось однозначно определить пользователя «Каликанов»"), fail-closed, no fabrication — the A195D identity-resolution boundary, not a composition defect.
- `po_brief_drill#2` (DMS PO status + blocked-task drill): non-deterministic on the first pass (NEEDS_CLARIFICATION after `sprint.resolve`), but **re-probe COMPLETED correctly** (sprint.health, 73 tasks, 18 done, 2 blocked, blocked-task details).
- `release_analytic#1/2/3`: **correct typed `v4_capability_unavailable`** (release membership unpopulated) — expected SC for this pattern.

---

## 4. QA-oracle fixes (this re-gate, boundary B artifacts — not product defects)

- **b49 (row 49):** `tasks.search` is a composition skill whose procedure **delegates to** `task.search`; the oracle's `ok` tested `"tasks.search" in traj` only. Fixed to accept the skill in `traj` OR `loaded_skills` OR the delegated `task.search` call (consistent with `classify()`). Data was already 432/432 exact.
- **b51 (row 51):** `po.daily_brief` is **cross-product** by design (`scope="approved_product_spaces_current_sprints"`, no space arg; iterates all `APPROVED_PRODUCT_SPACES` current sprints — certified cross-product in A219). The oracle wrongly used DMS-only (73). Fixed to mirror `_current_sprint_portfolio`. Verified agent == source exactly: **total 148 / active 127 / completed 21 / blocked 8 / unassigned 8** (DMS-SPRNT-3 73 + OLP-SPRNT-8 74 + WMB-SPRNT-2 1; CRPV/STS NO_CURRENT_SPRINT).

Both fixes are to QA artifacts only; no production change.

---

## 5. Findings (non-blocking)

- **F-A221R2-1 (owner, resolved in-fix):** the A221R-F1 stale test (`test_agent_core_v4_task_catalog.py` asserting the pre-fix `[release.resolve, task.search_release]` tuple) is now aligned to `[space.resolve, release.search, task.search_release]` in `975bf51`. V4 suites 216/216.
- **F-A221R2-2 (Phase 8 RED, blocking):** see §3. Owner fix below.
- **F-A221R2-3 (person-identity boundary, non-blocking):** the user's own surname "Каликанов" (genitive, no first name) returns a typed "couldn't uniquely determine user" clarification rather than resolving to Kalachanov.V.V. Fail-closed, no fabrication — the A195D/A213 identity-morphology boundary, surfaced here by two Phase 8 forms.
- **F-A221R2-4 (LLM non-determinism, non-blocking):** `po_brief_drill#2` first pass clarified but re-probe completed; Qwen3.8 planner variance on multi-intent drills. Safe (fail-closed), not a defect.
- **F-A221R2-5 (matrix note):** the additive row-49 guard change does not alter assignee/sprint/space+unassigned behavior, so rows 7/8/9 required no re-run (per instruction not to re-run 1-48).

---

## 6. Owner fix (Phase 8 RED, proposed — not implemented)

Make sprint-scoped attachment search expressible and bounded:
1. Add **`sprint_id`** to `task.search_attachments` (and its CapabilitySpec) in `_task_live_handlers.py`: when a sprint is given (and no task), scope candidates via the sprint's tasks (`get_sprint_tasks(sprint_id, space)`), which is small, then apply the existing bounded file fan-out (semaphore 12, `max_fanout` guard still applies as a safety net).
2. Update the `tasks.search`/attachment skill procedure so a "current/period sprint → attachments" composition threads the resolved sprint id into the attachment call.
+ non-mocked regression: "текущий спринт WMB задачи с вложениями" (WMB-SPRNT-2 = 1 task) must **COMPLETED** with the sprint's tasks (REAL_EMPTY if 0 attachments) — not `source_unavailable`; and a genuinely broad space-only (no sprint, no person, no task) scan must still fail closed.

After the fix: re-run Phase 8 `sprint_downstream#3` (3×) + Phases 9-13, then final GREEN/RED per spec. Do not re-run certified rows 1-54 unless the fix touches them.

---

## 7. Phases NOT run (first-confirmed-RED stop)

Phases 9 (clarification/session), 10 (Browser C full-surface), 11 (full-window audit), 12 (full latency), 13 (retained extras). Runners prepared (`qa_221_p9/p13_runner.py`, `qa221-browser-c.spec.ts`). Resume after the Phase 8 owner fix.

## 8. Artifacts (resumable)

- `qa_artifacts/a221_matrix_progress.json` — RED_STOPPED, 54/54 GREEN rows + row-49 re-gate + a221r2 metadata + `phases` block (p8 RED, p9-p13 NOT_RUN).
- `qa_artifacts/a221_p8_composition.json` — 24 rows, sprint_downstream#3 marked RED with full root_cause.
- `qa_artifacts/a221_canonical54_manifest.json` — 54 rows (rep notes from A221R retained).
- Runners: `qa_221r2_start_agent.sh`, `qa_221_p8/p9/p13_runner.py`, `qa221-browser-c.spec.ts`.

## 9. Services

agent `8212` (PID 28438 @ `3136230`), task-api `8241` (81954, system py3), MCP `3000` (29268), UI `5175` [::1] (47416) — all healthy.

**STOP.** Awaiting owner fix for the Phase 8 `sprint→attachments` composition (add `sprint_id` to the attachment capability). No code changed by QA.
