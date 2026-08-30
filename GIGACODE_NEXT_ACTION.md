# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_095D_CONSISTENCY_DEFECT_PROOF`

## Role boundary — mandatory
You are QA/tester only. **Do not modify production code, prompts, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, roadmap files, testing rules, or this file.**

Do not start Assignment 096. Assignment 096 is paused until 095D is complete.

## Why 095D exists

Assignment 095C produced an internally contradictory certification result:
- `sprint-carryover` and `sprint-scope-change` were reported `FAILED (PRODUCT_DEFECT_PROVEN)`;
- `release-forecast` was reported `FAILED (PRODUCT_DEFECT_PROVEN)`;
- FIRST_FAILING_BOUNDARY was reported as `DETERMINISTIC_METRIC_CALCULATION` for these failures;
- but the final verdict was `NO_PRODUCT_DEFECTS_AFTER_VALID_RETEST`.

Those statements cannot all be true simultaneously. 095D is a small evidence-only consistency gate. Its purpose is to determine whether these three rows are genuinely proven product defects or whether 095C misclassified them.

Do not rerun the full 54-skill marathon. Do not repair anything.

## Scope — exactly three skills
1. `sprint-carryover`
2. `sprint-scope-change`
3. `release-forecast`

## Phase 0 — provenance
1. Pull current branch and record exact HEAD.
2. Record `git status --short`; production files must remain clean.
3. Use production `task-api` + REAL AS21(SWTR).
4. fake/mock/frozen authoritative calls = 0.
5. AS21 writes = 0.
6. Revalidate every sprint/release/entity used against REAL AS21.

## Phase 1 — audit the 095C claims

For each of the three skills, quote/capture from the 095C raw evidence and report:
- exact natural-language query;
- resolved skill;
- grounded slots;
- capability arguments;
- source evidence IDs/requests;
- source response summary;
- Agent result/status;
- why 095C labelled it `PRODUCT_DEFECT_PROVEN`;
- why 095C nevertheless emitted `NO_PRODUCT_DEFECTS_AFTER_VALID_RETEST`.

Identify the exact report/classification logic or reasoning step responsible for the contradictory final verdict. Do not modify it.

## Phase 2 — independent A/B defect proof

For each of the three skills run one clean contract-valid A/B test.

### A — Agent under test
Use a realistic Russian query with a currently valid REAL sprint/release and capture:
- query/session_id;
- semantic frame and grounded slots;
- resolved skill/version;
- capability arguments;
- source calls/evidence IDs;
- final status/value/business facts.

### B — independent Oracle
Query REAL AS21 independently of the Harness answer and independently derive the expected source facts/calculation inputs. Do not use the same Harness deterministic metric implementation as the Oracle.

For each row explicitly answer:
1. Are all source facts required by the metric available?
2. If yes, what is the independently expected value/result and how was it calculated?
3. If no, which exact source field/history/snapshot is unavailable?
4. Does Agent A match Oracle B?

Allowed row dispositions:
- `PRODUCT_DEFECT_PROVEN`
- `SOURCE_DATA_OR_CAPABILITY_UNAVAILABLE`
- `EXPECTED_UNAVAILABLE_OR_CLARIFICATION`
- `AB_PASS`
- `ENVIRONMENT_BLOCKED`

A product defect is proven only if sufficient authoritative source facts exist and the product first diverges from the independently derived expected result, or if the product maps a known source-unavailable condition to an incorrect FAILED behavior contrary to its explicit contract.

## Phase 3 — FIRST_FAILING_BOUNDARY proof

For every row still classified `PRODUCT_DEFECT_PROVEN`, show the exact earliest divergence through:
`query -> semantic -> skill -> grounding -> capability args -> REAL source -> source facts -> deterministic calculation -> response/status`.

If boundary is `DETERMINISTIC_METRIC_CALCULATION`, provide:
- exact calculation inputs;
- independent expected calculation/result;
- actual calculation/result;
- exact evidence proving the difference.

Do not merely repeat the label from 095C.

## Phase 4 — certification consistency

Produce a three-row truth table:

| Skill | 095C classification | 095D A/B disposition | FIRST_FAILING_BOUNDARY | Product fix required? |

Then issue a logically consistent final verdict.

Allowed final verdicts only:
- `PRODUCT_DEFECTS_PROVEN`
- `NO_PRODUCT_DEFECTS_AFTER_AB_PROOF`
- `MIXED_PRODUCT_AND_SOURCE_LIMITATIONS`
- `BLOCKED_BY_ENVIRONMENT`

If at least one row remains `PRODUCT_DEFECT_PROVEN`, final verdict MUST NOT be `NO_PRODUCT_DEFECTS_AFTER_AB_PROOF`.

## Source integrity
Record:
- HTTP 500 count;
- HTTP 502 count/endpoints;
- timeout/retry count;
- successful REAL AS21 reads;
- fake/mock/frozen authoritative calls = 0;
- AS21 writes = 0.

Use >=120 s request timeout; 40–60+ s SWTR latency is normal. Retry timeout/502 up to 2 times before environment classification.

## Output
Create only QA artifacts under `po-agent-platform-v2/qa_reports/`.

Primary report:
`po-agent-platform-v2/qa_reports/CERTIFICATION_CONSISTENCY_DEFECT_PROOF_095D.md`

Optional evidence artifacts must use prefix:
`CERTIFICATION_CONSISTENCY_DEFECT_PROOF_095D_`

Report must include exact commands, tested HEAD, A/B evidence for all three skills, FIRST_FAILING_BOUNDARY evidence, contradiction root cause, source-integrity counters, truth table, exact owner-fix candidates if proven, and final verdict.

Commit and push only allowed QA artifacts. Verify primary report exists in remote HEAD, report final SHA and STOP.

**Do not start Assignment 096 or any later assignment.**