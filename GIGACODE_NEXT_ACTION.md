# GigaCode — Current Action

## Status
`ACTIVE_QA_ASSIGNMENT_132_FULL_54_SKILL_AB_CERTIFICATION`

## Context
Assignment 131 proved the focused post-fix gate GREEN against fresh independent REAL AS21 Oracle B:
- `Задачи Гаранина`: 16/16 exact match;
- `Задачи Гаранина в DMS`: 8/8 exact match;
- `Задачи Гаранина в OLP`: 3/3 exact match;
- generalized second-member control `Задачи Калачанова`: exact match;
- live assignee route, `task_keys` propagation and approved-space grounding fixes were verified.

However Assignment 131 did NOT execute Phase 10, therefore its `FULL_REGRESSION_GREEN` wording is not accepted as proof of a full regression. Assignment 132 must perform the missing full certification and independently investigate two suspicious exact-task semantics from Assignment 131.

## Role boundary
You are QA/test executor only. Do NOT modify production/backend/frontend code, prompts, skills, adapters, Task API, MCP-SWTR, team configuration, AS21 data, testing rules, or this file. Commit/push only QA artifacts under `po-agent-platform-v2/qa_reports/`.

## Absolute anti-surrogate rules
- NO task sync/local DB/cache as Agent truth or Oracle truth.
- NO fake/mock/frozen fixtures as authoritative truth.
- NO historical counts/keys copied as current Oracle.
- NO Harness/Agent output reused as Oracle B.
- NO AS21 writes.
- A/B means Agent A versus independently obtained REAL AS21 Oracle B.
- For task collections exact task-key-set equality is mandatory whenever Oracle B is available.
- HTTP 200 / COMPLETED alone is never PASS if business facts mismatch.
- If Oracle cannot be independently established, classify `ORACLE_NOT_PROVEN`, not PASS.

Approved task spaces globally: `WMB, STS, OLP, DMS, CRPV`.

## Timing
REAL AS21 may be slow. Run sequentially, concurrency=1. Source timeout >=120 sec; heavy calls up to 180 sec; retry transient timeout/5xx up to 2 times with 20–30 sec backoff. Prefer resumable/checkpointed execution for the marathon.

# PHASE 0 — provenance / clean production runtime
1. Pull branch `feat/core8-real-query-hardening-v2`.
2. Record exact HEAD and `git status --porcelain`.
3. Prove owner fixes `c1fdf2f`, `786bb07`, `c2c6135` are ancestors.
4. Hard restart Task API and Harness from current HEAD; record old/new PIDs, start times and commands.
5. Verify Task API, Harness, MCP-SWTR and REAL AS21 health.
6. Record authoritative local DB/sync reads=0, fake/mock/frozen=0, AS21 writes=0.

# PHASE 1 — focused sanity gate before marathon
Do NOT spend time rebuilding all Assignment 131 evidence. Freshly prove only these three gates before the long run:
1. `Задачи Гаранина` — independent Oracle B and exact-key A/B equality.
2. `Задачи Гаранина в DMS` — independent Oracle B and exact-key A/B equality.
3. `Задачи Калачанова` — independent Oracle B and exact-key A/B equality.

If any fails, STOP marathon and identify FIRST_FAILING_BOUNDARY.

# PHASE 2 — exact-task semantics forensic
Assignment 131 contains suspicious wording: exact lookup `DMS-380` reportedly returned the full Garanin collection, and nonexistent `DMS-999999` was rendered as source unavailable. Establish the real contract, do not assume either behavior is correct.

Test at least two fresh existing REAL task IDs from approved spaces plus one guaranteed nonexistent ID.

For each existing exact ID:
- Oracle B: independently point-read the exact task from REAL AS21;
- Agent A: natural Russian exact-task query in a fresh session;
- expected task collection, if represented as a collection, must contain exactly that requested task key and no unrelated assignee collection;
- capture semantic frame, selected skill, capability args, downstream route, evidence IDs, `task_keys`, answer/status.

For nonexistent ID:
- prove source health separately in the same time window using a known-good point read;
- prove the requested ID is absent using the authoritative point-read contract;
- Agent must not hallucinate;
- distinguish semantic `NOT_FOUND` from actual `SOURCE_UNAVAILABLE` whenever the source contract allows that distinction.

If exact lookup leaks an assignee collection, classify a product defect and identify FIRST_FAILING_BOUNDARY. If nonexistent lookup is incorrectly mapped to source outage despite healthy source and authoritative not-found evidence, classify response/status-mapping defect.

# PHASE 3 — full 54-skill marathon
Run ALL 54 implemented skills. No skip is allowed merely because earlier focused phases are green.

For every skill capture at minimum:
- skill name/version;
- realistic Russian business query satisfying the skill contract;
- semantic intent/slots;
- status;
- production capability/source route;
- evidence/source type;
- normalized result facts;
- elapsed time;
- verdict.

Where the skill returns AS21-derived business facts, build independent Oracle B using the authoritative REAL AS21 route and compare the facts. For task collections compare exact task-key sets. For calculated metrics independently calculate from Oracle source inputs where possible.

