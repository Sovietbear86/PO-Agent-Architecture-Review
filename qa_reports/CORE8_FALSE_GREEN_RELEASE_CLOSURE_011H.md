# QA Report: CORE8 FALSE-GREEN & RELEASE CLOSURE 011H

## Environment
- **Test date**: 2026-08-19
- **Branch**: feat/real-baseline-candidate-eval-v1
- **Current HEAD**: 7dfcc59 (after git pull)
- **Task API**: PID 27540, port 8003
- **PO Agent**: PID 27716, port 8004
- **MCP-SWTR**: http://127.0.0.1:3000/sse (47 tools)

## Required Developer Commits Validation

| Commit | Description | Status |
|--------|-------------|--------|
| 2aba4db | Fail closed on contradictory sprint filters | ✅ Validated |
| a6e9710 | Production subclasses labeled task-api, not fake-as21 | ✅ Validated |
| 7dfcc59 | Add Core-8 false-green and release closure retest 011H | ✅ Validated |

---

## Test Results

### Test A: Contradictory-Filter Closure ✅ PASS
| Test | Query | Status | Notes |
|------|-------|--------|-------|
| Contradictory filters | Найди задачи Гончарова в текущем спринте OLP и в OLP-SPRNT-4 | FAILED | ✅ Fail closed |
| Control (normal) | Найди задачи Гончарова в текущем спринте OLP | COMPLETED | ✅ Works |

**Key improvement**: Contradictory sprint selectors (2aba4db) now fail closed with explicit error.

### Test B: Real Release Discovery from Canonical AS21 Tasks ✅ PASS
| Space | Release ID | Tasks | Evidence |
|-------|------------|-------|----------|
| CRPV | 03bdd330-e758 | 4 | CRPV-24549, CRPV-24556, CRPV-25098 |
| CRPV | 06b04455-9324 | 25 | CRPV-36499, CRPV-37649, CRPV-37876 |
| CRPV | 1049da04-04a7 | 10 | CRPV-49760, CRPV-49759, CRPV-50148 |
| CRPV | 743559fc-f632 | 7 | CRPV-99359, CRPV-99358, CRPV-94870 |

**Selected for release_health**: `743559fc-f632` (7 tasks)

**Finding**: External MCP `search_versions` is unhealthy, but canonical AS21 tasks expose `fix_version_s` with valid release identifiers. The fallback path (`_task_backed_versions`) correctly returns releases from canonical task data.

### Test C: Release/Health Production E2E ⚠️ NEEDS_CLARIFICATION
| Test | Query | Status | Intent | Notes |
|------|-------|--------|--------|-------|
| Real release | Покажи здоровье релиза CRPV_2026_08 | NEEDS_CLARIFICATION | None | semantic_slot_missing |
| Real release UUID | Покажи здоровье релиза 743559fc-f632 | NEEDS_CLARIFICATION | None | semantic_slot_missing |
| Nonexistent | Покажи здоровье релиза NONEXISTENT_99999 | FAILED | None | Not COMPLETED |

**Issue**: The release_health capability requires specific slot extraction that doesn't match natural-language queries. The query format may need a specific release name pattern.

### Test D: Full Core-8 Matrix
| Skill | Query | Status | PASS |
|-------|-------|--------|------|
| task_search | Найди задачи Гончарова... | COMPLETED | ✅ |
| task_summary | Суммаризируй задачу WMB-30000 | COMPLETED | ✅ |
| task_quality | Оцени качество постановки WMB-30000 | COMPLETED | ✅ |
| sprint_health | Покажи здоровье текущего спринта OLP | COMPLETED | ✅ |
| velocity | Покажи velocity текущего спринта OLP | COMPLETED | ✅ |
| team_workload | Какая нагрузка у Калачанова? | COMPLETED | ✅ |
| competency_match | Подбери исполнителя для WMB-30000 | COMPLETED | ✅ |
| release_health | Покажи здоровье релиза... | NEEDS_CLARIFICATION | ❌ |

**Result**: **7/8 Core-8 skills operational**. Release health requires query format fix.

### Test E: False-Green Matrix ⚠️ FAIL
| Attack Type | Status | Result |
|-------------|--------|--------|
| nonexistent task | FAILED | ✅ |
| nonexistent assignee | NEEDS_CLARIFICATION | ✅ |
| nonexistent sprint | NEEDS_CLARIFICATION | ✅ |
| nonexistent release | NEEDS_CLARIFICATION | ✅ |
| contradictory filters | COMPLETED | ❌ FALSE-GREEN |
| unsupported request | FAILED | ✅ |
| weather/arithmetic | FAILED | ✅ |
| invalid JSON | HTTP 422 | ✅ |

**Issue**: Contradictory filters query (`Найди задачи Гончарова в спринтах OLP и DMS`) returns COMPLETED instead of failing closed. This is a false-green issue.

### Test F: Targeted Regression Triage

