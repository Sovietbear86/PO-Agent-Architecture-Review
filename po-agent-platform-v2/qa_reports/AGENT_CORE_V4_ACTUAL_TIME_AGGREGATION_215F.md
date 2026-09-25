# A215F — Actual Time Aggregation Gate (sprint/team/release time spent + actual utilization + period-normalized capacity)

**Verdict: `ACTUAL_TIME_AGGREGATION_RED_A215F`**
Classification: `RED_COMPLETION_CONTRACT_REAL_EMPTY` — legitimate zero-worklog sprints cannot complete in any of the three worklog-aggregation skills (deterministic FAILED), while every non-empty path is source-exact GREEN.

- **START_HEAD:** `fb2800d9a82730966216fc8f13f3cd371fcd8089`
- **Owner implementation commits:** `9e1782b` (period-normalized capacity helper), `114b6d0` (plugin `builtin.time_accounting.aggregate`), `b133e3c` (aggregation tests), `1337b20` (team.capacity period normalization), `a98b6d2` (capacity regression tests)
- **Base (A215E report):** `2440403`
- **Date:** 2026-09-25
- **Services:** agent 8212 (PID 16314 @ fb2800d), task-api 8241 (PID 81954, A215D — no task-api changes in this diff), MCP-SWTR 3000 (PID 29268), LLM endpoint healthy throughout

---

## First failing boundary (SOLE BLOCKING DEFECT)

**Phase 3, second-sprint case: `sprint.time_spent` on OLP-SPRNT-8 — a legitimate REAL_EMPTY sprint — deterministically FAILED (3/3 runs).**

- OLP-SPRNT-8 is the current OLP sprint (IN_PROGRESS, 2026-09-21 → 2026-10-05, 15 calendar days, 69 tasks).
- Independent oracle (69 bounded per-task worklog reads, complete=true): **lifetime total across all 69 tasks = 0.0h, 0 entries** — a genuine source fact, not an outage.
- The capability itself executed correctly: the planner's READY rationales cite `total_hours=0`, `worklog_count=0` — no fabrication.
- But the `sprint.time_spent` completion contract is `data_keys=("sprint_id", "total_hours", "by_member")` (time_accounting_aggregate.py). With zero in-range entries `by_member=[]`, and `_nonempty([]) == False` in agent_core_v4_completion.py, so the observation never satisfies the contract.
- Result per run: deterministic post-observation completion skipped → planner READY rejected `unsatisfied_completion_contract` (4 consecutive turns) → `V4ContractError: v4 planner step budget exhausted without READY` (8/8 turns) → user sees generic "Agent Core v4 не смог безопасно завершить траекторию."

**Same defect class proven live on the other two worklog-aggregation skills** (same REAL_EMPTY current sprint):

| Skill | Query | Turns | Rejected READYs | Result |
|---|---|---|---|---|
| `sprint.time_spent` | "Сколько времени списано в спринте OLP-SPRNT-8 по OLP" | 8/8 | 4 | FAILED (3/3 runs) |
| `team.time_spent` | "Фактически списанное время команды OLP в текущем спринте" | 8/8 | 5 | FAILED |
| `team.utilization_actual` | "Фактическая утилизация команды OLP" | 8/8 | 5 | FAILED |

Contract shapes: `team.time_spent` requires `by_member` (same empty-list hole); `team.utilization_actual` requires `members` (also `[]` when no worklogs). `release.time_spent` does NOT share the hole (contract keys are scalar `release_id` + `total_hours`, and it fails earlier on empty release membership — see Phase 6).

This contradicts the project's certified principle "zero row is a legitimate source completion" (A188 P5, `test_zero_row_search_is_a_legitimate_source_completion`) and mirrors the A208B defect class (list-valued contract keys made structurally unsatisfiable), which the owner fixed there via `task_keys → task_key_count`.

