# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_095_BACKGROUND`

## Role boundary
You are QA/tester only. Do not modify production code, prompts, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, roadmap files, or this file. If a defect is found, prove FIRST_FAILING_BOUNDARY and report it; do not fix it.

## Assignment 095 — long background full-backend certification

The previous 095 run classified 53/54 skills as environment-blocked too early. Treat REAL SWTR as a slow dependency: **one skill invocation may normally require 40–60 seconds or more**.

### Mandatory execution model
- Run the complete 54-skill certification as a **long-lived background process**, not as a short interactive run.
- Sequential execution is preferred; concurrency must be `1`, maximum `2` only when safe.
- Per individual SWTR-backed request timeout: **at least 120 seconds**.
- Heavy sprint/release/team/history requests: allow **up to 180 seconds**.
- On timeout, retry the same request up to **2 additional times** before marking that individual row BLOCKED.
- Pause briefly between retries.
- A 40–60 second response is normal latency, not failure.
- Do not infer broad SWTR outage from one `/swtr-read/versions` timeout if other source paths still work.
- Do not convert one timeout into 53 blocked skills without independent evidence.
- The full run may take **several hours**. Completion is more important than speed.

### Background resilience
Start the runner detached/backgrounded with stdout/stderr written to durable QA logs under:
`po-agent-platform-v2/qa_reports/`
using prefix:
`TOTAL_BACKEND_CERTIFICATION_095_`

Record exact command, PID and start time. The runner must checkpoint after every completed skill so it can resume from the last completed row if IDE/chat context closes or the runner is interrupted.

Do not require the GigaCode conversation to remain open for the test to continue.

## Scope
Dynamically enumerate the callable production skill catalog from the running registry. Runtime discovery is authoritative; reconcile it with the historical 48 original + 6 reconciled inventory.

For **every discovered callable skill** run at minimum:
1. canonical Russian query;
2. meaning-preserving paraphrase;
3. relevant edge/negative/clarification case where applicable;
4. REAL AS21/SWTR verification where source-backed.

For every request record start/end time, elapsed seconds, attempt number, timeout/retry count, resolved skill, semantic slots/arguments, capability/source evidence, expected vs actual and PASS/FAIL/BLOCKED.

For source-backed skills, HTTP 200 or plausible prose is not sufficient. Validate against an independent REAL AS21 oracle/read path wherever possible.

Checkpoint results after every skill.

## Mandatory historical regression pack
Also rerun:
- exact task-key lookup: at least two valid IDs + one nonexistent ID;
- sprint ID only;
- sprint + person;
- sprint + status;
- sprint + product/project where supported;
- person-only;
- status-only;
- person + product + status;
- second independent member;
- correction: new status replaces old and unaffected previous slots survive;
- history/changelog/attachments source paths where applicable;
- Sprint Intelligence deterministic key-set/metric checks;
- Team Workload deterministic key-set/metric checks.

Apply the same long timeout/retry policy.

## Source integrity
Track:
- HTTP 500 count;
- HTTP 502 count with endpoint/time mapping;
- timeout count;
- successful retry-after-timeout count;
- fake/mock/frozen authoritative calls = 0;
- AS21 writes = 0;
- successful REAL AS21 reads.

Classify each timeout/502 as isolated, endpoint-specific, capability-specific, or confirmed broad outage. `BLOCKED_BY_ENVIRONMENT` for the whole assignment is allowed only after repeated independent evidence that the environment prevents meaningful completion despite the long timeout/retry policy.

## Learning Loop matrix
For every discovered skill classify one:
- `APPLICABLE_AND_TESTED`
- `NOT_APPLICABLE_BY_POLICY`
- `BLOCKED`
- `FAILED`

`NOT_APPLICABLE_BY_POLICY` requires concrete production-policy/catalog evidence.

For each applicable skill prove the existing production Learning Loop:
negative/correction -> authoritative recheck -> generalized policy promotion -> persistent policy ID/version -> different query/entity -> genuine process restart -> same policy reused -> rollback -> policy no longer applies.

Batch policies before a shared restart where safely supported. Each policy ID/version must still have individual post-restart application evidence. Never persist entity facts, task IDs, member logins, sprint IDs, stored answers or correction prose.

## Automated regression
Run the complete relevant backend automated test suite. Report exact command and reconciled totals: collected/passed/failed/skipped/xfailed and exact failures.

## Final matrix
Produce one row for EVERY discovered callable skill with at least:
`Skill | Version | Canonical | Paraphrase | Edge | REAL source/oracle | Avg/Max latency | Retries | Evidence | Learning applicability | Learning proof | Restart | Rollback | Final`

Do not omit blocked rows.

## Verdict rules
Allowed final verdicts only:
- `FULLY_CERTIFIED`
- `REGRESSION_DETECTED`
- `BLOCKED_BY_ENVIRONMENT`

`FULLY_CERTIFIED` requires 100% required rows GREEN, zero unresolved source/oracle mismatch, all applicable Learning Loop rows GREEN, no unresolved production-relevant automated-test failures, HTTP500=0, fake authoritative calls=0, AS21 writes=0.

If product defects appear, continue safe non-destructive testing and group them by FIRST_FAILING_BOUNDARY. Do not modify production code.

## Output
Primary report:
`po-agent-platform-v2/qa_reports/TOTAL_BACKEND_CERTIFICATION_095.md`

Additional logs/checkpoints may be created only under the same `qa_reports/` directory with prefix:
`TOTAL_BACKEND_CERTIFICATION_095_`

Report must include exact background command/PID, tested HEAD, discovered catalog, complete per-skill matrix, latency/retry statistics, historical regression pack, REAL AS21 evidence, source integrity, Learning Loop matrix, restart/rollback evidence, automated-test arithmetic, FIRST_FAILING_BOUNDARY items and final verdict.

After the long background run completes, commit and push only allowed QA artifacts, verify the primary report exists in remote HEAD, report final SHA and STOP. Do not start any later assignment.