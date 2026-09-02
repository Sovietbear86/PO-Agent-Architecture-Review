# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_134_NO_SKIP_FULL_54_SKILL_ABC_MARATHON`

## Why Assignment 133 is rejected as incomplete
Assignment 133 is NOT accepted as a full A/B/C certification.

It discovered 54 skills but executed only 33. Batches 2–4 timed out and execution advanced past them. The final report was generated with 21 skills missing. It also claimed full A/B/C while the report does not contain complete real browser/UI evidence for every executed skill. This violates the assignment contract.

Assignment 134 exists to remove all ambiguity. This is a **hard no-skip marathon**. You are not being asked to sample, estimate, extrapolate, infer, or summarize. You must execute every discovered production skill and produce explicit A/B/C evidence for every row.

Historical reports 110C/132/133 are diagnostic evidence only. Do not reuse their PASS/FAIL values as current truth.

---

# ABSOLUTE STOP RULES — READ FIRST

1. **DO NOT GENERATE THE FINAL REPORT UNTIL EVERY DISCOVERED SKILL HAS A TERMINAL ROW.**
2. If runtime discovery returns 54 skills, then the final matrix MUST contain exactly 54 unique skill rows. `33/54`, `53/54`, or `54 cataloged but 33 executed` is forbidden.
3. **A timeout is NOT a terminal skill result.** A timed-out skill remains `PENDING_RETRY` and must be retried until it receives a real terminal product/source/UI classification.
4. **DO NOT MOVE TO THE NEXT BATCH while any skill in the current batch is `PENDING`, `RUNNER_TIMEOUT`, or missing A/B/C evidence.**
5. If a batch times out, split THAT SAME unfinished batch into smaller batches and retry. Do not advance.
6. If a 3-skill batch still times out, run the unfinished skills ONE BY ONE.
7. If one skill times out, restart a fresh runner/context and rerun THAT SAME skill. Do not skip it.
8. Runner/subagent/streaming timeout must never be converted into product FAIL, PASS, CHECK, or omitted row.
9. Do not stop simply because product defects are found. The purpose is complete defect inventory across the whole catalog.
10. Do not create or push a final report while `pending_count > 0`.
11. Before final report generation, run a machine-readable completeness assertion. If it fails, continue execution; do not report.
12. GigaCode must not modify production/backend/frontend code, prompts, skills, adapters, AS21 data or test rules. QA artifacts only.

The only legitimate early termination is a **proven persistent environment outage** that makes further execution impossible after the recovery procedure below. Even then, do not call the result FULL certification.

---

# TEST MODEL

For EVERY skill:

```text
A = actual PO Agent / Harness production natural-language path
B = independent REAL AS21/SWTR Oracle
C = actual application frontend/browser path
```

A/B/C are separately observed paths. C is not a second API call masquerading as UI.

Approved spaces: `WMB`, `STS`, `OLP`, `DMS`, `CRPV`.
Use real configured team members and real validated sprints/releases/entities. Never invent business data to make a query executable.

No local DB/sync/fake/mock/frozen source may be authoritative for A, B or C. No AS21 writes.

---

# EXECUTION ARCHITECTURE — CONTROLLER, NOT ONE LONG SUBAGENT

Do NOT ask one subagent to execute the whole assignment.

The top-level GigaCode process acts only as a **marathon controller**. Actual test work is deterministic and checkpointed.

Create/maintain a persistent machine-readable state file:

`po-agent-platform-v2/qa_reports/FULL_54_SKILL_ABC_134_STATE.json`

Required per-skill state:

```json
{
  "skill": "...",
  "ordinal": 1,
  "batch": "B01",
  "state": "PENDING|RUNNING|PENDING_RETRY|COMPLETE",
  "attempts": 0,
  "A_complete": false,
  "B_complete": false,
  "C_complete": false,
  "terminal_classification": null,
  "last_error": null,
  "evidence_files": []
}
```

Write state to disk **after every individual skill**, not merely after a batch.

On runner/context restart, reload this file and continue from the lowest ordinal whose state is not `COMPLETE`.

Never reconstruct progress from memory or chat context.

---

# TIMEOUT / RETRY POLICY — MANDATORY

## Product/source call timeouts
- normal REAL AS21/Harness call: **180 seconds minimum**;
- known heavy analytical capability: **300 seconds**;
- browser/UI wait for backend-driven result: **300 seconds**;
- concurrency: **1**.

## Retry policy per A/B/C leg
For timeout, 500, 502, transport reset, streaming failure or transient source error:

1. preserve raw error evidence;
2. wait 30 seconds;
3. source health-check with a known-good lightweight REAL AS21 request;
4. retry same leg;
5. maximum 3 normal attempts;
6. if runner/subagent itself timed out, start a fresh execution context and continue SAME skill;
7. if still unresolved, run SAME skill alone with no other skills in context;
8. only after the single-skill retry path is exhausted may it receive a terminal `SOURCE_UNAVAILABLE_CONFIRMED` or `ENVIRONMENT_BLOCKED` classification — and only with independent health evidence proving that classification.

