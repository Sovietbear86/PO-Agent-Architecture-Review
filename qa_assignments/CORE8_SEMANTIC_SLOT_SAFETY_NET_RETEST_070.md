# Assignment 070 — CORE8 Semantic Slot Safety-Net Retest

## Purpose

Verify the second production fix for the deterministic empty-slot failure discovered by Assignments 060/068/069.

Assignment 069 proved that both the primary semantic LLM and the dedicated recovery LLM can repeatedly return empty/invalid slot structures in the real runtime. The owner/developer therefore added a deterministic **literal surface safety-net** that preserves explicit user constraints without resolving or inventing AS21 entities.

This assignment is QA-only.

Do not modify production code, prompts, tests, wrappers, credentials, runtime configuration, AS21/SWTR data or expectations.

## Production fixes under test

Required ancestors of tested HEAD:

- `88d602ff006bb5b3af4c3ca5c157a52055f43620` — bounded LLM recovery pass
- `b9f46a1353c10ec93efe1381508ec5201c452e6d` — deterministic literal semantic-slot safety-net
- `d2cd375a7c3763a2e051ae583128127636687fdb` — targeted safety-net regression tests

The second fix intentionally does **not** contain team-member lists, product lists, AS21 IDs or source facts. It recognizes request syntax, preserves literal spans and leaves source/entity grounding downstream.

## Preconditions

1. Fetch/pull `feat/core8-real-query-hardening-v2`.
2. Record `START_HEAD`.
3. Prove all three commits above are ancestors of tested HEAD.
4. Working tree must be clean before QA artifacts.
5. Start fresh/current-checkout PO Agent and Task API processes.
6. Prove runtime/module provenance.
7. Run existing runtime freshness + SWTR health preflight.
8. If preflight fails, classify environment failure and STOP.

## Phase A — Targeted automated regression

Run at minimum:

- `po-agent-platform-v2/tests/test_semantic_slot_recovery.py`
- the semantic/core harness test suite used by Assignment 069
- task-search related harness tests
- genuine-correction focused tests

Required:

- new safety-net tests PASS;
- no new product regression;
- no test expectation weakening.

Report exact passed/failed/skipped counts.

## Phase B — Real AS21 semantic probes

Use the real `/api/v1/query` path and REAL AS21/SWTR data only.

No fake/mock positive source answers.

For each applicable query record:

- status
- intent
- semantic frame / slots
- source grounding evidence
- final result correctness
- warnings
- HTTP status

Run each semantic probe **3 times with independent sessions**.

### B1 — Person

`Покажи задачи Гаранина`

Required semantic evidence:

- `intent = task_search`
- `person_raw = Гаранина`
- no invented `member_login` before downstream grounding

### B2 — Product/space

`Покажи задачи в DMS`

Required:

- `product = DMS`

### B3 — Status

`Покажи задачи со статусом todo`

Required:

- `status_raw = todo`

### B4 — Multi-filter

`Покажи задачи Гаранина в DMS со статусом todo`

Required:

- `person_raw = Гаранина`
- `product = DMS`
- `status_raw = todo`
- all independent filters preserved simultaneously

### B5 — Sprint + person + status

Use a currently valid real DMS sprint known to the environment. Prefer `DMS-SPRNT-2` if still valid.

Example:

`Покажи задачи Гаранина в DMS-SPRNT-2 со статусом todo`

Required:

- person preserved
- exact sprint ID preserved structurally
- status preserved
- sprint token must not also be misclassified as product

### B6 — Exact task lookup non-regression

Use `DMS-273` and one additional known real task.

Required:

- exact task lookup behavior unchanged
- no task-key corruption by safety-net

### B7 — Cross-space genericity

Use at least two additional live spaces available to the current account, preferring from:

- OLP
- WMB
- CRPV
- STS

Use the same natural product-space syntax, e.g. `Покажи задачи в OLP`.

Required:

- space token is preserved without product-specific code changes
- result is grounded in live AS21

If a named space is inaccessible in the current source, classify only that probe as source-unavailable; do not fabricate data.

## Phase C — Genuine correction control

Run one real dialogue where the first request has explicit task filters and the second message genuinely changes one semantic constraint.

Required:

- correction recognized as correction;
- unchanged constraints retained;
- corrected constraint replaces only the intended value;
- recovery safety-net does not overwrite conversation correction state;
- real-source recheck is grounded.

This control is mandatory because the latest 067 report did not certify it.

## Phase D — Safety / anti-hallucination controls

Verify:

1. Unmarked free text does not create person/product/status slots merely because words are capitalized.
2. A hallucinated value from recovery LLM that is absent from the original request is not accepted.
3. Explicit sprint/task structural IDs remain authoritative.
4. No AS21 login/ID is invented by deterministic recovery.
5. No fake/mock source call is used for positive live certification.

## Phase E — Decision gate

Return `GREEN` only if:

- all targeted automated tests expected to pass are green;
- all required accessible semantic probes preserve their explicit filters;
- required 3x repetitions are stable;
- multi-filter query retains every independent constraint;
- genuine correction passes;
- HTTP 500 count = 0;
- fake/mock source calls = 0;
- no new product regression is found.

If any semantic slot still disappears, return `RED_PRODUCT_DEFECT`, identify the first proven failing boundary and STOP.

Do not fix it.

## Required report

Create only:

`qa_reports/CORE8_SEMANTIC_SLOT_SAFETY_NET_RETEST_070.md`

Report at minimum:

- `START_HEAD`
- ancestor proof for 88d602f / b9f46a1 / d2cd375
- fresh-process/current-checkout proof
- SWTR health verdict
- automated test counts
- each Phase B probe × 3 outcomes
- semantic slot PASS/FAIL count
- cross-space results
- genuine-correction verdict
- anti-hallucination verdict
- HTTP 500 count
- fake/mock source call count
- new product regressions count
- `READY_FOR_060_FULL_RERUN = YES/NO`
- final `070_VERDICT`

Commit/push only the permitted QA report and STOP.

Do not start Assignment 060, 062 or any later assignment automatically.