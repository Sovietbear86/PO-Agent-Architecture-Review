# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_131_POST_FIX_AB_CONTINUATION`

## Owner fixes under test
Owner commits:
- `c1fdf2ff31072661dcfabce9ab7248fee5aa355e` — preserve live REAL AS21 assignee source selector.
- `786bb079b3dafb3a72c366768aa84418fc0c3f91` — expose normalized `task_keys` in composite capability result.
- `c2c6135cb691f25a4fc4b1beac45f586b9a8dda6` — approved product spaces are grounded independently of whether the local/general task scan currently contains tasks in those spaces.

Assignment 130 proved the direct live facade and generic Garanin Agent path are correct: independent Oracle B found 16 tasks, direct live facade returned the same 16, and Agent case `Задачи Гаранина` returned the same 16. It also proved two blockers now fixed by the owner: missing `task_keys` propagation and needless clarification for approved DMS/OLP spaces.

## Role boundary
You are QA/test executor only. Do NOT modify production/backend/frontend code, prompts, skills, adapters, Task API, MCP-SWTR, team configuration, AS21 data, test rules, or this file. Commit/push only QA artifacts under `po-agent-platform-v2/qa_reports/`.

## Absolute anti-surrogate rules
- NO task sync or local DB population.
- NO local DB/cache as Agent truth or Oracle truth.
- NO fake/mock/frozen fixtures as truth.
- NO copied historical task counts/keys as current Oracle.
- NO Harness/Agent result as Oracle B.
- NO AS21 writes.
- Exact business facts must match independent REAL AS21 Oracle B.
- For task collections exact task-key-set equality is mandatory.
- If Oracle B cannot be independently proven, verdict is `ORACLE_NOT_PROVEN`, never PASS.

Approved task spaces globally: `WMB, STS, OLP, DMS, CRPV`.

## Retry / timing policy
- timeout >=120 sec per source request;
- heavy operations may use 180 sec;
- retry transient timeout/5xx up to 2 times;
- 20–30 sec backoff;
- sequential execution / concurrency=1.

# PHASE 0 — exact provenance and clean runtime
1. Pull `feat/core8-real-query-hardening-v2`.
2. Record exact HEAD and prove all three owner commits above are ancestors.
3. Record `git status --porcelain`; do not alter pre-existing dirty files.
4. Stop old Harness/Task API processes, prove ports free, start both from current HEAD, record new PIDs/start times/commands.
5. Verify Harness, Task API, MCP-SWTR and REAL AS21 health.
6. fake/mock/frozen/local-sync authoritative use = 0; AS21 writes = 0.

# PHASE 1 — fresh independent Oracle B
Rebuild current truth from scratch; do not copy Assignment 130 counts/keys.

For `Garanin.R.V` use independent REAL AS21:
`search_users -> unique externalId -> find_units_by_filter(assigned_to=externalId) -> complete pagination`.
Capture exact all/DMS/OLP task-key sets and source evidence.

# PHASE 2 — direct live facade
Recheck:
- assignee=Garanin.R.V
- assignee=Garanin.R.V + space=DMS
- assignee=Garanin.R.V + space=OLP

Each exact key set must equal the independent Oracle subset.

# PHASE 3 — rerun the previously blocked Agent gate
Fresh session per query:
1. `Задачи Гаранина`
2. `Задачи Гаранина в DMS`
3. `Задачи Гаранина в OLP`

For every case capture status, semantic intent, grounded slots, capability args, downstream route, `data.task_keys`, `data.tasks[].key`, evidence IDs/source, answer, elapsed.

Required:
- `data.task_keys` exists and exactly equals `data.tasks[].key` as a set;
- Agent generic == fresh Oracle all;
- Agent DMS == fresh Oracle DMS;
- Agent OLP == fresh Oracle OLP;
- DMS/OLP MUST NOT produce product clarification merely because the general scan lacks those spaces;
- live REAL AS21 assignee route must remain in use.

If Phase 3 fails, STOP and identify FIRST_FAILING_BOUNDARY with last-correct/first-incorrect artifacts.

# PHASE 4 — generalized second-member control
Only after Phase 3 GREEN.
Build a fresh independent Oracle for `Kalachanov.V.V` using the same REAL AS21 method. Report actual current distribution across approved spaces; assume nothing from prior reports.

Fresh Agent query: `Задачи Калачанова`.
Require exact key equality.

