# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_133_FULL_54_SKILL_ABC_BATCHED_CERTIFICATION`

## Goal
Run one large end-to-end **A/B/C certification of the complete production skill catalog** over several hours, but execute it in small resumable batches so no single agent/subagent/streaming timeout can invalidate the whole run.

For every skill:

```text
A = PO Agent / Harness production path
B = independent REAL AS21/SWTR Oracle
C = actual application UI/browser path
```

The objective is not merely to find defects. The objective is to build a complete 54-skill matrix proving whether the same user intent produces the same business truth through A, B and C, while also exposing semantic/session/UI-wiring defects and first failing boundaries.

Assignment 132 is prior evidence only. It proved useful defects but executed only 8/54 skills and therefore is NOT a full certification baseline.

## Role boundary
You are QA/test executor only. Do NOT modify production/backend/frontend code, prompts, skills, adapters, Task API, MCP-SWTR, team configuration, AS21 data, testing rules, or this file. Commit/push only QA artifacts under `po-agent-platform-v2/qa_reports/`.

## Absolute anti-surrogate rules
- NO task sync/local DB/cache as Agent truth, Oracle truth, or UI acceptance truth.
- NO fake/mock/frozen fixtures as authoritative truth.
- NO historical counts/keys copied as current Oracle.
- NO Harness/Agent output reused as Oracle B.
- NO API-only substitution for C when the UI element exists and can be exercised through the real browser/frontend path.
- NO AS21 writes.
- A/B/C means three separately observed paths.
- For task collections, exact task-key-set equality is mandatory wherever B can establish the set.
- HTTP 200 / COMPLETED / rendered widget alone is never PASS if business facts mismatch.
- Empty UI / `0` is never PASS unless B proves REAL_EMPTY.
- If Oracle cannot be independently established, classify `ORACLE_NOT_PROVEN`, not PASS.

Approved task spaces globally: `WMB, STS, OLP, DMS, CRPV`.
Use real configured team members and approved real entities. Do not invent external people/sprints/releases to manufacture coverage.

# EXECUTION MODEL — mandatory batching

This is ONE assignment but MUST NOT be run as one giant subagent request.

## Batch rules
- Dynamically discover the complete production skill catalog first. Current reconciled target is 54; runtime discovery is authoritative.
- Partition all discovered skills into **small deterministic batches of 6 skills maximum**. If a skill is known/heavy, use 3–4 in that batch.
- Each batch has its own fresh execution context and checkpoint file.
- Run batches sequentially, concurrency=1.
- Do not restart successful earlier batches after a later timeout.
- After every batch, immediately write/update checkpoint evidence to disk before proceeding.
- If a runner/streaming/subagent timeout occurs, classify it as QA-runner infrastructure, preserve completed rows, and resume from the first unfinished skill with a fresh context.
- A single streaming timeout MUST NOT terminate Assignment 133.
- Never reduce the total catalog sample because of timeout. Resume until all discovered skills are classified or a proven environment outage prevents continuation.

## Timeout rules
- REAL AS21 normal source timeout: >=120 sec.
- Heavy source/capability call: up to 180 sec.
- Transient source timeout/5xx: retry up to 2 times, 20–30 sec backoff.
- Agent/subagent streaming context: keep each batch small enough to avoid the ~483 sec failure seen in Assignment 132.
- Prefer a non-streaming/direct scripted runner for deterministic batch orchestration where available.
- Global assignment wall-clock target: approximately 2–4 hours. Do not stop merely because two hours elapsed if only a small remainder is unfinished.

