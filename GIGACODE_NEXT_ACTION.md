# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_103_TIMEZONE_FIX_AB_CERTIFICATION`

## Role boundary
You are QA/tester only. **Do not modify production code, prompts, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, roadmap files, testing rules, or this file.**

Assignment 102 proved REAL task history wiring and found one owner-actionable product defect: `task-time-in-status` mixed timezone-aware SWTR timestamps with timezone-naive `datetime.now()`. The owner has applied the minimal fix in `po-agent-platform-v2/src/po_agent/harness/task_intelligence.py`: use `datetime.now(timezone.utc)`.

Owner fix commit under test:
- `2cdd806a1c9b8525eba4fe3ffbc323099f6bbadd`

This assignment is the mandatory post-change A/B certification. Do not start sprint-snapshot or release-timeline implementation.

## Goal
Certify the timezone fix and complete the four history-backed skills against REAL AS21:
1. `task-history`
2. `task-time-in-status`
3. `sprint-cycle-time`
4. `sprint-lead-time`

Target structural readiness remains `51/54`; the remaining three unavailable skills must be only `sprint-carryover`, `sprint-scope-change`, and `release-forecast` due to missing `sprint_snapshots` / `release_timeline`.

## Phase 0 — provenance and fresh runtime
1. Pull current branch; record exact HEAD and clean `git status --short`.
2. Verify owner fix commit is in ancestry.
3. Audit the owner diff: it must be limited to timezone-aware current time in `task_intelligence.py` plus this QA assignment activation. No unrelated production behavior may change.
4. Fully restart production task-api and Harness; record new PIDs/start times.
5. Confirm task-api + REAL AS21/SWTR, source healthy, fake/mock/frozen authoritative calls=0, AS21 writes=0.
6. Timeout >=120 s; history/sprint-heavy calls up to 180 s; retry timeout/502 up to 2 times with 20–30 s backoff.

## Phase 1 — REAL history preflight
Use at least two valid REAL tasks. At least one must have non-empty workflow history. Capture direct task facts and raw history events independently from Agent A. Reuse DMS-271 only if it is still valid; do not assume prior evidence remains current.

## Phase 2 — task-history regression A/B
Re-run natural Russian task-history query. Oracle B is a direct REAL history read. Compare task key, ordered transition sequence, transition count and timestamps. Require `AB_PASS`.

## Phase 3 — task-time-in-status fix A/B
This is the primary fix certification.

For a task with meaningful history:
- Agent A: natural Russian time-in-status query.
- Oracle B: independently calculate every interval from raw REAL transition timestamps, using an offset-aware current UTC timestamp for the final open interval where contract requires it.
- Compare status labels, interval boundaries and rounded hours according to repository contract.
- Record whether the former `TypeError` is absent.

Do not accept only HTTP 200/COMPLETED. Business values must agree.

## Phase 4 — sprint-cycle-time A/B
Use a validated REAL sprint with enough historical events if available.
1. Independently obtain exact sprint task-key set from AS21.
2. Read REAL histories for the tasks used in the metric.
3. Recover exact repository formula from code/contracts.
4. Independently calculate expected per-task cycle times and aggregate.
5. Run Agent A and compare normalized metric facts.

If source data genuinely cannot satisfy the formula, require the contract-valid typed insufficient-history result and prove why from raw events. A runtime exception or fabricated zero is FAIL.

## Phase 5 — sprint-lead-time A/B
Repeat the same independent procedure for lead time. Verify the existing promoted Learning Loop policy does not alter authoritative numeric facts or conceal a deterministic/source failure.

## Phase 6 — readiness and remaining gaps
Record exact source facts and readiness. Expected structural state:
- `history` available;
- ready = 51, unavailable = 3;
- remaining unavailable exactly: `sprint-carryover`, `sprint-scope-change`, `release-forecast`;
- no history-backed skill unavailable due to source guard.

Do not claim `54/54`: source readiness and functional certification are distinct, and the three snapshot/timeline skills remain out of scope.

## Phase 7 — regression controls
At minimum A/B or authoritative checks for:
- exact task lookup;
- sprint scope exact task-key-set equality;
- one existing non-history skill from the 51-ready set;
- typed unavailability for one `sprint_snapshots` skill;
- typed unavailability for `release-forecast` due to `release_timeline`.

## Phase 8 — Learning Loop protection
Capture policy store before/after with exact active/promoted IDs and state. No new policy may be created/promoted/changed by this deterministic timezone fix. Existing policy must not be used as an Oracle.

## FIRST_FAILING_BOUNDARY
For every failed/non-expected row identify the earliest proven boundary among semantic interpretation, skill resolution, entity grounding, capability argument building/routing, source contract/data, deterministic calculation, response status mapping, learning policy application, owner regression, or QA Oracle defect.

## Output
Create only QA artifacts under `po-agent-platform-v2/qa_reports/`.

Primary report:
`po-agent-platform-v2/qa_reports/TIMEZONE_FIX_POST_CHANGE_AB_103.md`

Allowed final verdicts:
- `HISTORY_4_SKILLS_CERTIFIED_51_OF_54`
- `PARTIAL_HISTORY_UNLOCK`
- `PRODUCT_DEFECTS_PROVEN`
- `OWNER_CHANGE_REGRESSION`
- `AB_MISMATCH`
- `BLOCKED_BY_ENVIRONMENT`

GREEN requires task-history + task-time-in-status A/B PASS, no timezone exception, cycle/lead-time correct against independent REAL Oracle where source permits (or contract-valid proven insufficient-history), structural readiness 51/54 with exactly three expected source gaps, regression controls pass, Learning Loop unchanged, fake/mock/frozen=0, AS21 writes=0.

Commit/push only allowed QA artifacts, report final SHA, then STOP.