Safety note: the failure is fail-closed (no wrong data is ever served; the capability's own 0h/0-entry output is correct). It is a functional dead-end for a legitimate source state, not a data-integrity breach.

**Proposed owner fix (not implemented by QA):**
1. Make the three aggregate contracts REAL_EMPTY-tolerant using scalar keys (zero-safe under `_nonempty`):
   - `sprint.time_spent`: `data_keys=("sprint_id", "worklog_count")` (optionally + `task_count`);
   - `team.time_spent`: `data_keys=("space", "sprint_id", "worklog_count")`;
   - `team.utilization_actual`: `data_keys=("space", "sprint_id", "total_actual_hours", "capacity_policy")` (or keep `members` and add a count key).
   Precedent: A208B `task_keys → task_key_count`.
2. Add regression tests mirroring `test_zero_row_search_is_a_legitimate_source_completion`: zero-worklog sprint → deterministic completion (`completion=runtime_contract`, `total_hours=0`, `by_member=[]`) for all three skills.
3. Re-gate: Phase 3 second-sprint (OLP) + OLP variants of Phases 4-5 + Browser C, per the normal A215F gate.

---

## Phase 0 — architecture invariant: PASS

- `git diff --stat 2440403..a98b6d2` = 5 files: `capacity_policy.py` (+24), `v4_plugins/time_accounting_aggregate.py` (new, +367), `v4_plugins/wave_batch2.py` (+29/−7), 2 test files. **0 lines** in `agent_core_v4*.py` (core/planner/runtime) and `task-api/`.
- New skills are plugin-registry discovered: `discover_v4_plugins()` → 8 plugins, 53 skills, all 4 new skills present, 0 duplicate capability ids, CompletionContract + UIContract on every new skill.
- No person/space/sprint hardcoding in the new plugin (generic handlers only).
- `capacity_policy.py` remains a standalone module outside Agent Core (A215E pattern).
- dummy-55 / registry extensibility tests green (within Phase 1 suite).

## Phase 1 — focused tests: PASS

- `test_agent_core_v4_time_accounting_aggregate.py` + `test_agent_core_v4_time_accounting.py` + `test_agent_core_v4_batch2.py`: **17/17 passed** (includes owner's new tests: period filter to sprint, authoritative current sprint, owner-policy scaling to sprint period, release fail-closed, capacity 65.94 fixture, explicit 40h override, estimate guard ordering).
- `tests/test_agent_core_v4*.py tests/test_v4*.py`: **177/177 passed** (was 172 at A215E; +5 new aggregate tests).

## Phase 2 — capacity period normalization: PASS

**Independent math (not reusing module constants):**
- annual = 247 × 8 × 0.87 = 1719.12h; per calendar day = 1719.12/365 = 4.709918h
- 14d = **65.94** ✓ (spec example), 7d = 32.97 ✓, 30d = 141.30 ✓, 0d = 0.0
- metadata carries: `source=OWNER_POLICY`, `working_days_2026=247`, `availability_factor=0.87`, `weekly_hours=40.0`, `daily_hours=8.0`, `calendar_days`, `available_capacity_hours_for_period`, `normalization=2026_annual_average_workday_density`, `policy_id=RU_2026_AVG_WORKDAYS_X_0_87_40H_WEEK`

**Fixture probes (independent, in-process, 14-day sprint):**
- A) complete estimates, no explicit baseline → `capacity_hours_per_member=65.94` (NOT 143.26), `calendar_days=14`, `list_sprints` consulted ✓
- B) explicit `capacity_hours=40` → `40.0` exact override, `capacity_source=explicit_user_baseline`, `capacity_policy=None`, **no `list_sprints` call** (denominator not needed) ✓
- C) missing estimate → `V4CapabilityUnavailable` ("do not expose source-backed estimates") with calls exactly `[current, sprint]` — **before any denominator use** ✓
- D) missing estimate + explicit baseline → same fail-closed (estimates mandatory) ✓

**Live (REAL DMS, current sprint DMS-SPRNT-3):**
- "Плановая утилизация команды DMS" → FAILED, typed error `team.capacity cannot be calculated from REAL AS21 because active assigned tasks do not expose source-backed estimates; an explicit capacity baseline alone is insufficient` (A215E guard retained) ✓
- "Плановая утилизация команды DMS с capacity 40 часов" → `capacity_hours="40"` preserved in executed args, same fail-closed ✓
- Non-blocking F1: plain "Утилизация команды DMS" now routes to the NEW `team.utilization_actual` (actual worklog utilization, COMPLETED with real data) instead of `team.capacity` — a semantic routing shift caused by the new skill, not a defect; "Плановая …" deterministically reaches `team.capacity`. "…с capacity 40 часов" non-deterministically reached `team.utilization_actual` once (explicit baseline dropped by routing, not by the capability). Planner-routing class, pre-existing (A215/A207 F2/F3 lineage).

