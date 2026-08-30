# GigaCode — Current Action

## Status

`ACTIVE_QA_ASSIGNMENT_095`

## Role boundary — mandatory

You are QA/tester only.

**DO NOT modify production code, prompts, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, GIGACODE.md, PO_AGENT_HARNESS_EVOLUTION_PLAN.md, or this file.**

The production candidate is immutable for this assignment. If a new defect is found, prove the first failing boundary and report it. Do not repair it.

Assignment 072 is accepted GREEN. 072F proved the protected correction + persistent Learning Loop, including persistence, generalization, process replacement/reload and rollback. Do not reopen 072 unless Assignment 095 produces a concrete regression.

## Assignment 095 — Total Real-Agent Backend Certification

### Goal

Certify the **entire callable production skill catalog**, not only Core-8 and not a remembered/manual subset.

For every discovered production skill, determine and prove:

`functional behavior`
`+ REAL source correctness where source-backed`
`+ evidence/trace correctness`
`+ natural-language robustness`
`+ applicable Learning Loop behavior`
`+ persistence/restart/rollback safety`

Allowed final verdicts only:

- `FULLY_CERTIFIED`
- `REGRESSION_DETECTED`
- `BLOCKED_BY_ENVIRONMENT`

Do not start frontend work or any later assignment.

Production mode: `task-api` + REAL read-only AS21(SWTR).

## Phase 0 — clean provenance and runtime truth

1. Fetch/pull `feat/core8-real-query-hardening-v2`.
2. Record exact tested HEAD SHA and branch.
3. Record `git status --short`; production files must be clean.
4. Restart PO Agent + task-api from exact HEAD.
5. Record PID/start timestamps, package root, launch commands and relevant runtime mode variables.
6. Prove REAL AS21(SWTR) mode.
7. Prove fake/mock/frozen authoritative source mode is not active.
8. Record policy-store backend/location and active learned-policy baseline.
9. Record source/environment health before starting the matrix.

## Phase 1 — discover the authoritative production skill catalog

Do not use a hardcoded skill count as the source of truth.

Dynamically enumerate the callable production skills from the **running production registry/catalog/runtime**.

For every discovered skill capture:
- `skill_id`;
- version;
- callable/active state;
- required slots/arguments;
- source dependency/capability;
- whether REAL AS21 evidence is applicable;
- whether the persistent Learning Loop is applicable under current production policy.

Cross-check the discovered catalog against `PO_AGENT_48_SKILL_MATRIX.md` and the historical `48 original + 6 reconciled` inventory. Report missing, extra, disabled, duplicate or unreachable skills explicitly. Runtime discovery is authoritative.

Create a stable ordered skill list and use exactly that list for all later matrices.

## Phase 2 — functional black-box certification for EVERY discovered skill

For each discovered callable skill execute at minimum:

1. one canonical Russian natural-language query;
2. one meaning-preserving paraphrase with different wording/order;
3. one relevant edge/negative/clarification case where the skill contract has required slots or ambiguity;
4. REAL source-backed verification where applicable.

For source-backed skills, a HTTP 200 or plausible prose answer is not enough. Validate the deterministic business result against an independent REAL AS21 oracle/read path whenever the contract permits it.

Capture for each skill:
- exact query;
- resolved `skill_id`;
- semantic slots/arguments;
- deterministic capability call;
- authoritative source evidence;
- returned task/entity key set or deterministic metric where applicable;
- expected vs actual;
- evidence/trace IDs;
- PASS/FAIL/BLOCKED.

Do not infer PASS from previous reports. Assignment 095 must exercise the current HEAD.

## Phase 3 — mandatory historical high-risk regression pack

Regardless of the per-skill matrix, explicitly rerun and prove these historical classes:

### Exact task key
- exact task-key lookup through authoritative point read;
- include at least two valid real task IDs and one nonexistent ID;
- must not depend on bounded list cache.

### Sprint constraints
- sprint ID only;
- sprint + person;
- sprint + status;
- sprint + product/project where supported;
- prove requested constraints survive semantic interpretation and grounding.

### Multi-filter semantic preservation
- person only;
- status only;
- person + product + status;
- independent second team member;
- corrected status replaces old status rather than coexisting;
- correction preserves unaffected previous slots.

### History/changelog/attachments
For every production skill requiring these capabilities, prove the requested source evidence comes from the correct REAL source path and is not synthesized from task summary prose.

### Sprint Intelligence and Team Workload
Re-run their complete deterministic metric/key-set checks against an independent REAL oracle. Count-only equality is insufficient where exact key-set equality is available.

## Phase 4 — evidence and source integrity audit

Across the complete functional matrix prove:
- REAL AS21 read paths used where required;
- AS21 writes = 0;
- fake/mock/frozen authoritative calls = 0;
- HTTP 500 count;
- HTTP 502 count with endpoint/time mapping;
- every 502 classified as affecting / not affecting a certification row;
- no business fact is accepted solely from LLM prose;
- evidence/trace corresponds to the actual source/capability call.

If a required skill cannot be tested because REAL AS21 is unavailable, mark that row BLOCKED. Do not replace it with fake evidence.

## Phase 5 — per-skill Learning Loop applicability matrix

For **every discovered production skill**, classify exactly one:

- `APPLICABLE_AND_TESTED`
- `NOT_APPLICABLE_BY_POLICY`
- `BLOCKED`
- `FAILED`

`NOT_APPLICABLE_BY_POLICY` requires concrete production-policy/code/catalog evidence explaining why learning must not apply to that skill. Do not use it merely to avoid testing.

