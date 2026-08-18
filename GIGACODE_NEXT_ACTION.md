# GigaCode — NEXT ACTION

## Context
The attachment wiring implementation has already been completed and the QA report `qa_reports/AS21_A3_ATTACHMENT_WIRING_RETEST_005.md` was generated.

Current state from the report:
- `ATTACHMENT_WIRING_READY_FOR_PROMOTION = NO` only because the running `task-api` instance has not loaded the new `swtr_read` router.
- The route exists in code.
- Do **not** redo the implementation that is already complete.
- Do **not** repeat completed static checks unless required to diagnose a failure.

## Required action

1. Restart the local `task-api` application so the current code and the new `swtr_read` router are loaded.
   - Work from the repository's `task-api` directory.
   - Prefer the repository's documented/native start command.
   - If the application is currently running in a process you cannot enumerate or terminate because of sandbox restrictions, do **not** declare the test failed. Report exactly what manual action is required from the user.

2. After restart, verify that the running application exposes the new SWTR attachment route, including:
   - `GET /api/v1/swtr-read/tasks/{task_code}/files`
   - and any related download/content endpoint required by the attachment skill.

3. Run the attachment test against **real AS21 data**, not mocks.
   - Use the previously identified real task belonging to Kalachanov in WMB that contains attachment(s), or another already verified real task with attachments if the exact task key is recorded in the existing QA evidence.
   - Verify metadata discovery first.
   - Then verify retrieval/download/content path for at least one real attachment where the API permits it.

4. Validate end-to-end wiring:

   `real AS21 task -> SWTR read -> attachment metadata -> attachment retrieval -> canonical evidence -> Harness skill response`

5. Fail closed. Do not mark GREEN merely because the route exists in source code. GREEN requires successful verification against the running server and real AS21 evidence.

6. Regression safety:
   - run the targeted attachment tests;
   - run the relevant production/harness regression suite;
   - confirm `NEW_CODE_REGRESSIONS_VS_PREVIOUS_GREEN = 0`.

## Result file

Update or create:

`qa_reports/AS21_A3_ATTACHMENT_WIRING_RETEST_006.md`

The report must contain:
- git branch + HEAD;
- server start/restart evidence;
- route registration evidence;
- real task key used;
- real attachment metadata returned;
- attachment retrieval result;
- Harness-level result;
- targeted test counts;
- regression counts;
- blockers, if any;
- exact commands/actions performed;
- final verdict: `GREEN`, `YELLOW`, or `RED`;
- `ATTACHMENT_WIRING_READY_FOR_PROMOTION = YES/NO`.

## Important sandbox rule

If GigaCode cannot restart/stop the already-running server because process enumeration or process control is denied, stop at that boundary and write into the report:

`MANUAL_ACTION_REQUIRED = restart task-api`

plus the exact command the user should run. Do not attempt unsafe workarounds and do not fabricate runtime evidence.

## Scope discipline

GigaCode is acting as **tester/reviewer**, not primary developer. Do not make unrelated architectural changes. If a genuine implementation defect is discovered, document it with file/function/evidence in the report and leave the code change for the primary development loop.
