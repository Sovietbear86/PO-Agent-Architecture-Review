# GigaCode — Current Action

## Status
ACTIVE_QA_ASSIGNMENT_221_FULL_V4_54_ABC_CERTIFICATION

## Role lock
GigaCode is QA/adversarial tester + service operator only.

Do NOT modify production/frontend/plugin/test/config/architecture code.
Do NOT implement fixes.
Do NOT start Learning Reviewer work.
Commit/push only QA reports and resumable matrix artifacts.

If a blocking RED is proven, stop at that first failing boundary and preserve all completed matrix rows so the next re-gate resumes rather than restarts.

## Frozen baseline
A220 = GREEN.

Canonical checkpoint:
`checkpoint/v4-canonical54-green-a220`

Important:
owner checkpoint refs are Git **branches**, not tags.
Do not use `git tag -l checkpoint/*` as proof they are absent.
Validate via branch/ref lookup and record exact SHA.

Expected baseline:
- live registry = 68 skills / 13 plugins / 0 duplicates;
- canonical requirements = 54/54 covered;
- canonical missing list = [];
- no dummy plugin in production discovery;
- release.forecast live source maturity = SOURCE_CONDITIONAL / release_linkage_unpopulated.

## Authoritative certification inventory
Use BOTH repository sources:
1. `PO_AGENT_48_SKILL_MATRIX.md` — original requirements 1..48;
2. the six reconciled additions preserved in that document:
   - task-search-product
   - release-forecast
   - po-daily-brief
   - po-status-report
   - po-reminder-draft
   - po-local-task-draft

Build a machine-readable certification manifest before execution.

For each of the exact 54 canonical requirements record:
- requirement number/name;
- live V4 skill id;
- plugin id;
- source class: SOURCE_READY / SOURCE_PARTIAL / SOURCE_CONDITIONAL / SOURCE_FREE;
- representative NL query;
- required context dimensions;
- A result;
- B result;
- C result;
- exact status;
- evidence/task keys/counts where applicable;
- source routes called;
- local-store reads;
- mutation count;
- latency;
- notes.

Do not count the 14 legitimate extra V4 skills as canonical rows.
Do test critical extras separately as retained architecture regression.

## Global execution rules
1. Fresh or explicitly reset session per independent matrix case unless continuation is the thing under test.
2. Concurrency: max 2 Agent calls, max 4 bounded source reads unless an existing certified adapter internally uses a smaller/bounded semaphore.
3. Never blast all 54 in parallel.
4. Persist a checkpoint artifact after every 9 canonical rows.
5. On timeout:
   - retry once in a fresh session;
   - classify timeout separately;
   - never silently skip the row.
6. A SOURCE_CONDITIONAL row is GREEN only when Oracle B independently proves the required live source fact is unavailable/insufficient and Agent A fails closed without fabrication.
7. REAL_EMPTY is GREEN only when Oracle B proves an authoritative empty set.
8. Every collection requires exact set/key parity when the source exposes identities.
9. Browser C must exercise the real V4 UI path, not a backend-only simulation.
10. Zero production code changes.

## Phase 0 — baseline / architecture integrity
- resolve `checkpoint/v4-canonical54-green-a220` branch and record SHA;
- current branch must be descendant of that checkpoint plus QA-report/docs-only drift;
- fresh registry enumeration = 68/13/0 dups;
- base/robust planner signature parity GREEN;
- plugin dummy-55 extensibility GREEN in test-only context;
- 0 production local factual reads before matrix;
- services healthy.

Any generic V4 runtime failure => RED and STOP.

## Phase 1 — canonical manifest reconciliation
Create:
`po-agent-platform-v2/qa_artifacts/a221_canonical54_manifest.json`

Required:
- exactly 54 rows;
- no duplicate canonical requirement;
- every row mapped to exactly one primary live V4 skill;
- merged/alias legacy names explicitly map to the current dot-style V4 skill;
- no infrastructure/meta skill counted as a canonical requirement;
- six post-48 additions present exactly once.

