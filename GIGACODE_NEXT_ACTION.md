# GigaCode — CURRENT NEXT ACTION

## A230R3.18-P31-D2-R1-SOURCE-VALIDATION-QA

**Independent QA ONLY. No code edits, commits, pushes, merges, service termination, unbounded source queries or AS21 writes.** Preserve all local dirty files and user services. Before testing fetch origin and record LOCAL_HEAD=REMOTE_HEAD=TESTED_HEAD. Frozen Core V4 six files unchanged.

### Proven earlier baseline
A230R3.17 concluded **READY_TO_IMPLEMENT** on `426a100`: complete sprint GET `/api/v1/swtr-read/sprints/{id}/tasks?complete=true` exposes `complete=true`, `membership_proven=true`, canonical `source_id` and TQL pagination fallback; `/tasks/{code}/history` exposes source `workflow_status`, UTC `changed_at` with completeness. DMS-SPRNT-5 bounded oracle had 35 tasks, 20 terminal, one page at prior timestamp. Product-local timezone and working calendar are configuration obligations, not AS21 facts. Committed baseline absent: historical Predictability stays N/A.

### Owner D2 first implementation (NOT QA certified)
- `de6ce94` new `task-api/app/services/sprint_forecast_source.py`: fail-closed **pure validator** for complete sprint membership, canonical identity, proven membership, max task cap, per-task history completeness and timezone-aware status-change evidence.
- `f49251c` new `task-api/tests/test_sprint_forecast_source_contract.py`: offline contract tests (no REAL AS21 calls, no source mutation).
- No REST endpoint, no Task API live collector, no adapter conversion, no V4 plugin wiring or UI yet; **DO NOT claim live forecast exists**.
- Both files outside frozen Agent Core V4, no modifications to legacy sprint health code.

### Gate 0 — source integrity
Confirm only these two new source/test files plus updated QA spec since `426a100`, and all 6 frozen Core files byte-identical to `6fb335d`. Check no secrets, user-specific paths, internal hostnames or write-capable APIs.

### Gate 1 — unit and adversarial
Run `pytest -q task-api/tests/test_sprint_forecast_source_contract.py` in correct Task API environment; report exact pass/fail. Independently probe malformed `source_data` (None/non-dict), malformed page_info, missing source id, empty scope, > max_tasks, duplicate IDs, duplicate status event ID, inconsistent event ordering, malformed value, naive date, source missing. Must fail closed with typed result/validation failure, not uncaught 500 on live facade. Any unknown closure status is **not** a closure, only a raw status event. Recommend precise minimal owner-only changes for RED.
Run previous forecast 11/11, source-backed Task API battery, full V4 (~299), frontend build; distinguish pre-existing integration/legacy Task API failures.

### Gate 2 — contract audit for next owner patch
Inspect possible safe bounded live collector implementation: use existing `get_sprint_tasks(...complete=true)` and per-task `get_task_history`, concurrency <= 5, max tasks <= 100, no tenant scans, no raw history/PII in user-facing response, explicit source/complete/failure fields, per-call timeout and cancellation. Terminal status mapping must be proven via authoritative source statusType (not guessed "done" text); verify reopened task semantics and timestamps, product-local timezone/calendar explicit config, source complete. If 35 tasks ~1s at 5 concurrent, evaluate practical source latency and MCP transport cold-init. **No code changes by QA.**

### Verdict
`D2_R1_GREEN` only if source validators and tests pass and all contracts sound; else `RED` with first failing boundary. Preserve untracked report, no Git commits. STOP.

### Short command
Execute A230R3.18-P31-D2-R1-SOURCE-VALIDATION-QA from Review GIGACODE_NEXT_ACTION.md. Validate two new source-contract files, 11 forecast tests, full regress, frozen Core 6/6; identify exact boundaries before live REST route. QA only, report and STOP.