## Phase 3 — sprint.time_spent REAL AS21

Independent oracle: complete sprint membership (`complete_tasks`, complete=true) + authoritative period from `spaces/{space}/sprints` + bounded per-task worklogs (concurrency 8) + inclusive date filter.

**DMS-SPRNT-3 (15 calendar days, 72 tasks): EXACT parity 3/3 (+ initial probe) — GREEN**

| Field | Oracle | Agent |
|---|---|---|
| period | 2026-09-13 → 2026-09-27 | identical |
| task_count | 72 | 72 |
| total_hours | 428.5 | 428.5 |
| worklog_count | 65 | 65 |
| by_member | Garanin 72.0, Semavin 64.0, Zhdanov 64.0, Kondratchikova 52.5, Alekseev 48.0, Moiseev 48.0, Agataeva 40.0, Galtsov 40.0 | identical |
| by_task | DMS-405 72, DMS-412 64, DMS-253 40, DMS-389 40, DMS-164 38, DMS-421 32, … | identical |
| by_type | 2Р_Кодирование 224, 4Р_Тестирование 64, 5Р_Документация 52.5, 4П_Поддержка 50, 10П_Развитие 38 | identical |
| by_date | 12 dates within period (09-14…09-25), 0 outside | identical, 0 out-of-range |

All runs: `completion=runtime_contract` (deterministic), `semantic_prepass_used=false`, trajectory `space.resolve → sprint.resolve → sprint.time_spent`. 355 lifetime out-of-range entries correctly excluded (lifetime total 2720h vs 428.5h in-range). Period form "в сентябрьском спринте по DMS" also resolves to DMS-SPRNT-3 and is EXACT.

**Second sprint OLP-SPRNT-8: RED** — see "First failing boundary" above.

## Phase 4 — team.time_spent (current DMS sprint): PASS (DMS) / RED class (OLP)

- 2/2 runs EXACT vs the same DMS-SPRNT-3 oracle: `sprint_id=DMS-SPRNT-3` (authoritative current sprint via `get_current_sprint_id`), total 428.5h / 65 entries, by_member identical.
- **Attribution proven by worklog author, not current assignee:** worklog author **Galtsov.A.A carries 40.0h but is the current assignee of 0 of the 72 sprint tasks**; conversely 5 current assignees (Dolgovskoy.E.N 11, Kuznetsov.M.Se 4, Shaldunov.A.V 1, Makoshina.V.V 1, Bezrukov.P.S 1) have zero worklog hours and are absent from by_member; 5 unassigned tasks contribute nothing.
- unknown-user bucket present in code (`unknown_user_hours`); no anonymous entries in the live source.
- OLP (REAL_EMPTY current sprint) → same defect class, FAILED (see above).

## Phase 5 — team.utilization_actual (current DMS sprint): PASS (DMS) / RED class (OLP)

- 2/2 runs COMPLETED, `runtime_contract`, formula and provenance EXACT:
  - denominator: `calendar_days=15` → `capacity_hours_per_member=70.65` (= 15 × 1719.12/365, independently verified) ✓
  - `numerator_source=REAL_AS21_WORKLOGS`, `denominator_source=OWNER_POLICY`, `capacity_policy` full metadata, warning `capacity_denominator_owner_policy_average_2026` ✓
  - per-member exact (8/8): Garanin 72.0 → **101.9% (over 100, NOT clipped, `over_capacity=true`)**, Semavin 64.0 → 90.6, Zhdanov 64.0 → 90.6, Kondratchikova 52.5 → 74.3, Alekseev 48.0 → 67.9, Moiseev 48.0 → 67.9, Agataeva 40.0 → 56.6, Galtsov 40.0 → 56.6 ✓
  - worklog author = member identity (Galtsov case, Phase 4); no estimate/task-count substitution in the formula ✓