If the Oracle member has tasks in at least one approved space, additionally query that real space explicitly and require exact subset equality with no needless space clarification.

# PHASE 5 — status and combined filters
Only after Phases 3–4 GREEN.
Discover REAL statuses from current source data. Test at least:
- Garanin + one real non-zero DMS status;
- Garanin + one real non-zero OLP status;
- second member + one real status in a real space where tasks exist.

Build Oracle by complete independent assignee retrieval and deterministic filtering. Require exact Agent key sets.

# PHASE 6 — sprint/task-search targeted regression
Revalidate real sprint candidates before use. Test source-backed cases for:
- sprint only;
- assignee + sprint;
- sprint + status;
- assignee + space;
- assignee + space + status;
- correction turn where status changes while member/space survives;
- at least two exact task lookups;
- nonexistent task must not hallucinate.

Exact-key A/B equality for every task collection.

# PHASE 7 — dialogue regression guards
Verify Russian response for Russian input, no invented sprint, no unauthorized member substitution, no unnecessary approved-space clarification, no correction-loop trap, and preservation of unaffected slots across correction.

# PHASE 8 — Learning Loop deep smoke
Verify observable correction/feedback lifecycle and generalized-policy safety without inventing or promoting entity facts. If an API is intentionally unavailable, classify precisely rather than fabricate evidence.

# PHASE 9 — latency sample
Measure exact lookup, generic Garanin, Garanin DMS, one sprint, one status, one clarification/correction. Separate Agent overhead from REAL AS21 latency where possible.

# PHASE 10 — 54-skill regression
ONLY if Phases 1–9 are GREEN enough to make the broad run meaningful.
Run all 54 implemented skills sequentially against production paths. Use REAL AS21 where contract requires source facts and independent Oracle B wherever factual comparison is possible. No surrogate truth. Counts must sum exactly to 54.

# PHASE 11 — FIRST_FAILING_BOUNDARY
Use earliest evidence-backed boundary, including:
`SEMANTIC_INTERPRETATION`, `MEMBER_IDENTITY_RESOLUTION`, `SPACE_GROUNDING`, `STATUS_GROUNDING`, `SKILL_RESOLUTION`, `CAPABILITY_ARGUMENT_BUILDING`, `TASK_API_ADAPTER`, `MCP_TOOL_SELECTION`, `SOURCE_QUERY_CONSTRUCTION`, `SOURCE_RESPONSE_DECODING`, `POST_SOURCE_FILTERING`, `CAPABILITY_RESULT_PROPAGATION`, `RESPONSE_STATUS_MAPPING`, `RESPONSE_RENDERING`, `LEARNING_POLICY_APPLICATION`, `QA_HARNESS_ORACLE_DEFECT`.
Always show LAST_CORRECT_ARTIFACT and FIRST_INCORRECT_ARTIFACT.

# PHASE 12 — anti-surrogate audit
Report exact HEAD, owner commits present, old/new PIDs, source health, Oracle method, exact-key comparisons, REAL AS21 reads, retries/timeouts, local DB/sync authoritative reads=0, fake/mock/frozen authoritative reads=0, AS21 writes=0, and 54-skill arithmetic if Phase 10 runs.

## Allowed final verdicts
- `FOCUSED_GATE_GREEN_FULL_REGRESSION_GREEN`
- `TASK_KEY_PROPAGATION_DEFECT`
- `SPACE_GROUNDING_DEFECT`
- `FOCUSED_ASSIGNEE_GATE_DEFECT`
- `STATUS_OR_COMBINATION_DEFECT`
- `DIALOGUE_REGRESSION_PROVEN`
- `LEARNING_LOOP_REGRESSION_PROVEN`
- `LATENCY_REGRESSION_PROVEN`
- `FULL_REGRESSION_PRODUCT_DEFECTS_PROVEN`
- `MIXED_PRODUCT_SOURCE_AND_QA_DEFECTS`
- `BLOCKED_BY_ENVIRONMENT`
- `ORACLE_NOT_PROVEN`

## Output
Primary report:
`po-agent-platform-v2/qa_reports/POST_FIX_AB_CONTINUATION_131.md`

Optional raw evidence prefix:
`POST_FIX_AB_CONTINUATION_131_`

## Finish
Commit/push ONLY QA report/raw evidence. Production code must remain untouched. Provide report path, full SHA, verdict and STOP.

## Start when instructed
Execute Assignment 131 autonomously and strictly as written.