# GigaCode — CURRENT NEXT ACTION

## A230R2.1-QA — Independent regression of week period changes

**STRICTLY TEST ONLY.** Do not edit production code, tests, config, runtime, API, frontend, frozen Agent Core V4, or the implementation spec. Do not auto-fix, reformat or refactor. No cherry-pick, merges or publishing. If RED, report the first failing boundary and STOP. Only permitted write is a QA report in `po-agent-platform-v2/qa_reports/` with commit+push on the existing working branch.

### Scope
Owner commits under test: `8090bb6` (week parser), `34ef574` (period-intent guard), `d9dd200` (regression tests).
Read `docs/assignments/A230R2_OWNER_FIX_SPEC.md` and the independent RED report `po-agent-platform-v2/qa_reports/AGENT_CORE_V4_A230R1_UI_REAL_QUERY_FAILURES.md`.
First record exact TESTED_HEAD and tracked worktree state. Verify six frozen Core files byte-identical to checkpoint `6fb335d`. All goal feature flags must remain OFF.

### Tests
1. Run `tests/test_a230r2_week_periods.py` and existing period, task-live-handler, API V4 coverage/clarification/continuation tests, with actual counts, all failures and traceback.
2. Check deterministic rolling window: `за последнюю неделю` must mean seven calendar dates (today and six preceding dates) under Europe/Moscow; contrast `за прошлую неделю` (previous Monday–Sunday); test month/year boundaries, a fixed clock, malformed expressions and explicit `с 30.09.2026` inclusivity. Detect accidental regex false positives and flag unsupported forms rather than inventing semantics.
3. Verify `_TASK_PERIOD_INTENT_RE` recognizes the week wording and does not invent the date field. **Important:** parsing a phrase as `created_period` does not by itself fix the unresolved question of whether user meant created/updated/activity. Report that independently; never mark end-to-end C1/C2 GREEN without resolution.
4. Local REAL AS21 A/B source oracle (no fake/mock for live claim) for `покажи открытые задачи Калачанова за последнюю неделю` and continuation `с 30.09.2026`, if environment accessible. Do not hardcode historic counts; compare fresh source facts and exact arguments. Distinguish environment 429s from deterministic parser failures. Keep read scope bounded.
5. Run mandatory full V4 and relevant Task API/SWTR regression suites, frontend build, brief UI smoke if available. Reconfirm prior A229M2.2B1 3-goal regressions are not broken; ensure no new leaks, writes or unscoped reads. Report actual tests, skipped/failed and reason when unable.
6. All implementation changes forbidden. Do not treat preexisting A230R1 RED cases C3–C5 as fixed. This is a **partial gate for R2.1 only**.

### Deliverable
Report under `po-agent-platform-v2/qa_reports/AGENT_CORE_V4_A230R2_1_WEEK_PERIOD_QA.md`: TESTED_HEAD, Core 6/6 hashes, flags, case-by-case GREEN/RED, raw first failing boundary, AS21 A/B parity or unavailable reason, suite/build counts, open semantic issues. Commit/push **report file only**, and return report commit SHA.

### Short command
Run A230R2.1-QA from GIGACODE_NEXT_ACTION.md. QA only, no implementation changes. Stop and report on RED.
