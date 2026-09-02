# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_130_POST_FIX_TRUE_AB_REGRESSION`

## Owner fix under test
Owner commit: `c1fdf2ff31072661dcfabce9ab7248fee5aa355e`

Assignment 129 proved the REAL AS21 live assignee facade is correct, but Harness task-search capabilities could still fetch the empty legacy task facade before locally filtering by assignee. The owner fix changes the production Core-8 task-search handler so `assignee` is preserved as a SOURCE selector and passed into `adapter.search_tasks(...)`, allowing `ProductionTaskApiAS21Adapter` to route to `/api/v1/swtr-read/assignee-tasks`.

This assignment must certify that fix with TRUE independent A/B evidence. Only after the focused gate is GREEN may you run the broader regression.

## Role boundary
You are QA/test executor only. Do NOT modify production/backend/frontend code, prompts, skills, adapters, Task API, MCP-SWTR, team configuration, AS21 data, test rules, or this file. Commit/push only QA artifacts under `po-agent-platform-v2/qa_reports/`.

## Absolute anti-surrogate rules
- NO task sync or local DB population.
- NO local DB/cache as Agent truth or Oracle truth.
- NO fake/mock/frozen fixtures as truth.
- NO copied historical task counts/keys as current Oracle.
- NO Harness/Agent result as Oracle B.
- NO AS21 writes.
- HTTP 200 / COMPLETED is not PASS.
- Exact business facts must match independent REAL AS21 Oracle B.
- For task collections exact task-key-set equality is mandatory.
- If Oracle B cannot be independently proven, verdict for that case is `ORACLE_NOT_PROVEN`, never PASS.
- Do not invent employees, statuses, spaces, sprints or source facts.

Approved task spaces globally: `WMB, STS, OLP, DMS, CRPV`.

## Retry / timing policy
AS21 can be transiently unavailable.
- timeout >=120 sec per source request;
- heavy operations may use 180 sec;
- retry transient timeout/5xx up to 2 times;
- 20–30 sec backoff;
- sequential execution / concurrency=1.
Do not classify a transient source outage as a product defect without retries.

# PHASE 0 — exact provenance and clean runtime
1. `git switch feat/core8-real-query-hardening-v2`.
2. `git pull --ff-only origin feat/core8-real-query-hardening-v2`.
3. Record exact HEAD. It MUST contain owner commit `c1fdf2ff31072661dcfabce9ab7248fee5aa355e`.
4. Record `git status --porcelain` and hashes/diffs of any pre-existing dirty production files. Do not modify/stash/delete them.
5. Stop ALL previous Harness and Task API processes. Record old PIDs.
6. Prove ports are free.
7. Start Task API and Harness from current HEAD. Record new PIDs, start times, commands and working directories.
8. Verify Harness, Task API, MCP-SWTR and REAL AS21 health.
9. Confirm fake/mock/frozen/local-sync authoritative use = 0 and AS21 writes = 0.

# PHASE 1 — fresh independent Oracle B for Garanin
Rebuild source truth from scratch. Do NOT copy Assignment 129 values.

Use the proven independent route:
`search_users -> unique Garanin.R.V/externalId -> find_units_by_filter(assigned_to = externalId) -> complete pagination`.

After complete REAL AS21 retrieval, normalize/filter only to approved spaces WMB/STS/OLP/DMS/CRPV.

Capture exact sets:
- `B_GARANIN_ALL_KEYS`
- `B_GARANIN_DMS_KEYS`
- `B_GARANIN_OLP_KEYS`
- per-space counts
- pagination proof
- raw Oracle evidence.

# PHASE 2 — direct Task API live boundary
Re-run live facade independently:
1. `/api/v1/swtr-read/assignee-tasks?assignee=Garanin.R.V`
2. same with `space=DMS`
3. same with `space=OLP`

Compare exact keys against Phase-1 Oracle subsets.

Required before Harness testing:
- generic facade == B_GARANIN_ALL_KEYS
- DMS facade == B_GARANIN_DMS_KEYS
- OLP facade == B_GARANIN_OLP_KEYS

If not, STOP with source/facade boundary defect. Do not blame Harness.

# PHASE 3 — focused Harness TRUE A/B gate
Use a NEW session for every query.

### Case A — generic member query
User query exactly:
`Задачи Гаранина`