If denominator !=54 or any row unmapped => RED and STOP before traffic.

## Phase 2 — Group 1: task discovery/search (canonical 1–10)
Certify A/B/C for:
1 exact task lookup
2 phrase search
3 attachments
4 Excel attachments
5 PDF attachments
6 MSG attachments
7 assignee filter
8 status filter
9 sprint filter
10 release filter

Use live bounded REAL AS21 Oracle B.
For collections require exact key-set parity.
Attachment-specific rows require exact attachment metadata/type evidence.

Persist checkpoint after row 9 and again after row 10 if needed.

## Phase 3 — Group 2: task intelligence (11–20)
Certify:
11 grounded task summary
12 task definition quality
13 missing requirements
14 acceptance/testability analysis
15 dependency/link analysis
16 lifecycle/history
17 time in statuses
18 task aging
19 blocker analysis
20 similar/duplicate discovery

For deterministic analyses, Oracle B must reconstruct the same source inputs and formulas.
If a required source surface is absent, typed SOURCE_CONDITIONAL can pass only with independent proof.
No LLM-only unsupported factual claim.

Persist checkpoint after row 18.

## Phase 4 — Group 3: sprint/flow (21–32)
Certify:
21 sprint health
22 current sprint
23 sprint scope
24 velocity
25 throughput
26 WIP
27 cycle time
28 lead time
29 carryover
30 scope change
31 predictability
32 sprint risk queue

Use DMS current/recent sprint plus at least one second applicable product space where source data exists.
Verify formulas/units explicitly.
No invented previous sprint/baseline.

Persist checkpoint after row 27.

## Phase 5 — Group 4: team (33–40)
Certify:
33 workload distribution
34 WIP by member
35 blocked work
36 capacity/load
37 competency match
38 assignee recommendation
39 bottlenecks
40 distribution by competence

Use authoritative team identities.
No employee-performance scoring.
Capacity must preserve owner capacity policy + actual source data semantics.
If estimates/competency source is absent, fail closed exactly per certified contract.

Persist checkpoint after row 36.

## Phase 6 — Group 5: release + portfolio (41–48)
Certify:
41 release health/readiness
42 scope
43 progress
44 blockers
45 dependencies
46 risk queue
47 portfolio overview
48 PO attention queue

For current release linkage:
- independently probe source first;
- if membership remains unpopulated, release-derived rows must be typed SOURCE_CONDITIONAL;
- no zero-task release fabrication;
- portfolio/attention use their bounded current-sprint source contract and must remain source-exact.

Persist checkpoint after row 45.

## Phase 7 — Group 6: six reconciled additions (49–54)
Certify:
49 task search by product/space
50 release.forecast
51 po.daily_brief
52 po.status_report
53 po.reminder_draft
54 po.local_task_draft

release.forecast:
- live A/B/C expected SOURCE_CONDITIONAL while linkage unpopulated;
- controlled fixture contract must remain exact;
- no updated_at completion proxy.

PO draft skills:
- zero mutations;
- explicit point reads only where needed;
- user-only local draft = zero AS21 calls.

## Phase 8 — cross-skill unseen composition benchmark
Not part of 54 denominator, mandatory gate.

At least 3 fresh NL forms each:
- person + space + status
- person + sprint + status
- task -> assignee -> tasks
- current sprint -> downstream task collection
- task + time accounting
- sprint + member + time spent
- release identity -> explicitly requested release analytic
- PO brief -> drill into one grounded task

Require composition from reusable skills/capabilities.
No phrase-specific production branch.
No stale-state resurrection.

## Phase 9 — clarification/session benchmark
Cover:
- missing product;
- ambiguous sprint/release;
- clarification answer resumes original goal;
- explicit current query overrides old session context;
- new-dialog isolation;
- "Продолжи" without valid pending state fails safely;
- multi-hop clarification preserves original completion contract.

