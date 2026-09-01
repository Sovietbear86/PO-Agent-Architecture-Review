# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_110B_STRICT_FULL_MATRIX_EXECUTION`

## Why Assignment 110 is NOT accepted
Assignment 110 finished far too quickly for the requested exhaustive matrix and its report does not contain the mandatory evidence required by Assignment 110. The owner explicitly rejects 110 as a full certification.

The 110 report proves useful defects, but it is a forensic sample, not a complete marathon. It reports only a handful of live Agent rows, only DMS/OLP source coverage, only four latency observations, and no explicit 54-skill execution matrix, no every-member matrix, no full per-space status matrix, no WMB/STS/CRPV retest/retry proof, no full NONE-sprint matrix, and no complete Learning Loop lifecycle execution.

This assignment is a strict re-run and execution audit. Do not reinterpret or summarize away required rows.

## Role boundary
You are QA/test executor only. Do not modify production code, frontend code, prompts, tests, fixtures, learning implementation, runtime behavior, credentials, AS21/SWTR data, roadmap, QA rules, or this file. You may use supported feedback/learning operations only as product behavior under test. AS21 writes = 0.

Frontend remains frozen and OUT OF SCOPE.

## Core acceptance rule
A final report is invalid unless it contains direct execution evidence for every mandatory row below. Static code inspection, endpoint existence, HTTP 200, skill catalog enumeration, or historical reports do not substitute for execution.

## Phase 0 — provenance + execution clock
1. Pull branch, record exact HEAD and clean worktree.
2. Restart MCP-SWTR, Task API, Harness from exact HEAD.
3. Record test start timestamp and final end timestamp.
4. Maintain a monotonically increasing `executed_case_id` for every Agent A request and every independent Oracle B read.
5. Maintain counters:
   - Agent A requests total
   - Oracle B source reads total
   - retries/timeouts/502/503
   - REAL AS21 reads
   - fake/mock/frozen reads
   - AS21 writes
6. Checkpoint every 10–15 executed rows.

A run claiming exhaustive certification with implausibly low executed-case/source-read counts must be classified `QA_EXECUTION_INCOMPLETE`, not GREEN.

## Phase 1 — REAL source accessibility for all required spaces
Mandatory spaces: `WMB`, `STS`, `OLP`, `DMS`, `CRPV`.

For EACH space independently:
1. Perform direct Oracle B discovery/read using available MCP-SWTR/task-api paths.
2. If first path fails, inspect available read tools/contracts and try the correct source route for that space.
3. On timeout/502/503: up to 2 retries with 20–30 s backoff, then revalidate/restart source chain and retest once.
4. Do NOT conclude `source unavailable` merely because one chosen endpoint did not support the space.
5. If after contract discovery and retries the space is truly unavailable, provide raw tool/endpoint evidence and classify only that surface as `SOURCE_CAPABILITY_UNAVAILABLE_BY_DESIGN` or `ENVIRONMENT_BLOCKED` as appropriate.

For every accessible space capture fresh task corpus, statuses, assignees, sprints including NONE/null, releases, attachments and representative rich tasks.

## Phase 2 — all real statuses in every accessible space
For every distinct `(space, raw_status)` discovered live:
- Oracle B exact task-key set;
- Agent A canonical Russian query;
- Agent A paraphrase;
- exact set comparison;
- first encounter/fresh session/cold restart behavior for at least every custom or previously unknown status.

Source-valid status must never be falsely exposed as UNKNOWN. If the runtime discovers/learns a status, prove whether this is persisted or rediscovered after restart.

## Phase 3 — all team members + competencies
Discover the actual runtime team data source, not an example file.

For EVERY configured member:
- member-only task query vs Oracle;
- member + valid status;
- member + sprint when applicable;
- workload/WIP/blocked where applicable;
- role/profile/competency retrieval;
- competency match;
- assignee recommendation using both competencies and workload.

Report one explicit member row group per configured person. No sampling three members and calling the matrix complete.

## Phase 4 — sprint + NONE matrix
Use live approved sprints where valid:
- `DMS-SPRNT-1`
- `DMS-SPRNT-2`
- `OLP-SPRNT-5`
- at least one additional live OLP/DMS sprint if available.

Also explicitly test tasks with `sprint = NONE/null/empty` in WMB/CRPV or any other live space where Oracle proves such data.

For each sprint execute all applicable sprint skills and compare deterministic facts to Oracle. Missing historical source capability must return a typed truthful limitation.

## Phase 5 — mandatory 54-skill execution matrix
Read current `SKILL_CATALOG` and enumerate every implemented skill.

For EVERY implemented skill, execute and record at least:
1. canonical natural Russian request;
2. natural Russian paraphrase;
3. negative/missing-slot/unavailable case where meaningful;
4. Oracle B comparison for deterministic/source-backed facts;
5. resolved skill/version;
6. trace/evidence IDs;
7. elapsed time;
8. final verdict.

The final report MUST contain one explicit row per skill. A summary saying `51/54 ready` is not sufficient.

For LLM-heavy skills, compare grounded inputs/evidence/invariants rather than prose.

## Phase 6 — combinatorial filtering
Build a bounded live matrix across:
`space × member × status × sprint/NONE × release`.