Capture:
- status;
- semantic intent;
- skill id/version;
- resolved member login/externalId;
- slots and capability args;
- actual downstream adapter request/route;
- exact returned task keys;
- evidence IDs/source;
- answer text;
- elapsed time.

Required:
`A_GENERIC_KEYS == B_GARANIN_ALL_KEYS`.

The answer MUST NOT be zero when Oracle is non-zero.
The source path MUST be REAL AS21 live assignee search, not `/api/v1/tasks`.

### Case B — explicit DMS
Query:
`Задачи Гаранина в DMS`

Required:
`A_DMS_KEYS == B_GARANIN_DMS_KEYS`.

DMS is an approved space. The Agent must not ask a needless clarification solely because the user supplied `DMS`.

### Case C — explicit OLP
Query:
`Задачи Гаранина в OLP`

Required:
`A_OLP_KEYS == B_GARANIN_OLP_KEYS`.

OLP is an approved space. The Agent must not ask a needless clarification solely because the user supplied `OLP`.

### Focused gate
All three cases must pass exact set equality.
If any case fails: STOP broader regression and identify FIRST_FAILING_BOUNDARY. Do not continue to 54 skills.

# PHASE 4 — independent second-member control (Kalachanov)
Only after Phase 3 GREEN.

Do NOT reuse Garanin's DMS/OLP scope.
Build current REAL AS21 Oracle for `Kalachanov.V.V` using the same independent `search_users -> find_units_by_filter -> complete pagination` route.

Restrict only to globally approved spaces `WMB, STS, OLP, DMS, CRPV`; report actual current distribution. Do not assume counts from conversation/history.

Then fresh-session Agent query:
`Задачи Калачанова`

Required exact equality between Agent and independent Oracle across approved spaces.

Purpose: prove the fix is generalized and not Garanin-specific.

# PHASE 5 — assignee + status combinations
Only after Phases 3–4 GREEN.

Discover current REAL statuses from source data. Status names may differ by space. Never invent a canonical AS21 status that is absent in that space.

For at least:
- Garanin + one REAL DMS status with non-zero result;
- Garanin + one REAL OLP status with non-zero result;
- one second-member + one REAL status in a space where that member has tasks;

build Oracle B from complete live assignee retrieval then filter by the actual source status, and compare exact Agent task-key sets.

Also test a status phrasing previously unknown to the semantic layer if a valid real source status is available. If Agent asks for clarification, provide the source-backed status value and observe whether the learning/semantic path handles it correctly. Do NOT declare that arbitrary new source statuses must be permanently learned without evidence of the intended learning contract.

# PHASE 6 — sprint/task-search targeted regression
Only after Phases 3–5 GREEN.

Use REAL source facts. Prefer these known sprint candidates but revalidate them live before testing:
- `DMS-SPRNT-2`
- `DMS-SPRNT-1`
- `OLP-SPRNT-5`

Test at minimum:
- sprint-only task search;
- assignee + sprint where source facts permit complete Oracle proof;
- sprint + status where a real status exists;
- assignee + space;
- assignee + space + status;
- correction turn where status changes but member/space survives;
- exact task lookup for at least two source-backed task IDs;
- nonexistent task ID must not hallucinate.

For every task collection use exact-key A/B equality.

# PHASE 7 — dialogue quality / regression guards
Only after previous phases GREEN.

Verify in fresh sessions:
- no invented sprint when user says only `Задачи Гаранина`;
- Russian user input receives Russian Agent response;
- no unexplained English clarification;
- no correction-loop trap after selecting a clarification option;
- session context preserves unaffected slots across a correction;
- Agent does not repeatedly ask what must be improved when the user has supplied a concrete correction;
- no unauthorized member substitution.

# PHASE 8 — Learning Loop / Harness capability deep smoke
Only after core task-search gate is GREEN.

Do NOT promote a new policy unless the test contract explicitly requires it.

Verify observable lifecycle, not merely UI text:
- feedback/correction is accepted;
- source recheck occurs where required;
- candidate/evaluation/policy/version observability is reachable by the production Harness contract (or classify precise capability/observability gap);
- no duplicate policy creation for the same correction;
- no hardcoded entity fact learning;
- any previously promoted generalized policy remains restart-safe if applicable;
- rollback protection remains reachable;
- no regression of correction vs clarification separation.

