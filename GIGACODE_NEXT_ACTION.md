# GigaCode — CURRENT NEXT ACTION

## A230R3.20-R2-P31-D2-R4-SOURCE-PROOF-FIXTURE-QA

**INDEPENDENT QA ONLY.** Do not edit source, tests, docs, configs, frozen Core, Git history or Public. No commits, pushes, merges, source writes or unbounded scans. Preserve dirty files and all running user services. Fetch origin and record LOCAL=REMOTE=TESTED_HEAD.

### Previous independent R1 verdict
A230R3.20 QA on `fe2353b` was **D2_R4_RED** caused by the *owner's test fixture*, not the route: `task-api/tests/test_sprint_forecast_source_route.py::test_facade_passes_plain_args_and_returns_safe_counts` constructed `HistoryEvent` without the required `actor` field. Pydantic ValidationError occurred in synthetic fixture and was correctly caught by route's `except ValueError` -> masked 502. R1 had 3/4 owner route tests, but independent 18/18 HTTP adversarial checks (400/422/502/504 typed, <=100 task bound, no raw PII), real bounded DMS-SPRNT-5 AS21 A/B EXACT (as-of QA time: 34 tasks, 23 terminal, 34 complete histories, ~4.2s), collector 6/6, source 16/16, forecast 11/11, V4 299, frontend build 0. Task API 129 passed/26 failed: previous 25 baseline plus fixture. Core 6/6 byte-identical.
Client QoS note: route overall budget 90s matches adapter default 90s; later live plugin client should use explicit >90s read budget or consider reducing route budget, never treat a timeout as 0.

### Owner-only R2 patch
`aa8ce1f` changes **one line in test fixture**: supplies `actor="Test.User"` to synthetic `HistoryEvent`. No production code, API, MCP, Frontend or Core changes. Not yet QA-certified.

### Independent gates
1. Integrity: compare with `fe2353b`; only test fixture + current QA assignment changed. Confirm Core 6/6 frozen `6fb335d` hashes. Check test actor synthetic and no real employee names.
2. Run new route tests 4/4 expected, collector 6/6, source-contract 16/16 and pure forecast 11/11; repeat previously RED route success, verify 9-key sanitized envelope, plain handler kwargs, complete=true & history evidence, no raw history/PII and no invented forecast.
3. Adversarial path: invalid sprint (400), incomplete source/history (422), invalid MCP payload (502), timeout (504), client/handler exceptions accurately translated (not false 200). Verify mixed code/history identity, no source mutation. Do not add QA code to tracked tree.
4. Run full V4 (~299), Task API source-backed/full baseline and frontend build; distinguish 25 prior Task API failures (21 legacy local CRUD + 4 MCP environment) from any new failure; no blanket GREEN.
5. REAL AS21 recheck bounded DMS-SPRNT-5 only if useful and authorized, exact as-of/count; prior R1 live oracle parity is not invalidated by a fixture-only change.
6. Report tested HEAD, all gates, Core 6/6, and `D2_R4_R2_GREEN` or `RED` with first failing boundary. No fixes by GigaCode. STOP.

### Short command
Run A230R3.20-R2-P31-D2-R4-SOURCE-PROOF-FIXTURE-QA from Review GIGACODE_NEXT_ACTION.md. Independent QA only: 4/4 source-proof route tests after actor fixture fix, full regress, source completeness, no JSON/PII leak, Core 6/6. No commits, report and STOP.
