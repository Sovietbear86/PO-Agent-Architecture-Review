# Developer/QA Handoff: CORE8 RELEASE HEALTH FIX 011K

## Context
011J proved 7/8 Core-8 production E2E. Release grounding itself is healthy: short release UUID `743559fc-f632` resolves to full canonical AS21 UUID `743559fc-f632-4c3f-8d14-ee5e1516a814`. The remaining release-health failure is between semantic interpretation and deterministic execution: `release_id` is grounded, but the canonical query does not reliably carry `{release_id}`, so runtime returns `semantic_slot_missing` / `NEEDS_CLARIFICATION`.

GigaCode remains TESTER ONLY for this assignment. Do not edit production code, tests, fixtures, configuration, or AS21.

## Developer contract to validate
The production fix must be generic, not hardcoded to the current UUID:
1. For an explicit release-health utterance, preserve/select canonical intent `release_health`.
2. If the interpreter/grounder has a grounded `slots.release_id`, canonical execution must consume that slot even if the provider emitted a deficient canonical_query.
3. The canonical query for release-health must contain/use `{release_id}` before execution, or execution must be slot-driven in an equivalent deterministic way.
4. Never invent a release ID. Unknown/nonexistent/ambiguous releases remain fail-closed / clarification.
5. Do not weaken entity grounding, false-green protection, or source validation.

## Test A — Real release-health E2E
Restart Task API and PO Agent from current branch HEAD. Through real `/api/v1/query`, execute:
- `Покажи здоровье релиза 743559fc-f632`
- same request with the resolved full UUID

Required for both:
- status `COMPLETED`
- skill `release-health`
- short UUID resolves to the same full UUID proven in current AS21
- response data contains exact grounded `release_id`
- evidence contains real AS21 tasks from that release
- no unnecessary clarification

If live data changed, discover a current real release from canonical `fix_version_s` and repeat both shorthand/full-ID forms. Report live-data drift explicitly.

## Test B — Genericity / no hardcoding
Choose at least one SECOND distinct real release from canonical AS21 data and run release-health using its full ID and, when uniquely resolvable, a shorthand prefix.

Required: same execution path succeeds. Search production diff/source for hardcoded `743559fc-f632` special-casing; none is allowed outside tests/QA evidence.

## Test C — Fail-closed release controls
Execute:
- `Покажи здоровье релиза NONEXISTENT`
- an ambiguous release shorthand if a naturally ambiguous live candidate exists; otherwise document that no such live ambiguity exists
- release-health wording with no release identifier

Required: never `COMPLETED` with fabricated/default release. Return clarification/failure as appropriate.

## Test D — Core-8 matrix
Repeat all 8 production queries from 011J. Required: `CORE8_AGENT_E2E_PASS = 8/8`.

## Test E — Source and false-green invariants
Re-run:
- 10 false-green controls from 011J
- current OLP sprint completeness/pagination check
- WMB-30000 attachment check (5 XLSX unless proven live-data drift)

Required: all remain green.

## Test F — Two disputed regression tests
Run individually:
- `test_runtime_factory_runtime_records_production_execution_history`
- `test_portfolio_overview_never_labels_task_api_data_as_fake`

Important classification rule: a production adapter rejecting an invalid/empty source payload with `source_protocol_error` is NOT by itself a production regression when the intended source contract is fail-closed. Compare the test expectation to the current documented production contract. If the test still expects `COMPLETED` from malformed/invalid source data, classify `STALE_EXPECTATION_AFTER_FAIL_CLOSED_HARDENING`, not HIGH production regression. Do not weaken production validation to satisfy it.

Only classify `PRODUCTION_REGRESSION` if a valid source response now fails or correct source-backed behavior is lost.

## Test G — Focused + full regression
Run targeted release semantic/runtime tests, then full pytest. Compare with 011J baseline (`1166 passed, 6 failed, 11 errors`). Triage failures honestly. New HIGH production regressions must be zero.

## Authorization
Set `READY_FOR_LEARNING_LOOP_012 = YES` iff:
- Core-8 = 8/8
- real release-health E2E = PASS
- second-release genericity = PASS
- false-green = PASS
- sprint completeness = PASS
- attachments = PASS or proven live drift
- targeted HIGH production regressions = 0
- new HIGH production regressions = 0
- AS21 mutations = 0

## Report
Publish and push `qa_reports/CORE8_RELEASE_HEALTH_FIX_011K.md` with evidence and footer:

```text
ASSIGNMENT_ID = CORE8_RELEASE_HEALTH_FIX_011K
CURRENT_HEAD = <sha>
CORE8_AGENT_E2E_PASS = x/8
REAL_RELEASE_HEALTH_E2E_PASS = YES|NO
SECOND_RELEASE_GENERICITY_PASS = YES|NO
RELEASE_FAIL_CLOSED_PASS = YES|NO
FALSE_GREEN_ATTACKS_PASS = YES|NO
SPRINT_COMPLETENESS_PASS = YES|NO
ATTACHMENT_REGRESSION_PASS = YES|NO|LIVE_DATA_DRIFT
TARGETED_HIGH_PRODUCTION_REGRESSIONS = N
STALE_EXPECTATIONS_AFTER_FAIL_CLOSED_HARDENING = N
FULL_REGRESSION_PASSED = N
FULL_REGRESSION_FAILED = N
FULL_REGRESSION_ERRORS = N
NEW_HIGH_PRODUCTION_REGRESSIONS = N
AS21_MUTATIONS_DURING_TEST = N
READY_FOR_LEARNING_LOOP_012 = YES|NO
```

After publishing, STOP. Do not start Learning Loop 012 until the report is reviewed.