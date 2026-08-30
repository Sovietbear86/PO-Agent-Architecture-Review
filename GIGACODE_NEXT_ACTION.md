# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_100_REAL_AS21_EVIDENCE_GATE`

## Role boundary
QA/tester only. Do not modify production code, prompts, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, roadmap files, testing rules, or this file.

## Why Assignment 100 exists

Assignment 099 cannot be accepted as GREEN because its own report is internally inconsistent:
- target cases are classified as correct source-limited behavior;
- both controls (`sprint-scope`, exact `task-lookup`) FAILED because AS21 was unavailable;
- successful REAL AS21 reads are reported as `N/A`;
- nevertheless the final verdict is `BACKEND_CERTIFICATION_CLOSED_GREEN`.

A GREEN verdict is impossible without positive proof that REAL AS21/SWTR was reachable in the same fresh runtime and that the target sprint/task were independently read from the source. Assignment 100 is an evidence gate, not a code-fix task.

Do not use static code inspection, source-fact declarations, cached/checkpoint data, prior reports, or Harness fail-closed responses as proof that AS21 was actually queried successfully.

## Scope
Only prove live source grounding and re-run the minimum controls/targets necessary to validate 099.

## Phase 0 — fresh runtime and provenance
1. Pull current branch; record exact HEAD and clean `git status --short`.
2. Fully restart production task-api and Harness; record old/new PIDs and process start times.
3. Confirm mode is production `task-api` + REAL AS21/SWTR.
4. fake/mock/frozen authoritative calls = 0; AS21 writes = 0.
5. Do not reuse 098/099 checkpoints or cached Oracle results.

## Phase 1 — mandatory direct REAL AS21 preflight

Before calling the Agent, independently query REAL task-api/SWTR and capture raw evidence for ALL of the following:

A. Exact task point-read
- Use one currently valid task key discovered/validated from REAL AS21.
- Record endpoint/request, HTTP status, task key, title/status/assignee summary, elapsed time.

B. Sprint scope read
- Use one currently valid sprint, preferably `DMS-SPRNT-2` only if independently validated now.
- Record endpoint/request, HTTP status, exact task-key set, count, elapsed time.

C. One second independent REAL read
- Either another task point-read or a team/source-backed read.
- Record exact source facts.

Preflight PASS requires at least 3 successful REAL reads in this run, including task point-read and sprint scope.

If any mandatory read cannot succeed after timeout >=120 s and up to 2 retries for timeout/502 with 20–30 s backoff, STOP with `BLOCKED_BY_ENVIRONMENT`. Do not continue and do not issue GREEN.

HTTP 404 for a guessed entity is not environment failure; choose a valid entity from REAL discovery and retry the semantic test with that valid entity.

## Phase 2 — prove snapshot limitation independently

Only after Phase 1 PASS, independently test the historical sprint baseline contract for the SAME validated sprint:
- sprint metadata/start-time endpoint if present;
- sprint snapshot/commitment-baseline endpoint if present;
- membership/change-history endpoint if present.

Capture exact requests/statuses.

Conclude `SOURCE_CAPABILITY_UNAVAILABLE` only if:
1. current sprint scope was successfully read from REAL AS21 in Phase 1, AND
2. authoritative sprint-start baseline/history is demonstrably absent/unavailable through the current production source contract.

Do not infer source unavailability merely because Harness says `missing_source_fact`.

## Phase 3 — Agent A / Oracle B

Using the SAME validated sprint and fresh runtime, run:
1. scope-change (hyphen form)
2. scope change (space form)
3. Russian scope-change paraphrase
4. carryover
5. plain sprint-scope control
6. exact task-lookup control using the Phase-1 validated task

For each capture:
- session/query;
- resolved intent/skill where execution reaches semantic layer;
- status/warnings/data/answer;
- elapsed;
- source calls/evidence if exposed.

Oracle B comparisons:
- `sprint-scope`: Agent exact task-key set MUST equal Phase-1 Oracle task-key set.
- `task-lookup`: Agent task key/title/status core facts MUST match Phase-1 Oracle point-read.
- `scope-change`/`carryover`: if Phase 2 proved missing historical baseline, Agent must fail closed with typed source limitation and no invented metric.

Any disagreement in business facts is `AB_MISMATCH` regardless of HTTP 200 or prose.

## Phase 4 — no-source behavior test

The purpose of fail-closed logic is not to replace ordinary AS21 access.
Explicitly prove that normal source-backed skills still use AS21 when required.

Required assertions:
- `sprint-scope` causes/uses successful REAL AS21 reads;
- exact `task-lookup` causes/uses successful REAL AS21 reads;
- source guard for `scope-change` does not prevent unrelated normal reads;
- no universal early-return path is falsely treating healthy AS21 as unavailable.

If controls return source-unavailable while direct Oracle reads succeed, classify `PRODUCT_DEFECT_PROVEN` at the earliest boundary.

## Phase 5 — Learning Loop exact state

Capture before and after:
- total policy count;
- active/promoted count;
- exact active policy IDs/versions;
- immutable file hash/snapshot.

No N/A/Unknown allowed.
Target source-limited cases must not create/promote/change policies.

## Phase 6 — resolve 099

Allowed 099 resolution:
- `099_GREEN_CONFIRMED_WITH_REAL_AS21`
- `099_FALSE_GREEN_ENVIRONMENT_NOT_PROVEN`
- `PRODUCT_DEFECT_PROVEN`
- `BLOCKED_BY_ENVIRONMENT`

Do not call 099 GREEN merely because fail-closed responses are well-typed.

## Source integrity
Report exact counts from this run only:
- successful REAL AS21 reads;
- HTTP 500;
- HTTP 502;
- HTTP 404 by endpoint;
- timeouts/retries;
- fake/mock/frozen calls = 0;
- AS21 writes = 0.

Successful REAL AS21 reads MUST be a numeric value >=3 for GREEN.

## Output
Primary report:
`po-agent-platform-v2/qa_reports/REAL_AS21_EVIDENCE_GATE_100.md`

Optional raw evidence prefix:
`REAL_AS21_EVIDENCE_GATE_100_`

Allowed final verdicts:
- `BACKEND_CERTIFICATION_CONFIRMED_GREEN`
- `099_FALSE_GREEN_ENVIRONMENT_NOT_PROVEN`
- `PRODUCT_DEFECTS_PROVEN`
- `AB_MISMATCH`
- `BLOCKED_BY_ENVIRONMENT`

`BACKEND_CERTIFICATION_CONFIRMED_GREEN` requires ALL of:
- fresh post-fix runtime;
- >=3 successful direct REAL AS21 reads;
- successful task point-read control;
- successful sprint-scope control with exact task-key-set equality;
- independently proven missing historical baseline for the same sprint;
- correct fail-closed scope-change/carryover behavior;
- unchanged Learning Loop state;
- fake/mock/frozen=0, writes=0.

Commit/push only allowed QA artifacts, report final SHA, then STOP. Do not modify production code and do not start later assignments.