A streaming/request timeout of the QA executor is NEVER proof that the product timed out.

---

# PHASE 0 — PROVENANCE AND CLEAN RUNTIME

1. Pull `feat/core8-real-query-hardening-v2`.
2. Record exact HEAD.
3. Record `git status --porcelain` and distinguish pre-existing dirt from QA artifacts.
4. Hard restart Harness and Task API from current HEAD. Record PID, timestamp and start command.
5. Hard restart actual frontend from current HEAD. Record URL/process/build mode.
6. Verify actual browser can load UI and reach the same Harness environment as A.
7. Verify REAL AS21/MCP-SWTR with at least two known-good reads from different approved spaces.
8. Verify authoritative local DB reads=0, fake/mock/frozen reads=0, AS21 writes=0.
9. Record test start timestamp and monotonic elapsed time.

Do not start catalog execution if A, B and C base environments are not all usable.

---

# PHASE 1 — DISCOVER CATALOG AND FREEZE MANIFEST

1. Dynamically enumerate callable production skills from the runtime registry.
2. Write exact ordered list to:
   `FULL_54_SKILL_ABC_134_MANIFEST.json`
3. If discovered count is 54, freeze `expected_count=54`.
4. Create one canonical realistic Russian query for every skill before execution begins.
5. Map each skill to its C surface:
   - dedicated screen/widget if one exists;
   - otherwise actual Assistant UI/chat.
6. Create initial state file with all skills `PENDING`.
7. Calculate checksum/hash of ordered skill names and include it in state/report so skills cannot silently disappear later.

Do not derive PASS/FAIL from catalog metadata. Catalog presence proves implementation registration only, not skill execution.

---

# PHASE 2 — CONTROL TRIAD

Before skill 1, execute and preserve complete A/B/C evidence for:

- `Задачи Гаранина`;
- `Задачи Гаранина в DMS`;
- `Задачи Калачанова`;
- one fresh existing exact task;
- one guaranteed nonexistent exact task while a known-good point-read proves source health.

Do not stop because controls expose product defects. Continue catalog execution. The controls exist to anchor current runtime truth and catch broken QA wiring.

Important consistency rule: the final report may not later claim an assignee regression contradicted by its own current controls without new reproducing evidence. Historical defects are not current defects unless reproduced in Assignment 134.

---

# PHASE 3 — STRICT 54-SKILL MARATHON

## Initial batching
Start with batches of **3 skills**, not 6.

Heavy skill families (`sprint-*`, `release-*`, competency/quality/history/forecast) should default to **1 or 2 skills per batch**.

After each skill, write its raw evidence + update state.

## Batch barrier
At the end of each batch execute:

```text
assert every skill in current_batch has state == COMPLETE
assert every skill in current_batch has A_complete == true
assert every skill in current_batch has C_complete == true
assert B_complete == true OR an evidence-backed typed Oracle limitation exists
```

If any assertion fails, DO NOT increment batch number.

Retry only unfinished skills.

## Per-skill A execution
Use production Russian NL query through actual Harness entry point. Capture:
- exact query;
- unique session ID `qa:134:A:<ordinal>:<uuid>`;
- interpreter class and `llm_used` when exposed;
- raw semantic frame;
- grounded frame;
- selected skill/capability;
- capability args;
- source route;
- status;
- response;
- evidence IDs;
- exact task keys or structured facts/metric;
- elapsed time;
- raw error/trace if not successful.

A returning `COMPLETED` with zero data is not PASS unless B supports zero.

## Per-skill B execution
Use independent REAL AS21/SWTR operations, not Harness capability output.
Capture:
- direct source operation/query/filter;
- real entity IDs resolved;
- raw source evidence;
- normalized task-key set/source facts;
- independently calculated metric where possible;
- source health and elapsed time.

If B genuinely cannot establish a skill's historical/derived fact due to source contract, use a precise typed result: `SOURCE_CAPABILITY_UNAVAILABLE_BY_DESIGN`, `SOURCE_DATA_MISSING`, or `ORACLE_NOT_PROVEN`. This still requires evidence and does not allow skipping A or C.

## Per-skill C execution — REAL UI REQUIRED
C must go through the actual frontend/browser.

For every skill:
- open/use the mapped UI surface;
- use a fresh browser conversation for independent queries unless continuity is part of the test;
- type/submit the real query through UI when Assistant UI is the surface;
- wait for terminal UI state, not an arbitrary short sleep;
- capture visible answer/data/status;
- capture browser/network request evidence where available;
- capture screenshot for FAIL/ERROR/EMPTY-with-B-data and at least one PASS per batch;
- normalize visible task keys/count/metric;
- capture C latency.