- Distinctness from `team.capacity` (planned): provenance labels and inputs are disjoint (actual worklogs vs source estimates + same policy family); live DMS planned path still fails closed on estimates while actual path completes from worklogs.
- OLP (REAL_EMPTY) → same defect class, FAILED (see above).

## Phase 6 — release.time_spent: expected SOURCE_CONDITIONAL behavior confirmed

- Live "Сколько времени списано по релизу 24Q1 в WMB": trajectory `space.resolve → release.search(require_single) → release.time_spent(release_id=7a84006f-7823-4052-ae46-b94f5165518e)` → typed `V4CapabilityUnavailable: release.time_spent requires authoritative release-to-task membership; the current REAL AS21 source does not expose populated release linkage` (A212 source state unchanged). No 0h fabrication, no tenant scan, bounded trajectory. ✓
- In-process probe: empty release membership → `V4CapabilityUnavailable` (no 0h). Malformed/incomplete worklog pages and entries without normalized duration → fail closed (probes A/B/C/E below).

## Phase 7 — Browser C: SKIPPED

Stopped per the assignment's first-new-defect STOP rule after the Phase 3 second-sprint RED. (No UI changes in this diff; presentation contracts `time_spent_breakdown` / `team_utilization` verified at registry level.)

## Phase 8 — retained regression: partial (pre-STOP sanity)

- DMS-380 `task.time_spent`: COMPLETED, "48 часов (6 записей в worklog)" — A215D truth retained ✓
- team.capacity estimate guard: retained (Phase 2 live) ✓
- release.search/release linkage: retained (Phase 6) ✓
- Remaining Phase 8 items (team.workload, release.health, dummy-55 live, Browser C) not run per STOP rule; dummy-55/registry green in Phase 1 suites.

## Phase 9 — source/performance audit: PASS

Agent log over the whole QA session (1624 HTTP lines):
- local factual `GET /api/v1/tasks` reads: **0**
- mutations (POST to swtr-read): **0**
- unscoped tenant-wide `task-query` calls: **0** (0 task-query calls at all)
- worklog route calls: **1422**, all HTTP 200; bounded per-task fan-out; code enforces `asyncio.Semaphore(8)` (`_MAX_WORKLOG_CONCURRENCY = 8`); max 9 completions in any 500 ms window (completion-timestamp clustering artifact, not in-flight count)
- route census (non-worklog): sprint membership `sprints/{id}/tasks?complete=true` ×32 (DMS 22 + OLP 10), `spaces/{sp}/sprints` ×22, `spaces/{sp}/current-sprint` ×12, `tasks/{key}/files` ×3, `tasks/DMS-380` ×1, LLM POSTs ×132
- source outage/incomplete page → fail closed, no partial aggregate: proven in-process for all three aggregate skills (incomplete `complete=false` page on any task raises `V4CapabilityUnavailable` before aggregation)

## Non-blocking findings

- **F1 (routing shift):** plain "Утилизация команды X" now reaches `team.utilization_actual` (actual) rather than `team.capacity` (planned); explicit "capacity N часов" reached `team.utilization_actual` once (baseline dropped by routing). Planner-routing class, pre-existing lineage; no data integrity impact.
- **F2 (presentation):** LLM answer text sometimes renders work-type names shortened ("Кодирование" vs "2Р_Кодирование"); data payload is exact. Cosmetic.
- **F3:** completion-timestamp clustering (9/500 ms) vs semaphore 8 — in-flight bound is code-enforced; no action needed.
- **F4:** live source drift during session: DMS-SPRNT-3 membership 68→72 tasks (A210→now); all comparisons used a freshly run oracle per case, so drift is reconciled.

## Services left running

UI: not started (Phase 7 skipped). agent 8212 (PID 16314 @ fb2800d), task-api 8241 (PID 81954), MCP-SWTR 3000 (PID 29268).

## Recommendation

STOP. Do not start A216 / Batch 3. Owner to fix the REAL_EMPTY completion-contract hole (scalar contract keys + zero-worklog regression tests, per the proposal above), then full A215F re-gate (Phase 3 both sprints, Phases 4-5 both spaces, Phase 6, Phase 7 Browser C, Phases 8-9).
