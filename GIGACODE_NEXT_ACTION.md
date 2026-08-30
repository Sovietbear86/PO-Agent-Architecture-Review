# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_095B_PREFLIGHT_AND_MARATHON`

## Role boundary
You are QA/tester only. Do not modify production code, prompts, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, roadmap files, or this file. If a defect is found, prove FIRST_FAILING_BOUNDARY and report it; do not fix it.

## Goal
Do not launch another multi-hour run until the exact background environment proves end-to-end REAL SWTR access first.

Production mode: `task-api` + REAL read-only AS21(SWTR). One SWTR-backed invocation may normally take 40–60 seconds or more.

# Gate A — Production background preflight

1. Pull current branch and record HEAD, branch, `git status --short`.
2. Derive the exact production launch environment used by the working PO Agent/task-api: interpreter/venv, working directory, package root, `PO_AGENT_AS21_MODE=task-api`, task-api base URL, SWTR transport/config, model/runtime config and other required non-secret environment.
3. Confirm fake/mock/frozen authoritative modes are OFF and AS21 write authority is OFF.
4. Using that exact same environment intended for the marathon, execute three sequential end-to-end requests:
   - valid exact task lookup;
   - valid sprint-backed request;
   - valid team/release or another independent SWTR-backed capability.
5. Each request must use timeout >=120 sec, capture start/end/elapsed, reach PO Agent -> task-api -> REAL source, complete successfully, and record authoritative evidence.
6. If a request times out/502s, retry up to 2 times with 20–30 sec backoff and probe an independent capability before declaring broad outage.
7. Health endpoint alone is not enough.

**Do not start the 54-skill marathon unless all three preflight requests succeed in the exact same environment.**

If Gate A fails, produce narrow `BLOCKED_BY_ENVIRONMENT` evidence and STOP without launching the marathon.

# Gate B — Resumable background marathon

Start only after Gate A GREEN.

## Background execution
- Run detached/backgrounded so it survives IDE/chat closure.
- Durable stdout/stderr log under `po-agent-platform-v2/qa_reports/` with prefix `TOTAL_BACKEND_CERTIFICATION_095_`.
- Record PID, start timestamp, tested HEAD and non-secret environment fingerprint.
- Checkpoint after every completed skill.
- Checkpoint must store completed and pending skill IDs so the run can resume without restarting from zero.
- The marathon must use the SAME verified environment from Gate A.

## Timing
- Sequential execution preferred, concurrency=1.
- Maximum concurrency=2 only if source stability is proven.
- Normal SWTR latency: 40–60+ sec.
- Per request timeout >=120 sec.
- Heavy sprint/release/team/history requests may use up to 180 sec.
- Retry timeout/502 up to 2 additional attempts with 20–30 sec backoff.
- One slow skill must not terminate the run.
- Full run may take several hours.

## Full catalog scope
Dynamically enumerate the callable production skill catalog. Runtime discovery is authoritative; reconcile with historical 48 original + 6 reconciled.

For every discovered callable skill run:
1. canonical Russian query;
2. meaning-preserving paraphrase;
3. relevant edge/negative/clarification case where applicable;
4. REAL AS21/SWTR verification where source-backed.

For every request record start/end, elapsed, attempt, retries, resolved skill, semantic slots/args, capability/source evidence, expected vs actual and PASS/FAIL/BLOCKED.

For source-backed skills, plausible prose/HTTP200 is insufficient: use independent REAL source/oracle evidence where possible.

## Historical high-risk pack
Also rerun:
- exact task key: 2 valid + 1 nonexistent;
- sprint ID only;
- sprint + person;
- sprint + status;
- sprint + product/project where supported;
- person only;
- status only;
- person + product + status;
- second independent member;
- correction replaces old status and preserves unaffected slots;
- history/changelog/attachments where applicable;
- Sprint Intelligence exact key-set/metric checks;
- Team Workload exact key-set/metric checks.

## Source integrity
Track HTTP500, HTTP502 with endpoint/time mapping, timeout count, successful retries, fake/mock/frozen authoritative calls, AS21 writes and successful REAL reads.

Classify every timeout/502 as isolated, endpoint-specific, capability-specific or broad outage. One `/swtr-read/versions` timeout must never automatically block unrelated skills.

Whole-assignment `BLOCKED_BY_ENVIRONMENT` is allowed only after repeated independent evidence that meaningful completion is impossible despite retries/timeouts, while preserving all completed rows.

## Learning Loop matrix
For every discovered skill classify one:
- `APPLICABLE_AND_TESTED`
- `NOT_APPLICABLE_BY_POLICY`
- `BLOCKED`
- `FAILED`

For each applicable skill prove existing production loop:
negative/correction -> authoritative recheck -> generalized policy promotion -> persistent ID/version -> different query/entity -> genuine restart -> same policy reused -> rollback -> policy no longer applies.

Batch policies for shared restart when safe. Each policy still needs individual post-restart application evidence. Do not persist entity facts, task IDs, member logins, sprint IDs, stored answers or correction prose.

## Automated regression
Run complete relevant backend automated tests and report exact command plus reconciled totals: collected/passed/failed/skipped/xfailed and exact failures.

## Final matrix
One row for every discovered callable skill:
`Skill | Version | Canonical | Paraphrase | Edge | REAL source/oracle | Avg/Max latency | Retries | Evidence | Learning applicability | Learning proof | Restart | Rollback | Final`

## Verdicts
Allowed only:
- `FULLY_CERTIFIED`
- `REGRESSION_DETECTED`
- `BLOCKED_BY_ENVIRONMENT`

`FULLY_CERTIFIED` requires 100% required rows GREEN, zero unresolved source/oracle mismatch, all applicable Learning Loop rows GREEN, no unresolved production-relevant automated-test failures, HTTP500=0, fake authoritative calls=0 and AS21 writes=0.

If product defects appear, continue safe non-destructive testing and group by FIRST_FAILING_BOUNDARY. Do not modify production code.

## Output
Primary report:
`po-agent-platform-v2/qa_reports/TOTAL_BACKEND_CERTIFICATION_095.md`

Additional logs/checkpoints may be created only in the same directory with prefix `TOTAL_BACKEND_CERTIFICATION_095_`.

Primary report must include preflight evidence, exact background launch/PID, environment fingerprint, tested HEAD, discovered catalog, complete skill matrix, latency/retry statistics, checkpoint/resume behavior, historical regression pack, REAL AS21 evidence, source integrity classification, Learning Loop matrix, restart/rollback evidence, automated-test arithmetic, FIRST_FAILING_BOUNDARY items and final verdict.

After completion, commit/push only allowed QA artifacts, verify primary report exists in remote HEAD, report final SHA and STOP. Do not start later assignments.