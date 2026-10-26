# GigaCode — CURRENT NEXT ACTION

## A230R3.3-R3 — Independent typed clarification / planner-gap QA

**STRICT QA ONLY.** No production changes, no test edits, no Core changes, no prompt/flags/config changes, no automatic repair, no commits or merge. Fetch remote and test exact fresh HEAD; if local dirty, STOP rather than reset. Keep frozen Core V4 byte-identical 6/6 vs checkpoint `6fb335d`.

### Why R2 RED
R2 confirmed scope guard works when a planner passes lifetime semantics to a capability, but LLM planner loses the all-time constraint entirely for natural language request «Сколько всего часов было списано по задачам DMS-SPRNT-5 за всё время?», then returns generic task-search clarification. That is **not** a source-data error; the source has 660.5h all-time vs 147.5h within dated sprint window in QA snapshot (requery for fresh oracle, counts may drift).

### Owner R3 minimal non-Core mitigation
- `po-agent-platform-v2/src/po_agent/api/v1/__init__.py`: `_guard_lifetime_sprint_scope` at API postcondition boundary. For **explicit** lifetime sprint queries, a V4 COMPLETED or generic NEEDS_CLARIFICATION without verified full all-date worklog provenance becomes a **specific typed scope clarification** saying calendar totals cannot be called lifetime. This runs after planner-response transformation and before recording pending state. It never fabricates total hours, never invokes unscoped scans, and does NOT modify LLM planner or frozen Core V4.
- New test `po-agent-platform-v2/tests/test_api_sprint_lifetime_guard.py` checks actual `DMS-SPRNT-5` form, generic planner error, no leakage of 147.5h as all-time, non-lifetime query preservation, and proven all-date output exception.
- The guard is a **conservative fail-closed mitigation**, not implementation of all-date sprint totals and not a fix of LLM planner reasoning. Do not label natural-language lifetime sum feature GREEN until an actual all-date capability exists.

### QA gates
1. Capture TESTED_HEAD; inspect exact non-Core diff; check REGEX includes both «спринта» and code `DMS-SPRNT-5`; verify it matches the explicit owner text but not normal period queries.
2. Run new tests, previous A230R3.3 tests, full V4 suite and Task API SWTR suite and frontend build. Test no accidental API response-key incompatibilities or session contamination. Check 6/6 frozen Core SHA match.
3. In isolated agent session bounded live REAL AS21, replay:
  A. «Сколько списал Гаранин в период спринта DMS-SPRNT-5?» → actual within-window result with bounds and evidence.
  B. «Сколько всего часов было списано по задачам DMS-SPRNT-5 за всё время?» → specific typed scope clarification with warning, NEVER generic status/type filters and NEVER 147.5h as all-time. No historical 660.5h returned unless source complete verified all-time scope.
  C. Ordinary unrelated task query, relative period and member.worklogs_period must stay unchanged.
4. Verify typed NEEDS_CLARIFICATION persists correctly via _remember_clarification and that «Что именно нужно уточнить?» returns actual pending scope question.
5. Negative: all-time words without sprint must NOT trigger guard; sprint period without all-time must not trigger guard; failed source status must remain failed (only V4 COMPLETED/NEEDS_CLARIFICATION transformed); evidence payload of calendar totals not displayed as facts.
6. Confirm no LIVE AS21 mutations, no unscoped scans, test counts and first failing boundary. If RED, STOP and provide exact non-Core seam. Keep Public rollout paused.

### Deliverable
Chat-only independent QA matrix, exact tested remote head, case statuses, 6/6 Core hashes, tests, source A/B, real failing boundary if any. Do not fix.

### Short command
Run A230R3.3-R3 from GIGACODE_NEXT_ACTION.md on updated remote HEAD. QA only, targeted/live A/B + regressions, no code changes; report and STOP.
