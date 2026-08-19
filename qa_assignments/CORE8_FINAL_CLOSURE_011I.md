# QA Assignment: CORE8 FINAL CLOSURE 011I

## Mission
Close Core-8 validation now. This is the final acceptance gate before Learning Loop 012.

GigaCode is **tester only**. Do not edit production code, tests, configuration contracts, or expected results. If something fails, capture exact evidence in the report and stop after completing the matrix.

## Mandatory startup
1. `git pull` branch `feat/real-baseline-candidate-eval-v1`.
2. Record exact HEAD.
3. Restart Task API and PO Agent from that HEAD; prove PIDs/ports.
4. Verify MCP-SWTR connectivity.
5. Do not mutate AS21.

## Developer fixes that must be present
Validate these commits or their descendants:
- `4b2bca2` — multiple product/space conflict protection.
- `114856a` — explicit release grounding from production source-backed release facts.
- `eb55358` — exact-task alias normalization and tighter product scoping.
- `5fee275` — Task API E2E regression expectation aligned with the proven exact rich-read contract.

## A. Fast targeted regression first
Run these exact tests before manual E2E:

```bash
cd po-agent-platform-v2
pytest -q \
  tests/test_harness_task_api_e2e.py::test_task_api_end_to_end_query_maps_source_to_harness_contract \
  tests/test_harness_dialogue_runtime.py::test_dialogue_clarifies_multiple_ambiguous_slots_before_execution \
  tests/test_harness_dialogue_runtime.py::test_dialogue_executes_with_extracted_task_key
```

Required result: `3 passed`.

If any fails, do not modify code. Record traceback, actual response/frame and continue the black-box tests so the report remains complete.

## B. Prove the real release anchor
Use canonical real AS21 task data / `fix_version_s`, not a fabricated fixture.

Preferred already-proven anchor from 011H:
- release id: `743559fc-f632`
- space/tasks: CRPV, 7 tasks in 011H
- known evidence included `CRPV-99359`, `CRPV-99358`, `CRPV-94870`

Revalidate it on current HEAD. If the live dataset changed, select another release actually present in canonical AS21 tasks and record the exact ID + evidence task keys.

The external MCP `search_versions` ToolError is tracked as an external dependency and is **not a blocker to Core-8** if the production source-backed `fix_version_s` fallback successfully grounds and executes a real release. Never hide the external error in the report.

## C. Exact Core-8 matrix — all 8, no denominator games
Execute through the real production endpoint `/api/v1/query` only.

1. `task_search`
   - `Найди задачи Гончарова в актуальном спринте по OLAP`
   - Expected: `COMPLETED`, real assignee + OLP + live current sprint grounding, evidence from AS21.

2. `task_summary`
   - `Суммаризируй задачу WMB-30000`
   - Expected: `COMPLETED`, exact WMB-30000 evidence.

3. `task_quality`
   - `Оцени качество постановки WMB-30000`
   - Expected: `COMPLETED`, exact task evidence; Office/XLSX visibility must not regress.

4. `sprint_health`
   - `Покажи здоровье текущего спринта OLP`
   - Expected: `COMPLETED`, current sprint resolved live, not guessed.

5. `velocity`
   - `Покажи velocity текущего спринта OLP`
   - Expected: `COMPLETED`, complete sprint data path.

6. `team_workload`
   - `Какая нагрузка у Калачанова?`
   - Expected: `COMPLETED`, real team identity + AS21 work evidence.

7. `competency_match`
   - `Подбери исполнителя для WMB-30000`
   - Expected: `COMPLETED`, real team/competency knowledge + task evidence.

8. `release_health`
   - Use the revalidated exact real release ID from section B, e.g. `Покажи здоровье релиза 743559fc-f632`.
   - Expected: `COMPLETED`.
   - Response must contain the exact grounded release ID and task-backed evidence belonging to that release.

Report strictly `CORE8_AGENT_E2E_PASS = x/8`. Anything below 8/8 is NO-GO.

## D. False-green closure matrix
All attacks must fail closed as `FAILED`, `NEEDS_CLARIFICATION`, empty source-backed result where semantically valid, or HTTP 4xx at validation boundary. None may silently execute with a discarded contradictory selector.

Run at least:

1. Current + explicit sprint conflict:
   `Найди задачи Гончарова в текущем спринте OLP и в OLP-SPRNT-4`