If APIs are intentionally unavailable by design, classify them explicitly rather than fabricating lifecycle evidence.

# PHASE 9 — latency forensic sample
Measure end-to-end timings for at least:
- exact task lookup;
- generic Garanin assignee search;
- Garanin DMS search;
- one sprint query;
- one status query;
- one clarification/correction turn.

Break down where possible:
semantic interpretation / grounding / Task API / MCP-SWTR / response mapping.
Report p50-ish sample/individual values; do not optimize code in this assignment.
Flag repeated >10s Agent overhead that is not explained by REAL AS21 source latency.

# PHASE 10 — 54-skill regression gate
ONLY if Phases 1–9 have no proven product regression that invalidates the backend.

Run all 54 implemented skills sequentially against production paths.

Rules:
- live REAL AS21 when the skill contract requires source data;
- true independent Oracle B for every factual source-backed case where an Oracle can be established;
- source capability genuinely unavailable by design may be classified `EXPECTED_SOURCE_CAPABILITY_UNAVAILABLE`, but must not become PASS;
- missing real fix_version/history/snapshot data must not be fabricated;
- clarification is PASS only when the query is genuinely under-specified by contract;
- exact-key equality for task collections;
- no local DB/sync surrogate;
- actual calls must back reported canonical/paraphrase/edge cases;
- checkpoint/resumable execution is allowed;
- long/background execution is allowed;
- concurrency=1.

Report counts that sum exactly to 54.

# PHASE 11 — FIRST_FAILING_BOUNDARY
For any mismatch use the earliest evidence-backed boundary, for example:
- `SEMANTIC_INTERPRETATION`
- `MEMBER_IDENTITY_RESOLUTION`
- `SPACE_GROUNDING`
- `STATUS_GROUNDING`
- `SKILL_RESOLUTION`
- `CAPABILITY_ARGUMENT_BUILDING`
- `CAPABILITY_SELECTION`
- `TASK_API_ADAPTER`
- `MCP_TOOL_SELECTION`
- `SOURCE_QUERY_CONSTRUCTION`
- `SOURCE_RESPONSE_DECODING`
- `POST_SOURCE_FILTERING`
- `CAPABILITY_RESULT_PROPAGATION`
- `RESPONSE_STATUS_MAPPING`
- `RESPONSE_RENDERING`
- `LEARNING_POLICY_APPLICATION`
- `QA_HARNESS_ORACLE_DEFECT`

Always show LAST_CORRECT_ARTIFACT and FIRST_INCORRECT_ARTIFACT.
Do not guess root cause from final count alone.

# PHASE 12 — anti-surrogate audit
Mandatory in final report:
- exact HEAD;
- owner commit present;
- old/new PIDs;
- current source health;
- Oracle B method(s);
- exact-key comparisons;
- number of REAL AS21 reads;
- retries/timeouts;
- local DB/sync authoritative reads = 0;
- fake/mock/frozen authoritative reads = 0;
- AS21 writes = 0;
- no historical expected answer reused as current truth;
- 54-skill count arithmetic if Phase 10 runs.

## Allowed final verdicts
- `FOCUSED_GATE_GREEN_FULL_REGRESSION_GREEN`
- `FOCUSED_ASSIGNEE_GATE_DEFECT`
- `SPACE_GROUNDING_DEFECT`
- `STATUS_OR_COMBINATION_DEFECT`
- `DIALOGUE_REGRESSION_PROVEN`
- `LEARNING_LOOP_REGRESSION_PROVEN`
- `LATENCY_REGRESSION_PROVEN`
- `FULL_REGRESSION_PRODUCT_DEFECTS_PROVEN`
- `MIXED_PRODUCT_SOURCE_AND_QA_DEFECTS`
- `BLOCKED_BY_ENVIRONMENT`
- `ORACLE_NOT_PROVEN`

No other GREEN is allowed.

## Output
Primary report:
`po-agent-platform-v2/qa_reports/POST_FIX_TRUE_AB_REGRESSION_130.md`

Optional raw evidence prefix:
`POST_FIX_TRUE_AB_REGRESSION_130_`

## Finish
Commit/push ONLY QA report/raw evidence. Production code must remain untouched. Provide report path, full SHA, verdict and STOP.

## Start when instructed
Execute Assignment 130 autonomously and strictly as written.