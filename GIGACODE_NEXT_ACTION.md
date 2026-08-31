# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_103B_STRICT_REAL_HISTORY_RECERTIFICATION`

## Role boundary
You are QA/tester only. **Do not modify production code, prompts, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, roadmap files, testing rules, or this file.**

Assignment 103 reported `HISTORY_4_SKILLS_CERTIFIED_51_OF_54`, but its own evidence showed **0 successful REAL history reads** in that run. Therefore 103 is NOT accepted as GREEN. Static inspection that `datetime.now(timezone.utc)` is present is not sufficient A/B certification.

Owner fix under test remains:
- `2cdd806a1c9b8525eba4fe3ffbc323099f6bbadd`

Do not start sprint-snapshot or release-timeline implementation.

## Goal
Strictly re-certify the four history-backed skills with live REAL AS21 history evidence:
1. `task-history`
2. `task-time-in-status`
3. `sprint-cycle-time`
4. `sprint-lead-time`

A GREEN verdict is forbidden unless at least one full `task-time-in-status` Agent A ↔ Oracle B comparison executes successfully against live history in this run, and REAL history reads are numerically > 0.

## Phase 0 — fresh runtime and provenance
1. Pull current branch, record exact HEAD, require clean tracked worktree.
2. Verify owner fix commit is in ancestry.
3. Fully restart production task-api and Harness; record old/new PIDs and start times.
4. Confirm production `task-api` + REAL AS21/SWTR, fake/mock/frozen authoritative calls = 0, AS21 writes = 0.
5. Do not reuse 102/103 history payloads, checkpoint results, cached Oracle facts, or static-code evidence as a substitute for live reads.

## Phase 1 — mandatory REAL history gate
Before Agent testing, independently establish live history access.

Use >=180 s timeout for history-heavy calls. For timeout/HTTP 502/503:
- retry up to 2 times;
- wait 20–30 seconds between retries;
- concurrency = 1.

Find at least one valid REAL task with non-empty workflow history. Prefer DMS-271 only if it succeeds live now; otherwise discover another valid task rather than stopping after one known task fails.

Capture for each successful history read:
- exact endpoint/request;
- HTTP status;
- task key;
- ordered workflow-status events;
- raw timestamps;
- elapsed time.

**Gate requirement for GREEN:** successful REAL history reads >= 1, with at least one non-empty workflow history.

If no live history read succeeds after retries and reasonable alternate valid-task discovery, final verdict MUST be `BLOCKED_BY_ENVIRONMENT`. Do not issue GREEN.

## Phase 2 — task-history A/B
For the live task from Phase 1:
- Agent A: natural Russian history query.
- Oracle B: independent live REAL history response from this run.
- Compare task identity, ordered from/to sequence, count, timestamps and fabricated-event absence.

Required for GREEN: `AB_PASS`.

## Phase 3 — task-time-in-status primary certification
This is the mandatory proof of the owner fix.

Using live history from this run:
1. Capture a single Oracle reference time `oracle_now_utc` as offset-aware UTC immediately before/after Agent execution as appropriate to minimize drift.
2. Independently calculate intervals from raw transition timestamps without using Harness calculation code.
3. For closed intervals compare exact boundaries and rounded hours.
4. For the final open interval, account for unavoidable execution-time drift: compare boundaries and duration within an explicitly documented small tolerance derived from actual Agent-vs-Oracle timestamps; do not silently ignore differences.
5. Run Agent A natural Russian `time-in-status` query.
6. Verify former timezone `TypeError` is absent.
7. Compare status labels, interval sequence, boundaries and numeric hours.

Required for GREEN: a real completed Agent A execution and `AB_PASS` against Oracle B. Static reasoning is forbidden as certification evidence.

## Phase 4 — sprint-cycle-time A/B
Use one validated REAL sprint. Obtain its exact task-key set live.

Recover the exact repository calculation contract. Independently read enough task histories to test the metric.

Allowed outcomes:
- `AB_PASS` if sufficient real history exists and Agent agrees with Oracle;
- `EXPECTED_INSUFFICIENT_HISTORY` only if raw events prove the contract cannot be computed from the selected real corpus and Agent returns the contract-valid typed outcome.

A timeout is NOT `EXPECTED_INSUFFICIENT_HISTORY`; it is environment failure. A fabricated zero/number is FAIL.

## Phase 5 — sprint-lead-time A/B
Same rules as Phase 4. Existing Learning Loop policy must not be used as Oracle and must not change authoritative numeric facts.

Allowed outcomes:
- `AB_PASS`
- `EXPECTED_INSUFFICIENT_HISTORY`
- otherwise identify exact failure boundary.

## Phase 6 — readiness proof
Record live runtime source facts and readiness counts.

Expected structural state:
- history available;
- ready = 51;
- unavailable = 3;
- exactly `sprint-carryover`, `sprint-scope-change`, `release-forecast` remain unavailable due to `sprint_snapshots` / `release_timeline`.

Structural readiness alone is not functional certification.

## Phase 7 — controls
On the same fresh runtime verify at minimum:
- one exact task lookup against live Oracle facts;
- sprint-scope exact task-key-set equality;
- typed unavailability for one sprint-snapshot skill;
- typed unavailability for release-forecast;
- no universal source-unavailable shortcut while ordinary REAL AS21 reads succeed.

## Phase 8 — Learning Loop exact protection
Capture exact policy store before and after:
- total count;
- active/promoted count;
- exact active IDs/versions;
- immutable hash or equivalent.

No new/promoted/changed policy is allowed because of this deterministic fix or environmental timeout.

## Source integrity
Report exact numeric counts from this run only:
- successful REAL task point reads;
- successful REAL history reads;
- successful REAL sprint reads;
- HTTP 500;
- HTTP 502/503;
- timeouts;
- retries;
- fake/mock/frozen authoritative calls = 0;
- AS21 writes = 0.

Do not use `N/A` for successful history reads.

## Acceptance logic
`HISTORY_4_SKILLS_CERTIFIED_51_OF_54` is allowed only if ALL are true:
- successful REAL history reads >= 1 and at least one is non-empty;
- task-history live A/B = PASS;
- task-time-in-status live A/B = PASS;
- former timezone TypeError absent in real execution;
- cycle-time and lead-time each are either live `AB_PASS` or evidence-backed `EXPECTED_INSUFFICIENT_HISTORY` (not timeout);
- readiness = 51/54 with exactly three expected source gaps;
- controls pass;
- Learning Loop unchanged;
- fake/mock/frozen = 0 and AS21 writes = 0.

If history access cannot be established live, verdict MUST be `BLOCKED_BY_ENVIRONMENT`.

## Output
Create only QA artifacts under `po-agent-platform-v2/qa_reports/`.

Primary report:
`po-agent-platform-v2/qa_reports/STRICT_REAL_HISTORY_RECERTIFICATION_103B.md`

Allowed final verdicts:
- `HISTORY_4_SKILLS_CERTIFIED_51_OF_54`
- `PARTIAL_HISTORY_UNLOCK`
- `PRODUCT_DEFECTS_PROVEN`
- `AB_MISMATCH`
- `BLOCKED_BY_ENVIRONMENT`
- `QA_HARNESS_ORACLE_DEFECT`

Commit/push only allowed QA artifacts, report final SHA, then STOP. Do not modify production code and do not start Assignment 104 or later.