# PHASE 0 — provenance / clean runtime / UI boot
1. Pull `feat/core8-real-query-hardening-v2`.
2. Record exact HEAD and `git status --porcelain`.
3. Record pre-existing dirty production files separately; QA must not alter them.
4. Hard restart Task API and Harness from current HEAD; record PIDs/start commands/timestamps.
5. Start/restart the actual frontend from current HEAD and record URL/process/build mode.
6. Verify MCP-SWTR and REAL AS21 health.
7. Verify the UI can reach the same Harness environment being tested by A.
8. Record fake/mock/frozen/local-sync authoritative reads=0 and AS21 writes=0.
9. Create a unique assignment namespace for sessions: `qa:133:<batch>:<case>:<uuid>` for A; C/browser uses independent fresh browser conversation IDs and must never reuse A session state.

# PHASE 1 — catalog discovery and test-plan generation
1. Enumerate ALL callable production skills from the running registry/runtime.
2. Reconcile against the expected 54 catalog. If count differs, record the exact difference; do not silently force 54.
3. For each skill derive one realistic canonical Russian business query and, when meaningful, one short paraphrase/correction variant.
4. Map the intended UI route/screen/widget/action for C. If a skill has no dedicated UI widget, C may use the actual Assistant/chat UI, but it must still be exercised through the frontend/browser rather than calling Harness directly.
5. Assign each skill to a deterministic batch of <=6 skills.
6. Write the batch manifest before execution.

Primary manifest/checkpoint prefix:
`po-agent-platform-v2/qa_reports/FULL_54_SKILL_ABC_CERTIFICATION_133_`

# PHASE 2 — focused controls before broad batches
Run these controls once before Batch 1, using fresh independent sessions:

1. `Задачи Гаранина`
2. `Задачи Гаранина в DMS`
3. `Задачи Калачанова`
4. one existing exact task ID freshly proven by B
5. one guaranteed nonexistent task ID with a simultaneous known-good source-health point read

For each capture A, B and C. Do NOT stop the assignment if a product defect is reproduced. Record it, identify a preliminary boundary and continue into the batches unless the environment itself is unusable.

Known Assignment 132 clusters to recheck, not assume:
- NOT_FOUND vs SOURCE_UNAVAILABLE mapping;
- approved-space grounding/clarification;
- `task_quality`, `velocity`, `competency_match` `NoneType.get` errors.

# PHASE 3 — FULL A/B/C skill batches

For EVERY discovered production skill execute A, B and C where the contract permits factual comparison.

## A — Agent / Harness
Capture:
- natural-language query;
- unique A session ID;
- interpreter class;
- `llm_used` where exposed;
- raw semantic intent/slots;
- grounded frame;
- resolved skill/capability;
- capability args;
- downstream source route;
- response status/text;
- evidence IDs/source type;
- normalized facts/task keys/metrics;
- elapsed time.

Ordinary Russian NL queries are expected to use the production LLM-first semantic path. If a key case unexpectedly shows heuristic/non-LLM interpretation, classify and trace it.

## B — independent REAL AS21 Oracle
Construct B independently from A using direct authoritative AS21/SWTR operations. Do not reuse Harness capability output.

Capture:
- exact source operation/query/filter;
- authoritative entity resolution;
- normalized raw facts;
- exact task keys where applicable;
- independent metric calculation where applicable;
- source timestamp/latency;
- source-health evidence.

If the source contract cannot provide a historical fact required by the skill, classify precisely:
`SOURCE_CAPABILITY_UNAVAILABLE_BY_DESIGN`, `SOURCE_DATA_MISSING`, or `ORACLE_NOT_PROVEN`.
Do not fabricate history from current state.

## C — actual UI/browser
For the same business intent:
- use a fresh or intentionally controlled browser conversation/session as required;
- exercise the real frontend component/Assistant UI;
- capture browser conversation/session identifier when observable;
- capture actual frontend request/response path where tooling permits;
- capture visible result/status/count/task keys/metric;
- capture loading/empty/partial/error state;
- record screenshot or machine-readable browser evidence where practical;
- verify the UI does not silently substitute stale local values.

If a dedicated widget exists, use it. If the skill is only exposed through Assistant/chat today, use the actual chat UI and mark `C_SURFACE=ASSISTANT_UI`.

