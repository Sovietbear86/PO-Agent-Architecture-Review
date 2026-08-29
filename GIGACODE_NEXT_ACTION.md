# GigaCode — Current QA Action

## Status

`ACTIVE_QA_ASSIGNMENT`

## Active assignment

Run exactly:

`qa_assignments/CORE8_SEMANTIC_SLOT_SAFETY_NET_RETEST_070.md`

## Why this assignment is active

Assignment 069 completed `RED_PRODUCT_DEFECT` and proved that both the primary semantic LLM and the dedicated flat recovery LLM can deterministically return empty/invalid semantic slots in the real runtime.

The owner/developer has now added a second bounded safety layer that preserves only explicit literal request constraints and leaves AS21 entity/source grounding downstream.

## Production fixes under test

Required ancestors of tested HEAD:

- `88d602ff006bb5b3af4c3ca5c157a52055f43620` — bounded LLM slot recovery
- `b9f46a1353c10ec93efe1381508ec5201c452e6d` — deterministic literal semantic-slot safety-net
- `d2cd375a7c3763a2e051ae583128127636687fdb` — targeted safety-net tests

The deterministic layer must not contain or invent team-member IDs, logins, source facts or AS21 entity IDs. It only preserves explicit literal spans from the user's request.

## Role

QA/tester only.

Do not modify production code, prompts, tests, fixtures, credentials, wrappers, runtime configuration or AS21/SWTR data.

## Mandatory rules

1. Fetch/pull `feat/core8-real-query-hardening-v2` first and record `START_HEAD`.
2. Prove all required production/test commits are ancestors of tested HEAD.
3. Start fresh/current-checkout PO Agent and Task API processes and prove runtime provenance.
4. Run the existing runtime freshness and SWTR health preflight before live tests.
5. Execute Assignment 070 exactly as written.
6. Live positive certification uses REAL AS21/SWTR only; no fake/mock positive data.
7. Run required semantic probes three times with independent sessions.
8. Include cross-space checks beyond DMS where source access permits.
9. Include the mandatory genuine-correction control.
10. Do not repair failures or weaken expectations.
11. If 070 is RED, report the first proven failing boundary and STOP.
12. Do not start 060/062 or any later assignment automatically.
13. Commit/push only `qa_reports/CORE8_SEMANTIC_SLOT_SAFETY_NET_RETEST_070.md`, then STOP.

## Required completion summary

Report at minimum:
- START_HEAD;
- ancestor proof;
- fresh/current runtime proof;
- SWTR health verdict;
- automated test counts;
- semantic probe matrix × 3;
- semantic slot PASS/FAIL counts;
- cross-space results;
- genuine-correction verdict;
- anti-hallucination verdict;
- HTTP 500 count;
- fake/mock source call count;
- new product regressions count;
- READY_FOR_060_FULL_RERUN = YES/NO;
- final 070 verdict;
- QA report path and commit SHA.

STOP after Assignment 070.