Include both real non-empty and real empty combinations per applicable dimension. Compare exact task-key sets. Mandatory defect retests include:
- `Задачи Гаранина`
- one second DMS member
- one OLP member
- `In progress` in `DMS-SPRNT-2`
- another real DMS status
- member + status
- member + sprint
- member + status + sprint
- NONE-sprint query where source supports it.

Trace FIRST_FAILING_BOUNDARY beyond capability arguments when args are correct.

## Phase 7 — dialogue/context/language
Run real multi-turn cases across at least DMS and OLP:
- member -> add status;
- member+sprint -> replace status;
- remove status constraint;
- switch DMS -> OLP;
- clarification option selection;
- bare sprint;
- bare surname;
- correction after a wrong answer;
- `только открытые` continuation.

All Russian turns must receive Russian user-facing prose. No invented source IDs.

## Phase 8 — deep Learning Loop, not just endpoint probing
Do NOT classify learning merely by whether GET endpoints exist.

First inspect the executable runtime integration and actual persistence/state artifacts. Then use the normal product feedback flow on at least two proven wrong-answer cases.

For each case prove whether the chain actually occurs:
`feedback -> persisted improvement text -> pattern mining -> candidate -> eval case -> shadow/offline eval -> regression gate -> approval/promotion state -> applied policy -> same-case retest -> generalization -> fresh session -> cold restart -> rollback -> cleanup`.

If there is no public API for a lifecycle step, use supported runtime/product state/artifact evidence if that is how the implementation is designed. Missing GET endpoints alone are not enough to conclude that learning is broken.

If the Agent asks `Что бы вы хотели улучшить?` and after the user's concrete response there is no persisted artifact or lifecycle transition, classify `LEARNING_FEEDBACK_NOOP` with first failing boundary.

If promotion legally requires owner approval, stop at the real approval gate and prove the candidate/eval/state exist. Do not bypass governance.

## Phase 9 — Harness capability reachability
For each capability from the dialogue/learning architecture contract, prove actual production reachability or prove a real wiring gap:
- semantic interpreter
- grounding
- clarification persistence/resume
- correction
- satisfaction feedback
- trace/session/skill/version linkage
- observation/mining
- candidate generation
- eval generation
- shadow eval
- promotion gate
- policy application
- persistence
- rollback/version lineage.

Code existence is not PASS. Runtime reachability/evidence is required.

## Phase 10 — latency marathon
The prior 110 report had only one timing sample per a few skills, so p50/p95 were not actually measured.

For each of these request classes run at least 5 repetitions (cold/warm as appropriate):
- task lookup
- member-only
- status-only
- sprint scope
- multi-filter
- team skill
- one LLM-heavy skill.

Report real p50/p95/max and decompose total into semantic LLM, planning/ranking, grounding, AS21 I/O, hydration, deterministic execution, response LLM, retry/backoff.

Flag >10 s normal queries and identify dominant cause. Record source call count per request.

## Phase 11 — QA methodology self-audit
Explicitly compare Assignment 110 instructions vs what Assignment 110 actually executed. List every skipped/under-executed requirement and explain why the previous report finished quickly.

Mandatory classification if coverage was incomplete:
`PREVIOUS_110_QA_EXECUTION_INCOMPLETE`.

Do not defend the earlier report by treating discovered defects as permission to skip the rest of the requested matrix. This assignment exists specifically because the owner requested a full inventory before fixes.

## Minimum completion evidence
The final 110B report must include:
- start/end timestamps + wall-clock duration;
- total Agent A request count;
- total Oracle B read count;
- all five space discovery outcomes;
- full per-status matrix;
- full per-member matrix;
- explicit one-row-per-skill matrix for every implemented skill;
- sprint/NONE matrix;
- combinatorial filter matrix;
- dialogue matrix;
- Learning Loop lifecycle evidence;
- Harness capability reachability matrix;
- real latency repetitions and p50/p95/max;
- retries/source integrity counters;
- complete skipped/not-executable rows with evidence.

A fast stop after finding the first two defects is forbidden. Continue the full inventory unless the entire source environment becomes genuinely unavailable after the retry/restart protocol.

## Output
Primary report:
`po-agent-platform-v2/qa_reports/BACKEND_FULL_MATRIX_STRICT_EXECUTION_110B.md`

Supporting/checkpoint prefix:
`BACKEND_FULL_MATRIX_STRICT_EXECUTION_110B_`

Allowed final verdicts:
- `BACKEND_PRODUCT_DEFECTS_PROVEN_FULL_MATRIX_COMPLETE`
- `MIXED_PRODUCT_SOURCE_LEARNING_DEFECTS_FULL_MATRIX_COMPLETE`
- `BACKEND_AND_LEARNING_GREEN_FULL_MATRIX_CERTIFIED`
- `BLOCKED_BY_ENVIRONMENT`
- `QA_EXECUTION_INCOMPLETE`

No GREEN and no `FULL_MATRIX_COMPLETE` verdict unless all mandatory coverage evidence exists.

Commit/push only QA artifacts under `po-agent-platform-v2/qa_reports/`, report final SHA, executed-case counts and wall-clock duration, then STOP.