A UI element returning nothing/0 while B has data is a product defect, not an acceptable empty state.

## A/B/C comparison rule
Classify each skill row with all applicable comparisons:

```text
A_vs_B = semantic/business truth parity
C_vs_B = UI/business truth parity
A_vs_C = application path parity
```

For task collections:
`set(A.task_keys) == set(B.task_keys) == set(C.task_keys)` where all three expose task sets.

For aggregates/metrics, compare underlying source sets first, then the derived metric.

For narrative-only synthesis, verify all factual claims against B and compare key structured facts rather than prose wording.

# PHASE 4 — UI data-wiring audit embedded into every batch
For each C execution, record a compact lineage:

```text
UI screen/component
 -> frontend request
 -> API endpoint
 -> Harness skill/capability
 -> adapter/source route
 -> REAL AS21 truth
```

Classify visible UI state as one of:
`LOADING`, `SUCCESS_WITH_DATA`, `REAL_EMPTY`, `PARTIAL_DATA`, `SOURCE_UNAVAILABLE`, `NOT_FOUND`, `ERROR`.

Flag:
- unexplained empty/zero widget;
- stale data after filter/session change;
- wrong endpoint/capability;
- missing filter propagation;
- UI-specific truncation/mapping defect;
- browser session contamination;
- API response correct but rendering incorrect.

# PHASE 5 — semantic/dialogue/session regression
Across the batches ensure fresh coverage of:
- exact existing task;
- nonexistent task;
- person only;
- space only;
- person + space;
- person + status;
- person + space + status;
- valid sprint query where a real sprint exists;
- correction where changed slot replaces old value and unaffected slots survive;
- second-member control;
- Russian input -> Russian response;
- no unauthorized entity substitution;
- no needless clarification for approved spaces;
- fresh New Chat does not inherit correction state;
- A session and C/browser session do not contaminate each other;
- parallel/background QA activity with a different session ID does not alter C conversation state.

# PHASE 6 — Learning Loop A/B/C certification
This phase is mandatory and MUST be completed even if other skill defects exist.

Use at least three representative skills from different domains, including one task-search case and one analytical skill.

For each:
1. Execute initial request through C/browser and A capture.
2. Give explicit negative feedback/correction through the actual UI.
3. Observe dialogue/session classification.
4. Prove whether a fresh REAL AS21 recheck occurs.
5. Compare post-feedback result with B.
6. Inspect whether a generalized learning/repair candidate is created via the supported runtime path.
7. Prove no entity/count/task-ID memorization.
8. Prove an unsupported complaint does not create a false rule such as `zero is impossible`.
9. If persistence is currently supported, test cold restart/reload and rollback; otherwise classify the exact unsupported boundary.
10. Record whether current UX autonomously localizes mismatch or merely asks for clarification.

Do not mark the Learning Loop GREEN merely because a `correction` JSON object exists.

# PHASE 7 — known-defect forensic / FIRST_FAILING_BOUNDARY
For every mismatch, trace the earliest evidence-backed divergence. At minimum fully localize every reproducible Assignment 132 defect cluster.

Required format per defect:

```text
USER_INTENT
A artifacts
B artifacts
C artifacts
LAST_CORRECT_ARTIFACT
FIRST_INCORRECT_ARTIFACT
FIRST_FAILING_BOUNDARY
affected skills/UI surfaces
repro count
```

Allowed labels include:
`SEMANTIC_INTERPRETATION`, `SESSION_STATE`, `MEMBER_IDENTITY_RESOLUTION`, `SPACE_GROUNDING`, `STATUS_GROUNDING`, `SKILL_RESOLUTION`, `CAPABILITY_ARGUMENT_BUILDING`, `TASK_API_ADAPTER`, `MCP_TOOL_SELECTION`, `SOURCE_QUERY_CONSTRUCTION`, `SOURCE_RESPONSE_DECODING`, `POST_SOURCE_FILTERING`, `CAPABILITY_RESULT_PROPAGATION`, `RESPONSE_STATUS_MAPPING`, `RESPONSE_RENDERING`, `UI_DATA_WIRING`, `UI_STATE_MAPPING`, `UI_SESSION_LIFECYCLE`, `LEARNING_REVIEW`, `LEARNING_POLICY_APPLICATION`, `QA_HARNESS_ORACLE_DEFECT`.