**Calling Harness or frontend API directly is not C.**
If browser automation is unavailable/broken, repair the QA browser setup only (not product code) or classify environment block after proving it. Do not pretend API output is UI evidence.

## Per-skill comparisons
Record:
- `A_vs_B`;
- `C_vs_B`;
- `A_vs_C`.

For task collections exact set equality is required whenever exposed:

```text
set(A.keys) == set(B.keys)
set(C.keys) == set(B.keys)
```

For aggregates, compare source population/set first, metric second.

For narrative skills, independently verify every business fact against B where feasible.

---

# PHASE 4 — CONTINUOUS COMPLETENESS WATCHDOG

After every 5 completed skills, print and persist:

```text
DISCOVERED = N
COMPLETE = X
PENDING = N-X
A_COMPLETE = ...
B_COMPLETE_OR_TYPED = ...
C_COMPLETE = ...
NEXT_SKILL = ...
```

Required invariant:

```text
COMPLETE + PENDING == DISCOVERED
```

Never report "remaining skills completed" unless the state file proves all earlier timed-out skills are also complete.

If a batch timeout occurred earlier, the watchdog must list those exact skills as PENDING until actually rerun.

---

# PHASE 5 — SEMANTIC / SESSION / DIALOGUE REGRESSION

After all catalog rows are COMPLETE, run dedicated A/B/C scenarios for:
- exact existing task;
- nonexistent task (`NOT_FOUND` vs `SOURCE_UNAVAILABLE`);
- person only;
- approved space only;
- person + approved space;
- person + status;
- person + space + status;
- valid sprint;
- correction replacing status while preserving member/space;
- second-member control;
- Russian input -> Russian response;
- New Chat creates fresh dialogue state;
- A and C sessions never share correction state;
- background QA session cannot contaminate browser conversation.

Do not infer `SPACE_GROUNDING` from `NEEDS_CLARIFICATION` alone. Capture raw semantic frame and grounded frame, then prove the first failing boundary.

---

# PHASE 6 — LEARNING LOOP A/B/C — MANDATORY

Run only after all catalog skills are complete, but run even if many product defects exist.

Use at least 3 representative scenarios from different domains.
For each:
1. initial C/browser query;
2. A trace;
3. B truth;
4. explicit negative feedback through actual UI;
5. dialogue-act/session trace;
6. fresh REAL AS21 source recheck evidence;
7. post-feedback result vs B;
8. generalized repair/policy candidate inspection through supported runtime path;
9. prove no member/task/count memorization;
10. unsupported complaint must not promote a false invariant;
11. persistence/restart/rollback if current implementation claims support.

A mere `correction` JSON object is not Learning Loop certification.

---

# PHASE 7 — FIRST FAILING BOUNDARY

For every reproducible mismatch use this exact evidence structure:

```text
USER_INTENT
A_QUERY_AND_SESSION
A_RAW_SEMANTIC_FRAME
A_GROUNDED_FRAME
A_CAPABILITY_ARGS
A_SOURCE_ROUTE_AND_RESULT
B_DIRECT_QUERY_AND_RESULT
C_BROWSER_REQUEST_AND_VISIBLE_RESULT
LAST_CORRECT_ARTIFACT
FIRST_INCORRECT_ARTIFACT
FIRST_FAILING_BOUNDARY
REPRO_ATTEMPTS
AFFECTED_SKILLS
```

Do not guess root cause from symptoms. For example, `NEEDS_CLARIFICATION` is a symptom; `SPACE_GROUNDING` may be the boundary only if the raw/grounded trace proves it.

Allowed boundaries:
`SEMANTIC_INTERPRETATION`, `SESSION_STATE`, `MEMBER_IDENTITY_RESOLUTION`, `SPACE_GROUNDING`, `STATUS_GROUNDING`, `SKILL_RESOLUTION`, `CAPABILITY_ARGUMENT_BUILDING`, `TASK_API_ADAPTER`, `MCP_TOOL_SELECTION`, `SOURCE_QUERY_CONSTRUCTION`, `SOURCE_RESPONSE_DECODING`, `POST_SOURCE_FILTERING`, `CAPABILITY_RESULT_PROPAGATION`, `RESPONSE_STATUS_MAPPING`, `RESPONSE_RENDERING`, `UI_DATA_WIRING`, `UI_STATE_MAPPING`, `UI_SESSION_LIFECYCLE`, `LEARNING_REVIEW`, `LEARNING_POLICY_APPLICATION`, `QA_RUNNER_DEFECT`, `QA_HARNESS_ORACLE_DEFECT`.

---

# PHASE 8 — FINAL COMPLETENESS GATE — CODE ASSERTION REQUIRED

