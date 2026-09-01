# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_118R_POST_RESTORE_GARANIN_RETEST`

## Context
Assignment 118 correctly identified that the earlier owner rollback reintroduced a previously proven semantic-context regression: canonical `Task.title` again had `max_length=200`, while valid AS21 tasks can exceed 200 characters. The owner has now restored that already-proven fix in commit `c6cec85c23dc0786d597b7d4f46f46cde50831f4`.

This is NOT a new hypothesis and does NOT authorize any synchronization or local DB work.

## Absolute prohibitions
- NO task synchronization/population utilities.
- NO local DB refresh/population.
- NO local DB/cache as Oracle.
- NO fake/mock/frozen data.
- NO AS21 writes.
- NO assignee extraction changes.
- NO frontend changes.
- NO new speculative fixes.
- NO arbitrary users outside authoritative team data.
- NO task evidence outside WMB/STS/OLP/DMS/CRPV.

If you conclude that synchronization is required, STOP and classify that conclusion as invalid for this assignment. The production query must work from the live MCP-SWTR/REAL AS21 path without populating a local database.

## Goal
After the owner restored the previously proven long-title fix, re-run the original user-visible defect only:
`Задачи Гаранина`

Determine whether semantic interpretation now succeeds and, if it does, compare Browser UI, Direct Harness and a correctly scoped REAL AS21 Oracle.

## Phase 0 — fresh runtime
1. Pull current branch `feat/core8-real-query-hardening-v2`.
2. Prove HEAD contains owner commit `c6cec85c23dc0786d597b7d4f46f46cde50831f4`.
3. Restart normal Frontend, Harness and Task API services from current HEAD. Do not run any sync process.
4. Record PIDs/ports/start times.
5. Verify MCP-SWTR health and one REAL DMS/OLP point read.

## Phase 1 — semantic smoke
With fresh Harness sessions execute exactly:
- `Задачи Гаранина`
- `Задачи спринта DMS-SPRNT-2`
- one exact DMS task key lookup

For each record status, warnings, semantic intent/frame/slots if available and elapsed time.

Primary assertion: `Задачи Гаранина` must no longer fail because of the >200-character canonical-title validation error.

If it still fails, capture the exact exception. Do not speculate and do not change code.

## Phase 2 — Browser vs Direct Harness
Execute exact text `Задачи Гаранина` through:
A1. Browser UI with fresh session.
A2. Direct Harness using the exact same `/api/v1/query` contract.

Capture actual request URL/body/session ID, response status, semantic result and exact returned task keys.

## Phase 3 — scoped Oracle B
Build authoritative Oracle only for repository team member `Garanin.R.V` and only spaces:
`WMB, STS, OLP, DMS, CRPV`.

Requirements:
- use REAL MCP-SWTR/AS21 directly;
- validate the actual member-filter semantics before trusting results;
- inspect `assigned_to` on returned source rows;
- discard out-of-scope spaces;
- read all pages needed for completeness;
- record exact task-key set.

If a candidate MCP tool returns identical unrelated rows for different members, do not use that tool as Oracle.

## Phase 4 — parity decision
Compare exact sets:
`Browser UI keys == Direct Harness keys == scoped Oracle B keys`.

Counts alone are insufficient.

If Browser and Direct Harness both fail before source execution, report the exact first failing semantic boundary.
If semantic succeeds but the product result differs from Oracle, trace only the first downstream boundary actually exercised by this request.

## Mandatory guardrails
- No invented sprint for `Задачи Гаранина`.
- Russian user-facing text only.
- No arbitrary control members.
- No positive task evidence outside WMB/STS/OLP/DMS/CRPV.
- sync/population runs = 0.
- local DB authoritative reads = 0.
- fake/mock/frozen reads = 0.
- AS21 writes = 0.

## Counters
- Browser natural-language requests >= 1
- Direct Harness natural-language requests >= 3
- Scoped Oracle REAL AS21 reads >= 1

## Output
`po-agent-platform-v2/qa_reports/POST_RESTORE_GARANIN_RETEST_118R.md`

Allowed verdicts:
- `GARANIN_THREE_WAY_PARITY_GREEN`
- `SEMANTIC_DEFECT_REMAINS`
- `DOWNSTREAM_ROUTE_DEFECT_PROVEN`
- `ORACLE_CONTRACT_NOT_PROVEN`
- `BLOCKED_BY_ENVIRONMENT`

Commit/push only QA artifacts, provide full SHA, then STOP.

## Start now
Execute autonomously. No production changes, no synchronization, no local DB population.