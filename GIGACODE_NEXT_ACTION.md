# GigaCode — CURRENT NEXT ACTION

## A230R3.18-R2-P31-D2-SOURCE-METADATA-GUARD-QA

**QA ONLY.** Do not edit code, tests, docs, configs, Core V4, history or AS21; no commits/pushes/merges. Preserve all user services and dirty/untracked QA reports. Fetch origin, record LOCAL_HEAD=REMOTE_HEAD=TESTED_HEAD.

### Previous failure (independent R1)
A230R3.18 R1 reported **RED** on TESTED_HEAD `4a0e4d9`: 11/11 source-contract tests, 11/11 forecast, 299 V4, frontend build 0; Task API 126 passed/25 failed (baseline categories). Adversarial 14/16: `validate_complete_sprint_collection` raised **uncaught AttributeError** on `source_data=None` and `source_data=[]` at `task-api/app/services/sprint_forecast_source.py:27`. Core 6/6 unchanged. Must fail closed via ValueError, not 500.

### Owner-only fix, unverified
- `76be926`: changes only source validator: `source_data` must be dict before querying `sprint_membership_proven`; invalid input raises `ValueError("task_sprint_membership_unproven")`.
- `4f5ae92`: adds parameterized unit test for `None`, `[]`, string, integer and boolean source_data. No production Core/API route/MCP/UI modifications.
- This is still a **pure validator**, not yet a working live forecast endpoint/Skill/UI.

### Gates
1. Integrity: compare commit delta to `4a0e4d9` — exactly source validator + targeted test + assignment; frozen Core V4 6/6 byte-identical to `6fb335d`, no undocumented data paths.
2. Focused tests `task-api/tests/test_sprint_forecast_source_contract.py`: expect original 11 + new 5 parametrizations = **16 passes**. Independently re-run all 16 prior adversarial probes: malformed source_data None/list now typed ValueError, no uncaught AttributeError, no fabricated membership.
3. Run 11 delivery forecast tests, V4 full (~299), frontend build, SWTR-read Task API and broader Task API. Compare existing 25 failures against baseline — label honestly, do not declare blanket Task API GREEN.
4. Verify source-validation contract retains exact sprint membership, no duplicate IDs, proper history completeness and authoritative status transition timestamps. No real AS21 writes, no unscope reads. Core 6/6.
5. Report first failing line if RED; else `D2_R2_GREEN` with exact TESTED_HEAD, regression totals and remaining D2 collector/adapter/plugin/UI work. QA only, no changes, STOP.

### Short command
Run A230R3.18-R2-P31-D2-SOURCE-METADATA-GUARD-QA from current Review GIGACODE_NEXT_ACTION.md. QA only: malformed source_data fail-closed, 16 contract tests, 16 adversarial, 11 forecast, full regression and Core 6/6. No code fixes/commits; report and STOP.
