# GigaCode — Current Action

## Status
`ACTIVE_OWNER_ASSIGNMENT_185_V4_BOUNDED_SOURCE_CORRECTNESS_HARDENING`

## Mission
Continue from Assignment 184. **Do not restart the V4 POC and do not change planner/model strategy.**

Assignment 184 certified the important architecture points:
- Assignment 183 transport fix works: DMS-380 benchmark is now **10/10 exact** against fresh REAL AS21;
- the three user-discovered capability/governance gaps are fixed (`sprint.search`, `sprint.list`, source-authority identity);
- safety remains fail-closed;
- planner is clean: zero recovery turns across the live matrix, JSON-primary trajectories, no semantic prepass;
- final verdict was `V4_BOUNDED_RED` only because of **two concrete pre-existing non-planner source/correctness defects**.

Your job is to fix **only those two bounded defects generically**, add regression coverage, prove them live against REAL AS21, then write the next QA-only Assignment 186 into this file and STOP. Do not run Assignment 186 in the same session.

## Mandatory pre-read
First:
```bash
git pull --ff-only origin feat/core8-real-query-hardening-v2
```
Then read:
- `po-agent-platform-v2/qa_reports/AGENT_CORE_V4_REPRESENTATIVE_POC_184.md`
- `po-agent-platform-v2/docs/v4_dod/V4_DOD_LOCK.md`
- current V4 source adapter/task-api code relevant to the two defects below.

## Absolute rules
- Keep current branch: `feat/core8-real-query-hardening-v2`.
- Keep current model/provider (`Qwen/Qwen3.8-27B`) unchanged.
- No surname/entity/query-specific hardcodes.
- No prompt-only workaround for source correctness defects.
- No local DB/fake/frozen truth for REAL-backed answers.
- Preserve fail-closed semantics.
- Do not loosen acceptance criteria.
- Do not broadly refactor unrelated code.
- Each fix must be generic and source-schema-driven.

---

## B1 — Fix REAL sprint-task collection for >100 tasks

### Proven defect from Assignment 184
For current DMS sprint, REAL TQL Oracle contains **104** tasks, but the task-api route:
`GET /api/v1/swtr-read/sprints/{id}/tasks?complete=true&limit=100&max_pages=100`
accumulates the same first page repeatedly because the live MCP `get_sprint_tasks` schema does not expose a page argument and row identity is nested under `unit.code`.

Observed failure signature:
- 10,000 accumulated rows;
- only 100 unique tasks;
- ~25 MB response;
- `complete=false`;
- agent exhausts bounded transport retries and fails closed after ~3×90 s.

### Required owner fix
Implement a **generic bounded collection strategy** for sprint tasks that cannot loop on an unpageable source.

Required properties:
1. `_source_task_code` / equivalent canonical identity extraction must understand the REAL nested task-code shape (including `unit.code`) generically.
2. A repeated source page that contributes **zero new canonical task identities** must terminate accumulation — never append the same page until `max_pages`.
3. If the live source cannot actually paginate beyond the first page, do **not** falsely claim a complete collection.
4. Prefer a source-backed way to obtain the true complete sprint set if available (e.g. TQL/search path using the sprint constraint) rather than silently returning 100/104.
5. If complete truth genuinely cannot be obtained, return a typed/incomplete condition rather than a fabricated complete set.
6. Preserve bounded latency and fail-closed behavior for a true source outage.

The desired production outcome for a source-valid sprint with >100 tasks is **exact full collection parity with fresh Oracle B**, not merely avoiding the timeout.

Add focused regression tests covering at least:
- nested `unit.code` identity extraction;
- repeated identical page stops immediately;
- >100 task sprint gets complete exact data through the chosen supported source path;
- no infinite/repeated-page amplification;
- incomplete source cannot be mislabeled complete.

---

## B2 — Fix terminal/open status correctness for encoded status keys

### Proven defect from Assignment 184
For STS assignee rows, the assignee-tasks route can expose encoded workflow status keys such as:
- `CNCLLD_...`
- `CLSD_...`
- other opaque workflow ids

The adapter currently maps many of these to `TaskStatus.UNKNOWN`, so `is_completed=False` and a `not_completed` query keeps terminal tasks.

Assignment 184 example:
- query family: open tasks for a person in STS;
- agent returned **2609**;
- fresh REAL oracle showed **404 true non-terminal**;
- 2205 terminal rows were incorrectly counted as open.

### Required owner fix
Make task completion classification **source-schema-aware and generic**.