Before writing even one line of the final Markdown report, run a deterministic validator over the state/matrix.

If runtime discovered 54, these assertions must pass:

```text
assert discovered_count == 54
assert len(unique_skill_names) == 54
assert complete_count == 54
assert pending_count == 0
assert every row has A_complete == true
assert every row has C_complete == true
assert every row has B_complete == true OR valid typed B limitation with evidence
assert no row state in [PENDING, RUNNING, PENDING_RETRY]
assert no duplicate skill names
assert every COMPLETE row has an evidence file
```

Write validator output to:
`FULL_54_SKILL_ABC_134_COMPLETENESS.json`

**If any assertion fails: DO NOT GENERATE FINAL REPORT. Return to the first unfinished skill and continue.**

This is the most important rule in Assignment 134.

---

# PHASE 9 — FINAL REPORT

Only after Phase 8 is GREEN generate:

`po-agent-platform-v2/qa_reports/FULL_54_SKILL_ABC_CERTIFICATION_134.md`

Mandatory matrix columns:

| # | Skill | Query | A status | B status | C status | A_vs_B | C_vs_B | A_vs_C | Attempts | LLM used | Source route | UI surface | Latency A | Latency B | Latency C | Verdict | First failing boundary |

The report must contain all rows, not a sample.

Also report:
- discovered / complete / pending arithmetic;
- total A calls;
- total independent B reads;
- total actual C/browser executions;
- source timeouts/retries;
- QA-runner timeouts/restarts separately;
- backend defect clusters;
- UI-specific defect clusters;
- Learning Loop verdict;
- exact list of typed source limitations;
- no fake/mock/local-sync truth;
- AS21 writes=0.

A product defect does not reduce required coverage. `FULL_ABC_PRODUCT_DEFECTS_PROVEN` requires COMPLETE catalog coverage, not partial coverage.

---

# ENVIRONMENT OUTAGE ESCAPE HATCH — VERY STRICT

You may terminate before 54/54 only if ALL are true:
1. the environment itself prevents execution, not merely one QA runner context;
2. current skill was retried in a fresh context and alone;
3. source/UI health checks independently reproduce the outage;
4. at least 3 attempts with backoff are documented;
5. restart of the affected QA/service process was attempted where safe;
6. exact unfinished skill list remains in state file;
7. final verdict is `BLOCKED_BY_ENVIRONMENT_INCOMPLETE`, never FULL certification.

A 120s or 483s subagent/streaming timeout by itself does NOT satisfy this escape hatch.

---

# FINAL VERDICTS

Allowed:
- `FULL_ABC_CERTIFICATION_GREEN` — 54/54 complete, required A/B/C gates GREEN, Learning/session gates GREEN.
- `FULL_ABC_PRODUCT_DEFECTS_PROVEN` — 54/54 complete, backend/product defects proven.
- `FULL_ABC_MIXED_PRODUCT_AND_UI_DEFECTS_PROVEN` — 54/54 complete, both backend and UI-specific defects proven.
- `BLOCKED_BY_ENVIRONMENT_INCOMPLETE` — only under strict outage escape hatch.

Forbidden:
- any verdict beginning `FULL_` when complete_count < discovered_count;
- "timeout-limited sample" as a completed assignment;
- extrapolating "30+ affected" from unexecuted skills;
- PASS for `COMPLETED tasks=0` without Oracle evidence;
- finalizing after skipping a timed-out batch;
- catalog presence being counted as skill execution;
- API response being counted as C/browser evidence.

---

# OUTPUT ARTIFACTS

Mandatory:
- `FULL_54_SKILL_ABC_134_MANIFEST.json`
- `FULL_54_SKILL_ABC_134_STATE.json`
- `FULL_54_SKILL_ABC_134_COMPLETENESS.json`
- one evidence/checkpoint artifact per batch/skill as needed;
- `FULL_54_SKILL_ABC_CERTIFICATION_134.md`

Commit/push QA artifacts only after the final report exists, or if a true environment outage requires preserving incomplete state/evidence.

At finish print exactly:

```text
Assignment 134 complete
HEAD: ...
DISCOVERED: ...
COMPLETE: ...
PENDING: ...
A_COMPLETE: ...
B_COMPLETE_OR_TYPED: ...
C_COMPLETE: ...
A_CALLS: ...
B_READS: ...
C_BROWSER_EXECUTIONS: ...
QA_RUNNER_TIMEOUTS: ...
PRODUCT_DEFECT_CLUSTERS: ...
UI_DEFECT_CLUSTERS: ...
LEARNING_LOOP: ...
VERDICT: ...
REPORT: ...
SHA: ...
STOP
```

If `PENDING != 0`, `Assignment 134 complete` is forbidden.

## Start now
Execute Assignment 134 autonomously. Expect this to take hours. Correctness and complete 54/54 evidence are more important than speed.