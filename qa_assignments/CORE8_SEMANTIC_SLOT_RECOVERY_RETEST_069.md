# Assignment 069 — CORE8 Semantic Slot Recovery Retest

## Role

You are QA/tester only. Production code has already been changed by the owner/developer.
Do not modify production code, prompts, runtime factory, tests, fixtures, credentials, wrappers or AS21/SWTR configuration.

## Production change under test

Commit: `88d602ff006bb5b3af4c3ca5c157a52055f43620`

Purpose: recover explicit task-search constraints when the primary LLM semantic frame and audit both return an empty nested `slots` object. The recovery is still LLM-first, uses a separate flat JSON contract, and accepts only literal values present in the original user query.

## Preconditions

1. Pull/fetch `feat/core8-real-query-hardening-v2` and record `START_HEAD`.
2. Prove the production commit above is an ancestor of `START_HEAD`.
3. Working tree must be clean apart from allowed QA report artifacts.
4. Stop stale PO Agent / Task API processes and start fresh processes from the current checkout.
5. Prove current-checkout module provenance for the running processes.
6. Run the existing runtime freshness + SWTR health preflight before live tests.
7. All live certification queries must use REAL AS21/SWTR data. No fake/mock positive data.

If runtime freshness or SWTR health fails, STOP with an environment verdict. Do not diagnose generic 403/502 as token/role failure without evidence.

## Phase A — Focused semantic slot recovery

Run each query at least 3 times through the real PO Agent `/api/v1/query` path and capture the semantic frame before grounding/execution.

Required queries:

1. Person only: `Покажи задачи Гаранина`
   - expected explicit slot: `person_raw` with the literal person wording from the query.
2. Product only: `Покажи задачи в DMS`
   - expected: `product=DMS`.
3. Status only: `Покажи задачи со статусом todo`
   - expected: `status_raw=todo`.
4. Person + product: `Покажи задачи Гаранина в DMS`
   - expected: both independent constraints preserved.
5. Multi-filter: use the same multi-filter real query that failed Assignment 060 and verify all explicit independent constraints survive.
6. Exact task key: `Покажи DMS-273`
   - exact task lookup must still work and must not be broadened.
7. Sprint: use a real DMS sprint identifier from current AS21 data and verify literal sprint constraint survives.

For every case report:
- intent;
- extracted slots;
- whether slot recovery was needed if observable without production instrumentation;
- final source query/bound constraints;
- real AS21 result status/count;
- HTTP status;
- repeatability across 3 runs.

## Phase B — Safety / non-broadening

Verify:

1. Recovered raw values are literal spans of the original query.
2. No invented member login/person/product/status/sprint/release is introduced.
3. A query without explicit filters is not given fabricated filters.
4. Existing non-empty primary slots are preserved rather than replaced by the recovery pass.
5. Exact task-key and sprint structural handling remains correct.
6. No silent fallback to fake/mock data.

## Phase C — Genuine correction control

Because the latest 067 run did not certify genuine correction, run one real conversation control:

A1. Ask a real task/person query.
A2. Explicitly correct one semantic constraint, e.g. `Нет, я имел в виду Моисеева` using a real team member available in the configured team/source.
A3. Repeat/confirm the corrected request.

Required:
- dialogue act recognized as correction;
- corrected constraint replaces the previous one;
- unrelated constraints remain stable;
- authoritative real source is rechecked;
- no HTTP 500;
- correction is not mistaken for clarification replay.

## Phase D — Targeted automated regression

Run at minimum:

- `po-agent-platform-v2/tests/test_semantic_core_v2.py`
- `po-agent-platform-v2/tests/test_semantic_slot_recovery.py`
- semantic frame boundary tests relevant to Core8;
- task lookup/search regression tests relevant to Assignment 060.

Report total/pass/fail/skip. Any unexpected failure means RED.

## Phase E — Resume gate for Assignment 060

If and only if A-D are GREEN, rerun the semantic-slot portion of Assignment 060 against the fresh current process and real AS21 source.

Required before GREEN:
- person slot PASS;
- product slot PASS;
- status slot PASS;
- multi-filter slot preservation PASS;
- genuine correction PASS;
- HTTP 500 count = 0;
- unexpected broadening = 0;
- fake/mock source calls = 0;
- new product regressions = 0.

Do NOT start Assignment 062.

## Report

Create only:

`qa_reports/CORE8_SEMANTIC_SLOT_RECOVERY_RETEST_069.md`

Do not commit helper scripts, generated JSON, screenshots, logs, credentials, `.env`, test modifications or production changes.

## Final verdict

Return exactly one:

- `GREEN_SLOT_RECOVERY_CERTIFIED`
- `RED_PRODUCT_DEFECT`
- `ENVIRONMENT_BLOCKED`

Required completion summary:

- START_HEAD
- production fix ancestor proof
- fresh-process/current-checkout proof
- SWTR health verdict
- focused query matrix with 3x repeatability
- semantic slot pass/fail counts
- genuine correction verdict
- automated test counts
- HTTP 500 count
- fake/mock source call count
- new product regressions count
- Assignment 060 resume/retest verdict
- `READY_FOR_060_FULL_RERUN = YES/NO`
- report path
- QA commit SHA

Commit and push only the allowed QA report, then STOP.
Do not start Assignment 062 or any later assignment.