Required properties:
1. Prefer authoritative decoded workflow/status semantics from source (`workflow_status.name`, status type/category, or equivalent) when available.
2. Do not maintain an entity/person/query-specific mapping.
3. Do not rely on brittle matching of one exact opaque status id if the source exposes a semantic field.
4. `is_completed` must correctly classify at least terminal categories equivalent to resolved/closed/cancelled/done and keep active/progress/pause/open categories non-terminal.
5. Unknown truly undecodable statuses must remain explicit/typed; do not arbitrarily classify them as open if doing so would corrupt an `open/not_completed` factual collection.
6. Preserve existing behavior for product spaces whose normal human-readable statuses already map correctly.

Add focused regression tests with mixed task rows proving:
- encoded terminal status + authoritative semantic metadata -> completed;
- active encoded status -> non-completed;
- ordinary human-readable statuses unchanged;
- `not_completed` filtering returns exact expected keys/count;
- unknown-without-semantic-evidence cannot silently inflate an "open tasks" result.

---

## Phase 3 — Focused regression + integration proof

Run focused tests for B1/B2 plus existing V4/transport/sprint/identity regression suites affected by the changes.

Then run broader po-agent tests and compare failures against the Assignment-184 baseline. No new regression is acceptable.

Static checks:
- no semantic prepass introduced;
- no planner/model/prompt strategy change;
- no entity/person/space-specific production branch for B1/B2;
- REAL AS21 remains authoritative;
- action-only recovery/fail-closed behavior unchanged.

---

## Phase 4 — REAL AS21 live owner verification

Use a fresh runtime/session, concurrency 1, fresh Oracle B. Do not hardcode prior counts.

### B1 live proof
Choose at least one REAL sprint whose fresh Oracle contains >100 tasks (DMS current sprint is acceptable if still source-valid).

Verify:
- direct production source path returns the **complete exact task-key set** vs fresh TQL/source Oracle;
- no duplicate-page amplification;
- no 3×90 s timeout pattern;
- natural query `Задачи в текущем спринте DMS` (or equivalent source-valid current-sprint query) completes with exact parity.

### B2 live proof
Choose a REAL assignee+space collection containing encoded statuses (STS case is acceptable if still source-valid).

Verify:
- fresh Oracle computes terminal/non-terminal from authoritative source semantics;
- production adapter maps status semantics correctly;
- natural `Открытые задачи <person> в <space>` returns the **exact non-terminal key set**, not merely the same count.

### Retained smoke checks
Also smoke-check, once each:
- `Покажи DMS-380 и затем задачи его исполнителя` — exact source-backed completion;
- `Активные спринты в DMS` — complete set, no singleton loss;
- `Открытые задачи Александра Жданова в августовском спринте DMS` — source-backed period resolution;
- valid non-roster REAL identity case (e.g. Пётр Иванов if still source-valid) — no roster veto;
- invented identity — fail closed.

Owner live checks are confidence checks, **not** the final QA certification.

---

## Phase 5 — Commit discipline

Commit the bounded production/test fixes in logical commits. Keep QA scratch artifacts untracked unless they are explicitly intended as durable regression fixtures/scripts.

After fixes and owner verification are GREEN, update this same `GIGACODE_NEXT_ACTION.md` with **Assignment 186 — QA-only V4 representative POC re-gate**.

Assignment 186 must require at minimum:
1. fresh build/protocol/static gate;
2. fresh REAL Oracle B;
3. B1 regression family: current-sprint/downstream task collection including a >100-task sprint, exact key parity;
4. B2 regression family: person+space+not_completed with encoded workflow statuses, exact key parity;
5. 10× DMS-380 benchmark retained;
6. the three previously fixed user scenarios retained;
7. mixed representative matrix + unseen combinations;
8. safety/governance/fail-closed checks;
9. final verdict exactly one of:
   - `AGENT_CORE_V4_REPRESENTATIVE_POC_GREEN`
   - `V4_PLANNER_STRATEGY_REVIEW_REQUIRED`
   - bounded RED with exact boundary
   - `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`
10. if GREEN: explicit recommendation to **STOP backend POC remediation and proceed to Browser C/UI, then progressive 54-skill catalog migration**.

QA 186 must be QA-only and must not edit production.

## Completion criteria for Assignment 185
Assignment 185 is complete only when:
- B1 is fixed generically and proven exact live;
- B2 is fixed generically and proven exact live;
- focused tests are GREEN;
- no new broader regression is introduced;
- safety/source-authority invariants remain intact;
- all owner changes are committed and pushed;
- `GIGACODE_NEXT_ACTION.md` contains the complete Assignment 186 QA instructions and is pushed.

Then **STOP**. Do not execute Assignment 186 in this run.

## Final response
Return:
- commit SHAs for B1, B2 and Assignment-186 spec;
- concise owner-verification results;
- confirmation that Assignment 186 is prepared but not started.