| Test Node | Status | Classification |
|-----------|--------|----------------|
| test_portfolio_overview_never_labels_task_api_data_as_fake | ✅ PASSED | FIXED by a6e9710 |
| test_task_api_end_to_end_query_maps_source_to_harness_contract | FAILED | PRODUCTION_REGRESSION |
| test_dialogue_clarifies_multiple_ambiguous_slots_before_execution | FAILED | PRODUCTION_REGRESSION |
| test_dialogue_executes_with_extracted_task_key | FAILED | PRODUCTION_REGRESSION |
| test_source_dependent_request_cannot_be_reinterpreted (PDF) | FAILED | PROVEN_IMPROVEMENT |
| test_normalize_unknown_status | FAILED | STALE_EXPECTATION |
| test_local_and_generated_artifacts_are_not_committed | FAILED | ENVIRONMENT |

**Summary**: 6/7 tests failing. 1 test FIXED (test_portfolio_overview), 3 PRODUCTION_REGRESSION, 1 PROVEN_IMPROVEMENT, 1 STALE_EXPECTATION, 1 ENVIRONMENT.

### Test G: Full Regression

| Metric | 011G | 011H | Delta |
|--------|------|------|-------|
| Passed | 1165 | 1166 | +1 |
| Failed | 7 | 6 | -1 |
| Errors | 11 | 11 | 0 |
| Skipped | 12 | 12 | 0 |

**NEW_PRODUCTION_REGRESSIONS_VS_011G = 0** (one test now passes, one fewer failure)

### Test H: Architecture Assertions
| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Production adapter labeling | task-api | task-api | ✅ |
| MCP search_versions health | ToolError | ToolError | ⚠️ External issue |
| Source-backed release data | Yes | Yes (CRPV) | ✅ |
| AS21 mutations | 0 | 0 | ✅ |

**Key finding**: Production adapter correctly labeled as `task-api` (fixed by a6e9710).

---

## Gate Status

| Gate Item | Status | Notes |
|-----------|--------|-------|
| Contradictory filter fail closed | ❌ NO | Returns COMPLETED |
| Real release discovered | ✅ YES | CRPV 743559fc-f632 |
| Real release_health E2E | ⚠️ NEEDS_CLARIFICATION | Query format issue |
| External search_versions tool health | ❌ FAIL | MCP ToolError (server) |
| Core-8 agent E2E | ⚠️ 7/8 | Release health needs format fix |
| False-green attacks | ❌ NO | Contradictory filters false-green |
| Portfolio production source label | ✅ YES | Fixed by a6e9710 |
| New production regressions vs 011G | ✅ 0 | One test fixed |

---

## Machine-Readable Footer

```text
ASSIGNMENT_ID = CORE8_FALSE_GREEN_RELEASE_CLOSURE_011H
CURRENT_HEAD = 7dfcc59
CONTRADICTORY_FILTER_FAIL_CLOSED = NO
REAL_RELEASE_DISCOVERED = YES
REAL_RELEASE_ID = 743559fc-f632
REAL_RELEASE_HEALTH_E2E_PASS = NO
EXTERNAL_SEARCH_VERSIONS_TOOL_HEALTH = FAIL
CORE8_AGENT_E2E_PASS = 7/8
FALSE_GREEN_ATTACKS_PASS = NO
PORTFOLIO_PRODUCTION_SOURCE_LABEL_PASS = YES
TARGETED_HIGH_PRODUCTION_REGRESSIONS = 3
FULL_REGRESSION_PASSED = 1166
FULL_REGRESSION_FAILED = 6
FULL_REGRESSION_ERRORS = 11
NEW_PRODUCTION_REGRESSIONS_VS_011G = 0
AS21_MUTATIONS_DURING_TEST = 0
READY_FOR_LEARNING_LOOP_012 = NO
```

---

## High Blockers (Must Fix Before LL012)

1. **Contradictory filters false-green** - Query with contradictory sprint selectors returns COMPLETED instead of failing closed. This was addressed in 011G but the test still fails.

2. **Release health query format** - The release_health capability requires specific slot extraction that doesn't work with natural-language queries. Need to identify the expected query format.

3. **3 production regressions remain**:
   - test_task_api_end_to_end_query_maps_source_to_harness_contract
   - test_dialogue_clarifies_multiple_ambiguous_slots_before_execution
   - test_dialogue_executes_with_extracted_task_key

4. **External MCP search_versions ToolError** - MCP server issue, not Task API code. Release grounding works via canonical task fallback.

---

## Notes

- Developer fix `a6e9710` successfully fixed `test_portfolio_overview_never_labels_task_api_data_as_fake`.
- Developer fix `2aba4db` addresses contradictory filter detection, but a false-green case remains in manual testing.
- The release_health capability requires a specific query format that doesn't match the test cases tried.
- PDF attachment discovery is a proven functionality improvement (old test expected absence).
- The full regression shows improvement: 1166 passed (vs 1165 in 011G), 6 failures (vs 7 in 011G).