No user repetition required when valid pending request exists.

## Phase 10 — Browser C full-surface pass
For every canonical row, Browser C must have at least one real UI execution or an explicitly grouped UI execution that visibly exposes that row's result/state.

Verify:
- loading;
- COMPLETED / SUCCESS_WITH_DATA;
- REAL_EMPTY where proven;
- NEEDS_CLARIFICATION;
- SOURCE_CONDITIONAL / SOURCE_UNAVAILABLE;
- ERROR only for genuine unexpected failure;
- no blank widget;
- no misleading zero;
- no wrong-space data;
- no hidden write.

For source-conditional release skills, generic typed V4 panel is acceptable when no dedicated widget exists, provided the source limitation is clear and no data is fabricated.

## Phase 11 — independent source/write audit
Across the complete A221 window require:
- GET /api/v1/tasks local factual reads = 0;
- equivalent local DB/cache factual fallback = 0;
- unbounded/tenant-wide task scans = 0 unless a specifically certified source route has an explicit bounded tenant-level contract (none expected here);
- mutations POST/PUT/PATCH/DELETE = 0;
- source unavailable never converted to REAL_EMPTY;
- all release membership queries space-scoped;
- all sprint collections bounded and completeness-checked.

## Phase 12 — performance/operability observation
Record p50/p95 wall latency by category:
- simple point lookup;
- task collection;
- multi-hop composition;
- sprint analytics;
- time accounting;
- release SOURCE_CONDITIONAL;
- PO cross-product aggregation.

This is observation, not optimization.
Do not change code.
Flag pathological >60s ordinary cases separately.

## Phase 13 — retained architecture extras
Test, outside canonical denominator:
- agent.help full live catalog;
- conversational ping;
- member.time_spent;
- sprint.time_spent;
- team.time_spent;
- release.time_spent;
- team.utilization_actual;
- sprint utilization/current-period helpers;
- any other critical post-54 compositional helper identified in live registry.

Require no regression but do not alter 54 denominator.

## Required artifacts
Create/update:
- `po-agent-platform-v2/qa_artifacts/a221_canonical54_manifest.json`
- `po-agent-platform-v2/qa_artifacts/a221_matrix_progress.json`
- `po-agent-platform-v2/qa_artifacts/a221_source_audit.json`
- `po-agent-platform-v2/qa_artifacts/a221_latency.json`
- Browser screenshots/logs under `qa_221_browser_c/`
- final report:
  `po-agent-platform-v2/qa_reports/AGENT_CORE_V4_FULL_54_ABC_221.md`

Progress artifact must be resumable:
- row id;
- completed phases;
- hashes of relevant baseline files;
- source timestamp;
- status.
Do not rerun already certified rows after an unrelated later-row failure unless the owner fix could affect them.

## Final classification
Each canonical row must end as exactly one:
- GREEN_SOURCE_READY
- GREEN_SOURCE_FREE
- GREEN_SOURCE_CONDITIONAL
- RED

No UNKNOWN, SKIPPED, NOT_RUN in a GREEN final verdict.

## Verdict
Use exactly one:
- `AGENT_CORE_V4_FULL_54_ABC_GREEN_A221`
- `AGENT_CORE_V4_FULL_54_ABC_RED_A221`

If GREEN:
report:
- 54/54 terminally classified;
- counts by GREEN_SOURCE_READY / GREEN_SOURCE_FREE / GREEN_SOURCE_CONDITIONAL;
- 0 RED;
- exact source audit totals;
- Browser C coverage;
- p50/p95 latency summary;
- live registry count;
- then recommend Gate V4-LEARNING (Learning Reviewer 2.0).

If RED:
identify the first failing canonical row + first failing boundary (A, B, C, contract, source, UI, safety, performance);
commit/push partial resumable artifacts + report;
STOP.

Do not modify code.
