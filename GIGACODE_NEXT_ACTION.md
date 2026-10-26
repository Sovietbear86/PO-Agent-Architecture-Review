# GigaCode — NEXT ACTION

## A230R3.3-R2 — Independent RED remediation QA

**QA ONLY:** Do not modify source, tests, Core, configs, Git history, source data, or Public. Do not commit or merge. Fetch exact remote HEAD, compare local/remote and test THAT revision in isolated environment. STOP at first newly introduced RED and report. Freeze Core V4 six files vs checkpoint `6fb335d`.

### Previous failure evidence (2026-10-26)
- Test defect: `test_member_sprint_scope_explanation.py` referred to `CapabilitySpecV4.capability_id`, actual model field is `id`. Fixed at owner commit `0fe502f`.
- Source semantic mismatch: `sprint.time_spent` returned 147.5h **within sprint calendar**, but natural-language question asked **all time on sprint tasks**. QA REAL AS21 oracle: 33 current tasks (prior 34 drift), 660.5h / 86 entries across all dates; 147.5h /20 entries within dates; 513h/66 entries outside. Garanin himself had 0h in sprint dates, but 160h outside. Do not assume current numbers fixed: query actual source and note drift.
- Additive repair in `time_accounting_aggregate.py` at `2a40f22`: explicitly identify calendar scope in `sprint.time_spent` and `team.time_spent`, add `time_basis`, `all_time_total=false`, `outside_period_included=false`, `complete=true`, and block explicit lifetime wording in capability arguments with typed clarification instead of returning sprint hours as lifetime.
- New tests `test_sprint_aggregate_scope_guard.py` at `07b9c27`. Existing period parser changes remain intact.

### QA gates
1. Exact TESTED_HEAD and Core hash 6/6. Diff limited to the small additive plugin/test changes since previous A230R3.3 test.
2. Targeted tests: `test_member_sprint_scope_explanation.py`, `test_sprint_aggregate_scope_guard.py`, `test_member_worklogs_period.py`; verify test discovery and expected 3+ acceptance cases. Check Python syntax, no test/test-fixture bug. Validate `CapabilitySpecV4.id` and ability to instantiate tests. On RED report exact first failing line, no code changes.
3. Source contract: verify `sprint.time_spent` and `team.time_spent` preserve all existing keys/results; date-scope explanation must explicitly exclude outside-period worklogs. Utilization policy and original source aggregation unchanged.
4. LIVE two distinct intents (controlled test sessions, bounded REAL AS21):
   - **A** «Сколько списал Гаранин в период спринта DMS-SPRNT-5?» → within-period only, evidence-backed with explicit dates.
   - **B** «Сколько всего часов было списано по задачам DMS-SPRNT-5 за всё время?» → MUST NOT label 147.5h as lifetime. A typed unsupported/clarification with explanation is acceptable until an approved complete bounded all-date capability exists. A real complete all-date oracle is also acceptable ONLY with proven complete pagination, task membership and provenance. If LLM planner omits lifetime semantics from capability arguments, determine first planner/completion boundary, RED and do not edit frozen Core.
5. Revalidate 33/34 membership drift, author/date scope, 0h Garanin within vs 160h outside from a fresh independent AS21 oracle; never hardcode old counts.
6. No fake zeros during errors, missing duration/pagination must fail closed. Previous relative period forms still pass. Full V4 regression, Task API SWTR regression, frontend build. Classify pre-existing service/LLM failures separately.
7. Report case matrix and exact GREEN/RED, source oracle totals and boundaries, first failing boundary, test counts, Core 6/6, verified `TESTED_HEAD`. Chat only; STOP. **Do not begin A230R3.4 UI or Public skills QA in this task.**

### Short command
Run A230R3.3-R2 from GIGACODE_NEXT_ACTION.md against up-to-date remote HEAD. QA-only; no fixes, no commits; report and stop.
