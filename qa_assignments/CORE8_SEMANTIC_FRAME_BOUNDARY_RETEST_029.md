# QA Assignment 029 — Core-8 Semantic Frame Boundary Retest

## Purpose
Validate the architectural remediation after 026 V2 exposed paraphrase divergence, silent filter loss and false-green task sets.

This is NOT a new benchmark. The real-data semantic acceptance criteria from Assignment 026 remain authoritative and must not be weakened or rewritten.

## Production changes under test
- two-pass LLM semantic extraction + independent constraint audit;
- structural task/sprint identifier hygiene;
- source-backed product/person/status/sprint grounding;
- no silent dropping of requested semantic constraints;
- correction turns applied against prior semantic session state instead of a synthetic combined query.

## Rules
1. GigaCode is QA only. Do not modify production code, prompts, adapters, tests, AS21 data, .env values or learning state.
2. Pull CURRENT HEAD of `feat/core8-real-query-hardening-v2` and restart Task API + PO Agent.
3. Keep restored LLM transport configuration from 027/028 locally; never commit secrets or `.env`.
4. Run focused developer regression first:
   - `po-agent-platform-v2/tests/test_semantic_core_v2.py`
   - `po-agent-platform-v2/tests/test_semantic_frame_boundary_v3.py`
   - existing explicit sprint/fail-closed tests.
5. Then rerun the SAME 026 real-data test runner V2 and its independent hydrated SWTR oracle. Do not change query wording, expected semantics or pass criteria.
6. Oracle for assignee/status must be built from sprint task keys + individual task reads, never from incomplete sprint-list attributes.
7. Compare exact task-key SET equality for factual task searches.
8. A requested constraint that disappears and broadens the result is a production FAIL even if HTTP=200.
9. `DMS-SPRNT-999999` must fail closed.
10. Corrections use the same session_id and must preserve unaffected prior filters.

## Mandatory focused invariants
For each case capture raw semantic frame BEFORE grounding, grounded frame, capability args and resulting task keys.

### A. Structural identifier integrity
- `Покажи задачи Гаранина в DMS-SPRNT-1`
- `DMS-SPRNT-1: что у Гаранина?`

Required: `sprint_id == DMS-SPRNT-1`; never the whole sentence; never `task_key=SPRNT-1`.

### B. Paraphrase invariance
Run all 8 original Section-B formulations from Assignment 026.
Required: semantically equivalent requests produce the same grounded constraint set and same exact task-key set (unless source changes during run; document if so).

### C. Multi-filter preservation
Run all original Section-C/D requests.
Required: person/product/sprint/status constraints are all present after grounding OR response is NEEDS_CLARIFICATION/FAILED. Never silently execute a broader query.

### D. Correction state
Run original Section-F scenarios.
Required: unaffected prior constraints remain identical after person/status/sprint correction. Generic recheck reopens evidence and asks targeted clarification rather than inventing new filters.

### E. False-green attacks
A response is false-green if any of the following occurs:
- expected non-empty oracle but agent returns completed empty result;
- agent returns tasks outside a requested sprint/product/person/status constraint;
- semantic frame loses a requested constraint and still executes;
- malformed structural slot reaches capability execution.

## Final metrics
Report exactly:
- `029_FOCUSED_TESTS_PASS = x/y`
- `026_FULLY_EXECUTED = YES/NO`
- `CORE8_REAL_DATA = x/8`
- `PARAPHRASE_INVARIANCE = x/8`
- `CORRECTION_LOOP = x/6`
- `MULTIFILTER_PRESERVATION = x/y`
- `STRUCTURAL_ID_INTEGRITY = x/y`
- `FALSE_GREEN_COUNT = n`
- `SILENT_SLOT_DROP_COUNT = n`
- `SEMANTIC_CRUTCH_COUNT_PRODUCTION = n`
- `HTTP_500_COUNT = n`
- `READY_TO_RERUN_017_V2 = YES/NO`

GREEN requires all semantic architecture gates relevant to 026 to pass, `FALSE_GREEN_COUNT=0`, `SILENT_SLOT_DROP_COUNT=0`, no high production regression, and full Core-8 real-data acceptance.

Publish only `qa_reports/CORE8_SEMANTIC_FRAME_BOUNDARY_RETEST_029.md` (plus machine-readable result JSON if the existing runner already produces one), commit, push, and STOP.