2. Two explicit sprint IDs:
   `Найди задачи Гончарова в OLP-SPRNT-4 и OLP-SPRNT-5`

3. Two product/space selectors:
   `Найди задачи Гончарова в спринтах OLP и DMS`
   Required: not `COMPLETED`; response should expose product/space ambiguity rather than silently pick OLP or DMS.

4. Nonexistent exact task: `Покажи задачу NONEXISTENT-99999`.
5. Nonexistent assignee.
6. Nonexistent sprint.
7. Nonexistent release.
8. Unsupported request.
9. Weather/arithmetic request.
10. Invalid JSON body -> HTTP 422.

Set `FALSE_GREEN_ATTACKS_PASS=YES` only if all pass.

## E. Sprint completeness and attachment preservation
Recheck:
- OLP first page may expose `hasNext=true`.
- complete mode produces full canonical sprint set with no duplicate task IDs.
- WMB-30000 still exposes all 5 XLSX attachments proven by 010B/011G unless live AS21 itself changed; if changed, distinguish live-data drift from code regression.

## F. Full regression and triage
Run full pytest suite.

For failures, classify exactly:
- `PRODUCTION_REGRESSION`
- `STALE_EXPECTATION_PROVEN_IMPROVEMENT`
- `ENVIRONMENT/EXTERNAL`

Known historical non-production candidates from 011H must not be relabeled as production merely to block the gate:
- old PDF-absence expectation after PDF discovery improvement;
- unknown-status stale expectation if current canonical contract intentionally preserves unknown status;
- local `.gigacode`/artifact environment hygiene issue.

The gate requires **zero remaining HIGH `PRODUCTION_REGRESSION`**. It does not require falsifying correct behavior to make stale/environment tests green.

## G. Learning Loop authorization decision
`READY_FOR_LEARNING_LOOP_012 = YES` iff ALL are true:
- `CORE8_AGENT_E2E_PASS = 8/8`
- `REAL_RELEASE_HEALTH_E2E_PASS = YES`
- `FALSE_GREEN_ATTACKS_PASS = YES`
- `TARGETED_HIGH_PRODUCTION_REGRESSIONS = 0`
- current-sprint completeness is still proven
- WMB-30000 attachment regression is green (or documented live-data drift)
- `AS21_MUTATIONS_DURING_TEST = 0`
- no new HIGH production regression introduced by current commits.

External MCP `search_versions` ToolError alone does not veto the gate when the source-backed canonical release fallback is proven E2E. Record it as `EXTERNAL_DEPENDENCY_ISSUE`.

## Required report
Publish and push:
`qa_reports/CORE8_FINAL_CLOSURE_011I.md`

Required sections:
1. Environment / branch / HEAD / PIDs.
2. Developer commit validation.
3. Targeted 3-test regression result with exact node statuses.
4. Real release anchor and AS21 evidence.
5. Full 8-row Core-8 matrix.
6. Full false-green matrix.
7. Sprint completeness.
8. WMB-30000 attachment regression.
9. Full pytest numbers and triage of every remaining failure/error category.
10. External MCP status.
11. Gate decision.
12. Machine-readable footer.

Machine-readable footer:
```text
ASSIGNMENT_ID = CORE8_FINAL_CLOSURE_011I
CURRENT_HEAD = <sha>
TARGETED_THREE_PRODUCTION_TESTS_PASS = YES|NO
REAL_RELEASE_ID = <id>
REAL_RELEASE_HEALTH_E2E_PASS = YES|NO
CORE8_AGENT_E2E_PASS = x/8
FALSE_GREEN_ATTACKS_PASS = YES|NO
SPRINT_COMPLETENESS_PASS = YES|NO
ATTACHMENT_REGRESSION_PASS = YES|NO|LIVE_DATA_DRIFT
TARGETED_HIGH_PRODUCTION_REGRESSIONS = N
FULL_REGRESSION_PASSED = N
FULL_REGRESSION_FAILED = N
FULL_REGRESSION_ERRORS = N
EXTERNAL_SEARCH_VERSIONS_TOOL_HEALTH = PASS|FAIL
NEW_HIGH_PRODUCTION_REGRESSIONS = N
AS21_MUTATIONS_DURING_TEST = N
READY_FOR_LEARNING_LOOP_012 = YES|NO
```

## Stop rule
After publishing the report, STOP. Do not start Learning Loop 012 yourself. Do not edit code/tests. Do not expand to 48 skills yet. The report is the authorization evidence for the next phase.