For each applicable skill, prove the production Learning Loop contract using a safe bounded negative/correction pattern:

`initial execution`
`-> explicit negative feedback/correction`
`-> fresh authoritative source validation when source-backed`
`-> generalized allow-listed policy candidate/promotion`
`-> persistent policy ID/version/skill_id/audit`
`-> no entity/answer memorization`
`-> different query/entity benefits`
`-> policy remains/reloads across a genuine process restart`
`-> same policy is applied after restart`
`-> rollback/deactivation`
`-> policy no longer applies after rollback`

Use the existing production policy mechanism only. Do not create test-only learning behavior.

### Efficiency rule for restart testing

Do **not** restart once per skill if the production policy store supports multiple simultaneous active policies. You may:
1. create active policies for a safe batch of applicable skills;
2. record all IDs/versions;
3. perform one genuine process restart;
4. prove every policy in the batch reloads and applies to its own different qualifying query;
5. rollback each policy and prove inactive state.

The report must still contain per-skill evidence. Shared restart evidence is acceptable only when each policy ID/version is individually tied to post-restart application.

## Phase 6 — Learning Loop safety/adversarial checks

Across the learning matrix prove:
- learned payloads contain generalized behavior only;
- no task IDs/member logins/sprint IDs/stored answers/correction prose/entity truths are memorized;
- unsupported user assertion cannot override contradictory REAL AS21 evidence;
- repeated identical correction does not create unbounded duplicate active policies;
- version/audit history remains traceable;
- malformed/invalid policy state fails safely where an existing non-destructive test path is available;
- rollback removes policy from active resolution;
- correction-state cache remains clean;
- learning recheck does not corrupt semantic conversation state;
- AS21 writes remain 0.

Do not manually corrupt production persistence merely to satisfy a safety row. If no safe existing test path exists, document the limitation and use relevant automated regression evidence.

## Phase 7 — automated regression suite

Run the complete relevant automated backend test suite from the exact tested HEAD.

Report:
- exact command(s);
- total collected;
- passed;
- failed;
- skipped/xfailed;
- exact failing test names;
- whether any failure is new, pre-existing, environment-related or product-related.

Arithmetic must reconcile. Do not report `N/N passed` if a failure also exists.

Any production-relevant regression failure prevents `FULLY_CERTIFIED` unless it is conclusively proven non-product/environment-only and all affected runtime rows are independently certified.

## Phase 8 — final complete certification matrix

Produce one row for **EVERY discovered callable production skill** with at least:

| Skill | Version | Functional canonical | Paraphrase | Edge/clarification | REAL source/oracle | Evidence | Learning applicability | Learning proof | Restart | Rollback | Final |

No discovered callable skill may be omitted.

Also include separate summary matrices for:
- catalog reconciliation;
- historical high-risk regressions;
- source integrity;
- Learning Loop safety;
- automated tests.

## Stop-on-defect rule

Assignment 095 is a certification exercise, not a repair campaign.

If one or more failures are found:
1. do not change production code;
2. continue non-destructive testing where doing so is safe and useful so failures can be grouped by shared boundary;
3. for every distinct defect cluster identify `FIRST_FAILING_BOUNDARY` with evidence;
4. do not speculate beyond evidence;
5. final verdict = `REGRESSION_DETECTED` unless environment failure prevents meaningful completion.

If environment failure makes the remaining matrix impossible, final verdict = `BLOCKED_BY_ENVIRONMENT` and clearly separate already-proven product failures from blocked rows.

## Acceptance criteria for FULLY_CERTIFIED

`FULLY_CERTIFIED` requires all of the following:

- 100% of dynamically discovered callable production skills represented in final matrix;
- zero functional RED;
- zero unresolved source/oracle mismatch;
- all applicable Learning Loop rows GREEN;
- all non-applicable learning rows justified by production policy evidence;
- persistence/generalization/restart/rollback proven for applicable learned policies;
- correction/clarification historical regressions remain GREEN;
- automated backend regression has no unresolved production-relevant failure;
- HTTP 500 = 0;
- fake/mock/frozen authoritative calls = 0;
- AS21 writes = 0;
- all required REAL AS21 rows grounded successfully.

A high pass percentage is not sufficient. One unresolved production regression means `REGRESSION_DETECTED`.

## Output

Create only QA artifacts under:

`po-agent-platform-v2/qa_reports/`

Required primary report:

`po-agent-platform-v2/qa_reports/TOTAL_BACKEND_CERTIFICATION_095.md`

If raw machine-readable matrices/traces are too large for the markdown report, you may additionally create files prefixed exactly:

`TOTAL_BACKEND_CERTIFICATION_095_`

under the same `qa_reports/` directory. Do not create or modify production files.

The primary report must include:
- exact commands;
- tested HEAD SHA and runtime provenance;
- dynamically discovered skill catalog;
- catalog reconciliation;
- per-skill functional matrix;
- historical high-risk regression evidence;
- REAL AS21/oracle evidence;
- source integrity counters;
- per-skill Learning Loop applicability/proof matrix;
- persistence/generalization/restart/rollback evidence;
- learning safety matrix;
- automated-test arithmetic;
- every `FIRST_FAILING_BOUNDARY` if failures exist;
- remaining known failures/blocked rows;
- final complete skill certification matrix;
- final verdict.

Commit and push ONLY the allowed QA artifacts. Verify the primary report exists in remote HEAD after push. Report final SHA and STOP.

Do not start any later assignment.