Where a skill is legitimately not executable because the current REAL source lacks a required business entity/history/capability, classify precisely as `SOURCE_CAPABILITY_UNAVAILABLE_BY_DESIGN`, `SOURCE_DATA_MISSING`, or `ORACLE_NOT_PROVEN`; do not call it PASS and do not call it product FAIL without evidence.

The final matrix MUST contain exactly 54 unique implemented skills. Arithmetic across PASS/FAIL/BLOCKED-or-typed-unavailable categories MUST equal 54.

# PHASE 4 — semantic/dialogue regression pack
As part of the marathon or immediately after it, explicitly certify these historical invariants with fresh sessions:
- exact existing task ID;
- nonexistent exact task ID;
- sprint only when a valid real sprint exists;
- sprint + person when supported;
- sprint + status when supported;
- person only;
- status only when grounded;
- person + product/space + status;
- correction turn: new status replaces old while unaffected person/space slots survive;
- second-member control proving no Garanin hardcoding;
- Russian input -> Russian response;
- no unauthorized entity substitution;
- no needless DMS/OLP clarification.

# PHASE 5 — Learning Loop regression
Recheck the protected Learning Loop behavior using its actual supported runtime/API path. Do not infer GREEN from dashboard endpoints that are intentionally absent. Verify at minimum:
- correction can be observed;
- source recheck is performed where required;
- generalized policy/repair contains no memorized entity facts;
- no automatic promotion of a false rule such as `zero is impossible`;
- if persistent-policy lifecycle is part of the current supported contract, verify it through the supported path or explicitly classify why it cannot be re-certified in this environment.

# PHASE 6 — source integrity / latency
Report:
- REAL AS21 read count or auditable call evidence;
- HTTP 500/502/timeouts/retries;
- source health before/after marathon;
- fake/mock/frozen/local-sync authoritative reads=0;
- AS21 writes=0;
- latency distribution/sample for representative fast and heavy skills.

# PHASE 7 — FIRST_FAILING_BOUNDARY
For every product mismatch identify the earliest evidence-backed boundary and show LAST_CORRECT_ARTIFACT + FIRST_INCORRECT_ARTIFACT. Allowed labels include:
`SEMANTIC_INTERPRETATION`, `MEMBER_IDENTITY_RESOLUTION`, `SPACE_GROUNDING`, `STATUS_GROUNDING`, `SKILL_RESOLUTION`, `CAPABILITY_ARGUMENT_BUILDING`, `TASK_API_ADAPTER`, `MCP_TOOL_SELECTION`, `SOURCE_QUERY_CONSTRUCTION`, `SOURCE_RESPONSE_DECODING`, `POST_SOURCE_FILTERING`, `CAPABILITY_RESULT_PROPAGATION`, `RESPONSE_STATUS_MAPPING`, `RESPONSE_RENDERING`, `LEARNING_POLICY_APPLICATION`, `QA_HARNESS_ORACLE_DEFECT`.

# PHASE 8 — anti-surrogate / report integrity audit
Before final verdict verify:
- exact HEAD tested;
- clean runtime provenance and PIDs;
- 54 unique skills really executed;
- 54-skill arithmetic equals 54;
- every factual PASS has sufficient REAL-source/Oracle evidence according to its contract;
- no unresolved report placeholders such as `{data[...]}`;
- no historical counts treated as current truth;
- no Harness capability reused as independent Oracle;
- no production files changed by QA.

## Final verdict rules
Use ONE primary verdict:
- `FULL_54_SKILL_AB_CERTIFICATION_GREEN` — only if all 54 are actually executed/classified, no product defect is proven, and all required factual A/B comparisons are green;
- `FULL_REGRESSION_PRODUCT_DEFECTS_PROVEN` — one or more product defects proven;
- `EXACT_TASK_LOOKUP_REGRESSION_PROVEN`;
- `NOT_FOUND_STATUS_MAPPING_DEFECT_PROVEN`;
- `LEARNING_LOOP_REGRESSION_PROVEN`;
- `MIXED_PRODUCT_SOURCE_AND_QA_DEFECTS`;
- `BLOCKED_BY_ENVIRONMENT` — environment prevents meaningful completion;
- `ORACLE_NOT_PROVEN` — independent truth cannot be established for required certification.

Do NOT use `FULL_REGRESSION_GREEN` if the 54-skill marathon was skipped or incomplete.

## Output
Primary report:
`po-agent-platform-v2/qa_reports/FULL_54_SKILL_AB_CERTIFICATION_132.md`

Optional raw/checkpoint evidence prefix:
`FULL_54_SKILL_AB_CERTIFICATION_132_`

## Finish
Commit/push ONLY QA report and raw/checkpoint evidence under `qa_reports/`. Do not modify production code. Provide report path, full SHA, exact 54-skill arithmetic, verdict and STOP.

## Start when instructed
Execute Assignment 132 autonomously and strictly as written.