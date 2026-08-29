# Assignment 072 — CORE8 Semantic Slot Owner Fix Certification

## Goal
Certify the owner/developer semantic-slot and correction fixes after Assignment 071. This is a focused live certification, not another diagnostic archaeology cycle.

## Role
QA/tester only.

Do NOT modify production code, prompts, tests, fixtures, credentials, wrappers, runtime configuration or AS21/SWTR data. Do not repair failures. Commit only the QA report and STOP.

## Owner fixes under test
The tested HEAD must contain these owner commits as ancestors:
- `167c44615a40d628863739729b5c65dddf91747c` — query-aware semantic recovery; preserves existing slots; current literal constraints replace stale correction state; removes unproven todo->open hardcode.
- `ae2ba4ee7cb4be749a6e113319cd40eddaf546a4` — authoritative person-login re-grounding from person_raw/real identities.
- `cadb692bcece9f047e86630267345eb3457a25ab` — focused recovery regression tests.

A1 from 071 is intentionally retained. A2 is reimplemented more narrowly: recovery is driven by explicit constraints present in the current user query, not by a blanket requirement that person/product/status must all exist. A3 is intentionally removed: status business semantics must be grounded downstream, not guessed by the surface parser.

## Phase 0 — Preflight
1. Fetch/pull `feat/core8-real-query-hardening-v2`; record START_HEAD.
2. Prove all three owner commits above are ancestors of tested HEAD.
3. Prove clean working tree before QA output.
4. Start fresh/current-checkout PO Agent and Task API processes.
5. Run runtime freshness preflight.
6. Run SWTR health guard. Positive live certification must use REAL AS21/SWTR only.
7. Record HTTP/service health and runtime PIDs/provenance.

If freshness or SWTR health fails, classify the environment precisely and STOP. Do not mutate environment/config to make the test pass.

## Phase A — Focused automated tests
Run at minimum:
- `po-agent-platform-v2/tests/test_semantic_slot_recovery.py`
- semantic core tests relevant to slot contract
- semantic frame boundary tests relevant to slot preservation
- any existing correction-runtime tests that cover SemanticCorrectionRuntimeV2

Report pass/fail counts and distinguish proven pre-existing failures from new failures. Do not weaken expectations.

## Phase B — Real AS21 semantic probes ×3
Use independent sessions for each repetition. Verify final semantic frame AND real-source result/clarification behavior. Required probes:

B1. Person only: `Покажи задачи Гаранина`
- person_raw preserved;
- member_login/assignee grounded from real/configured identity, never arbitrary prose.

B2. Explicit sprint only: `Покажи задачи в DMS-SPRNT-2`
- sprint_id preserved;
- no unnecessary semantic recovery broadening.

B3. Exact task: `Покажи задачу DMS-273`
- exact task route remains intact.

B4. Status only: `Покажи задачи со статусом todo`
- status_raw = literal `todo`;
- surface parser MUST NOT invent `status_semantic=open`;
- downstream AS21/domain grounding may canonicalize status only if supported by source/domain evidence. Record what actually happens.

B5. Multi-filter: `Покажи задачи Гаранина в DMS-SPRNT-2 со статусом todo`
- person + sprint + status all survive simultaneously;
- source execution remains bounded by all proven constraints.

B6. Cross-space
Run at least one accessible non-DMS real-space query. Prefer OLP; if unavailable, use WMB/CRPV/STS with source evidence. Do not label a token as product/sprint/space unless AS21 proves that interpretation.

B7. Anti-hallucination negative control
Use an invented/unproven person/space/sprint value and prove the system fails closed/clarifies instead of inventing an AS21 ID or broadening the query.

## Phase C — Genuine correction ×3 — mandatory gate
In the SAME session per repetition:
1. `Покажи задачи Гаранина в DMS-SPRNT-2 со статусом todo`
2. correction/current request: `Покажи задачи Гаранина в DMS-SPRNT-2 со статусом in progress`

Required invariants after turn 2:
- person_raw remains Гаранина;
- sprint_id remains DMS-SPRNT-2;
- status_raw is `in progress` (not stale `todo`);
- member_login/assignee is the authoritative grounded identity, NOT the full query text;
- no unrelated slot is corrupted;
- no fake/mock source usage;
- if the status cannot be grounded in AS21, fail closed/clarify while preserving the requested literal; do not silently substitute another status.

Run 3 independent sessions. Any repeat failure => RED.

## Phase D — Decision gate
GREEN requires ALL of the following:
- focused recovery tests pass;
- all required explicit semantic constraints in B/C pass (100%, no 32/36-style aggregate ambiguity);
- correction invariants pass 3/3;
- anti-hallucination PASS;
- HTTP_500_COUNT = 0;
- FAKE_MOCK_SOURCE_CALLS = 0;
- no new product regression;
- fresh runtime + SWTR health PASS.

If GREEN set `READY_FOR_060_FULL_RERUN = YES`.
Otherwise set NO, report FIRST_FAILING_BOUNDARY with concrete evidence, and STOP.

## Report
Create only:
`qa_reports/CORE8_SEMANTIC_SLOT_OWNER_FIX_CERTIFICATION_072.md`

Required summary:
- START_HEAD + ancestor proof;
- runtime/SWTR preflight;
- automated test counts;
- B1-B7 matrix ×3;
- explicit constraint ledger with PASS/FAIL per expected constraint;
- status raw-vs-grounded semantics evidence;
- correction trace ×3;
- member_login corruption regression verdict;
- HTTP 500 count;
- fake/mock source calls;
- new regressions count;
- READY_FOR_060_FULL_RERUN YES/NO;
- FINAL_VERDICT GREEN/RED;
- report commit SHA.

STOP. Do not start Assignment 060/062/073 automatically.