Do NOT propose broad fixes when the boundary is not proven.

# PHASE 8 — source integrity / latency / resiliency
Across the whole assignment report:
- REAL AS21 read evidence/call count where auditable;
- HTTP 500/502/timeouts/retries;
- runner/streaming timeouts separately from product/source errors;
- source health before, during representative batches and after completion;
- fake/mock/frozen/local-sync authoritative reads=0;
- AS21 writes=0;
- A latency and C end-user latency distributions;
- representative fast/heavy p50/p95 samples where enough data exist.

# PHASE 9 — batch completeness and anti-surrogate audit
Before final verdict prove:
- exact HEAD tested;
- runtime/frontend provenance;
- discovered skill count and exact unique skill list;
- every skill has a terminal classification row;
- no duplicated row used to inflate arithmetic;
- every batch checkpoint exists;
- all completed batches survived any later timeout/restart;
- every factual PASS has B evidence;
- every UI PASS has C evidence;
- no unresolved placeholders;
- no historical truth substituted;
- no production files modified by QA.

If runtime discovery returns 54, arithmetic MUST equal exactly 54.
If runtime discovery differs, arithmetic MUST equal the discovered count and the catalog discrepancy is separately reported.

# FINAL MATRIX — mandatory columns
At minimum:

| # | Skill | Query | A status | B status | C status | A_vs_B | C_vs_B | A_vs_C | LLM used | Source route | UI surface | Latency A | Latency C | Verdict | First failing boundary |

Every discovered skill must have exactly one primary row.

# Final verdict rules
Use ONE primary assignment verdict:

- `FULL_ABC_CERTIFICATION_GREEN` — all discovered skills classified; all required A/B/C factual comparisons GREEN; no product defects; Learning Loop/session/UI gates GREEN.
- `FULL_ABC_PRODUCT_DEFECTS_PROVEN` — complete catalog classified and one or more product defects proven.
- `FULL_ABC_MIXED_PRODUCT_AND_UI_DEFECTS_PROVEN` — complete catalog classified with both backend/agent and UI-specific defects.
- `FULL_ABC_PARTIAL_ENVIRONMENT_BLOCK` — all feasible batches completed but a proven environment/source outage blocks specified remainder.
- `ORACLE_NOT_PROVEN` — required independent truth cannot be established for material portions.

Do NOT call the assignment FULL/GREEN if skills were merely skipped because a subagent or streaming request timed out.

# Output
Primary report:
`po-agent-platform-v2/qa_reports/FULL_54_SKILL_ABC_CERTIFICATION_133.md`

Mandatory batch/checkpoint evidence:
`po-agent-platform-v2/qa_reports/FULL_54_SKILL_ABC_CERTIFICATION_133_BATCH_<NN>.md`

Recommended raw machine-readable matrix:
`po-agent-platform-v2/qa_reports/FULL_54_SKILL_ABC_CERTIFICATION_133_MATRIX.json`

# Finish
Commit/push ONLY QA report/checkpoint/raw evidence under `qa_reports/`.
Do not modify production code.
Return:
- report path;
- full SHA;
- discovered skill count;
- exact PASS/FAIL/BLOCKED arithmetic;
- number of A/B/C-complete rows;
- number of backend defects;
- number of UI-specific defects;
- Learning Loop verdict;
- primary verdict;
- STOP.

## Start now
Execute Assignment 133 autonomously as one multi-hour certification job, using resumable batches exactly as specified.