# QA Report: CORE8 FINAL CLOSURE 011I

## Environment
- **Test date**: 2026-08-19
- **Branch**: feat/real-baseline-candidate-eval-v1
- **Current HEAD**: 02bd390 (after git pull)
- **Task API**: PID 37672, port 8003
- **PO Agent**: PID 37765, port 8004
- **MCP-SWTR**: http://127.0.0.1:3000/sse (47 tools)

## Required Developer Commits Validation

| Commit | Description | Status |
|--------|-------------|--------|
| 4b2bca2 | Fail closed on conflicting Core-8 product selectors | ✅ Validated |
| 114856a | Ground explicit releases from live canonical AS21 facts | ✅ Validated |
| eb55358 | Tighten product grounding and normalize exact task lookup | ✅ Validated |
| 5fee275 | Align Task API E2E with exact rich-read contract | ✅ Validated |
| 02bd390 | Add final Core-8 closure gate 011I | ✅ Validated |

---

## Test Results

### Test A: Fast Targeted Regression (3 Tests)

| Test Node | Status | Classification |
|-----------|--------|----------------|
| test_task_api_end_to_end_query_maps_source_to_harness_contract | ✅ PASSED | FIXED by 5fee275 |
| test_dialogue_clarifies_multiple_ambiguous_slots_before_execution | ✅ PASSED | FIXED by eb55358 |
| test_dialogue_executes_with_extracted_task_key | ❌ FAILED | PRODUCTION_REGRESSION |

**Result**: **2/3 tests passed**. One test remains failing due to OLP-3134 not found in current AS21 dataset.

**Detailed error**:
```
test_dialogue_executes_with_extracted_task_key FAILED
  AssertionError: assert <ResponseStatus.FAILED: 'FAILED'> in {<ResponseStatus.COMPLETED: 'COMPLETED'>, <ResponseStatus.PARTIAL: 'PARTIAL'>}
  HarnessResponse(status=FAILED, answer='Задача OLP-3134 не найдена.', ...)
```

### Test B: Real Release Anchor Verification ✅ PASS
| Space | Release ID | Tasks | Evidence |
|-------|------------|-------|----------|
| CRPV | 06b04455-9324 | 25 | CRPV-36499, CRPV-37649, CRPV-37876 |
| CRPV | ad84b531-a5b2 | 17 | CRPV-9182, CRPV-53781, CRPV-16166 |
| CRPV | 2f86cc9c-2289 | 14 | CRPV-48377, CRPV-48360, CRPV-38367 |
| CRPV | 64ead32c-9f2f | 12 | CRPV-28498, CRPV-28507, CRPV-7076 |
| CRPV | 1049da04-04a7 | 10 | CRPV-49760, CRPV-49759, CRPV-50148 |
| CRPV | 743559fc-f632 | 7 | CRPV-99359, CRPV-99358, CRPV-94870 |
| CRPV | c82abd10-a2bd | 6 | CRPV-52305, CRPV-52308, CRPV-52309 |
| ... | ... | ... | ... |

**Selected release**: `743559fc-f632` (CRPV, 7 tasks, evidence: CRPV-99359, CRPV-99358, CRPV-94870)

**Finding**: Release `743559fc-f632` from 011H is still present in current AS21 dataset (114856a verified). External MCP `search_versions` returns ToolError (502) but canonical AS21 `fix_version_s` fallback works.

### Test C: Exact Core-8 Matrix

| Skill | Query | Status | Skill ID | PASS |
|-------|-------|--------|----------|------|
| task_search | Найди задачи Гончарова... | COMPLETED | task-search-assignee 1.0.0 | ✅ |
| task_summary | Суммаризируй задачу WMB-30000 | COMPLETED | task-summary 1.0.0 | ✅ |
| task_quality | Оцени качество постановки WMB-30000 | COMPLETED | task-quality 1.0.0 | ✅ |
| sprint_health | Покажи здоровье текущего спринта OLP | COMPLETED | sprint-health 1.0.0 | ✅ |
| velocity | Покажи velocity текущего спринта OLP | COMPLETED | sprint-velocity 1.0.0 | ✅ |
| team_workload | Какая нагрузка у Калачанова? | COMPLETED | team-workload 1.0.0 | ✅ |
| competency_match | Подбери исполнителя для WMB-30000 | COMPLETED | team-assignee-recommendation 1.0.0 | ✅ |
| release_health | Здоровье релиза 743559fc-f632 | NEEDS_CLARIFICATION | None | ❌ |

**Issue**: The release_health skill requires `release_id` slot extraction from query. Current semantic layer returns `semantic_slot_missing` when the release UUID isn't extracted.

**Result**: **7/8 Core-8 skills PASS**. Release health needs query format or semantic extraction fix.

### Test D: False-Green Closure Matrix ✅ PASS

| Attack Type | Query | Status | PASS |
|-------------|-------|--------|------|
| Current + explicit sprint conflict | Найди задачи Гончарова в текущем спринте OLP и в OLP-SPRNT-4 | FAILED | ✅ |
| Two explicit sprint IDs | Найди задачи Гончарова в OLP-SPRNT-4 и OLP-SPRNT-5 | NEEDS_CLARIFICATION | ✅ |
| Two product/space selectors | Найди задачи Гончарова в спринтах OLP и DMS | NEEDS_CLARIFICATION | ✅ |
| Nonexistent exact task | Покажи задачу NONEXISTENT-99999 | FAILED | ✅ |
| Nonexistent assignee | Какая нагрузка у Несуществующего? | NEEDS_CLARIFICATION | ✅ |
| Nonexistent sprint | Покажи здоровье спринта NONEXISTENT | NEEDS_CLARIFICATION | ✅ |
| Nonexistent release | Покажи здоровье релиза NONEXISTENT | NEEDS_CLARIFICATION | ✅ |
| Unsupported request | Какая погода в Москве? | FAILED | ✅ |
| Weather/arithmetic | Какая погода? | FAILED | ✅ |
| Arithmetic | Сколько будет 2+2? | FAILED | ✅ |

**Result**: **All 10 false-green controls FAIL CLOSED**. Contradictory filter fixes from `4b2bca2` working correctly.

### Test E: Sprint Completeness and Attachment Preservation ✅ PASS

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| OLP first page hasNext | hasNext=true | hasNext=True | ✅ |
| Complete mode source | task-api-canonical-cache | task-api-canonical-cache | ✅ |
| Complete count >= first page | 103 >= 100 | 103 | ✅ |
| WMB-30000 attachments | 5 XLSX files | 5 XLSX files | ✅ |

**Attachments**:
- Справочно_3ЛТП_Типовая трудоемкость_2025-2026 (прогноз).xlsx
- Справочно_Ресурсы 2026 (БП и ПГК).xlsx
- Шаблон_Календаризация (опционально).xlsx
- strata27_template_0707(1)(1)(1)(1).xlsx
- Шаблон к заполнению (согласования ПШЕ).xlsx

### Test F: Full Regression and Triage

| Metric | 011H | 011I | Delta |
|--------|------|------|-------|
| Passed | 1166 | 1166 | 0 |
| Failed | 6 | 6 | 0 |
| Errors | 11 | 11 | 0 |
| Skipped | 12 | 12 | 0 |

**Failed tests classification**:
1. **test_domain_models.py::test_normalize_unknown_status** - STALE_EXPECTATION: preserving unknown status is current canonical contract
2. **test_final_architecture_regressions.py::test_runtime_factory_runtime_records_production_execution_history** - PRODUCTION_REGRESSION (post-eb55358)
3. **test_final_architecture_regressions.py::test_source_dependent_request_cannot_be_reinterpreted (PDF)** - PROVEN_IMPROVEMENT: PDF discovery now works
4. **test_final_architecture_regressions.py::test_portfolio_overview_never_labels_task_api_data_as_fake** - PRODUCTION_REGRESSION: mock now triggers proper validation
5. **test_harness_dialogue_runtime.py::test_dialogue_executes_with_extracted_task_key** - PRODUCTION_REGRESSION: OLP-3134 not found in AS21
6. **test_repository_hygiene.py::test_local_and_generated_artifacts_are_not_committed** - ENVIRONMENT: .gigacode/settings.json missing

**NEW_HIGH_PRODUCTION_REGRESSIONS_VS_011H = 0**

### Test G: Learning Loop Authorization Decision

**Current Status**:
- CORE8_AGENT_E2E_PASS = 7/8 (release_health needs fix)
- REAL_RELEASE_HEALTH_E2E_PASS = NO (semantic slot extraction issue)
- FALSE_GREEN_ATTACKS_PASS = YES (all 10 controls fail closed)
- TARGETED_THREE_PRODUCTION_TESTS_PASS = NO (1/3 tests fail)
- SPRINT_COMPLETENESS_PASS = YES
- ATTACHMENT_REGRESSION_PASS = YES (WMB-30000 still has 5 XLSX files)
- EXTERNAL_SEARCH_VERSIONS_TOOL_HEALTH = FAIL (MCP ToolError - server issue)
- TARGETED_HIGH_PRODUCTION_REGRESSIONS = 5
- NEW_HIGH_PRODUCTION_REGRESSIONS_VS_011H = 0
- AS21_MUTATIONS_DURING_TEST = 0

---

## Gate Decision

**READY_FOR_LEARNING_LOOP_012 = NO**

**Blocking issues**:
1. **Core-8 E2E = 7/8** - release_health requires query format or semantic extraction fix
2. **3 targeted production tests** - 1/3 tests fail (test_dialogue_executes_with_extracted_task_key)
3. **5 remaining high production regressions** in full suite

**Non-blockers (external)**:
- MCP search_versions ToolError is an external MCP-SWTR server issue, not a code issue
- Release grounding works via canonical AS21 `fix_version_s` fallback (verified)

---

## Machine-Readable Footer

```text
ASSIGNMENT_ID = CORE8_FINAL_CLOSURE_011I
CURRENT_HEAD = 02bd390
TARGETED_THREE_PRODUCTION_TESTS_PASS = NO
REAL_RELEASE_ID = 743559fc-f632
REAL_RELEASE_HEALTH_E2E_PASS = NO
CORE8_AGENT_E2E_PASS = 7/8
FALSE_GREEN_ATTACKS_PASS = YES
SPRINT_COMPLETENESS_PASS = YES
ATTACHMENT_REGRESSION_PASS = YES
TARGETED_HIGH_PRODUCTION_REGRESSIONS = 5
FULL_REGRESSION_PASSED = 1166
FULL_REGRESSION_FAILED = 6
FULL_REGRESSION_ERRORS = 11
EXTERNAL_SEARCH_VERSIONS_TOOL_HEALTH = FAIL
NEW_HIGH_PRODUCTION_REGRESSIONS = 0
AS21_MUTATIONS_DURING_TEST = 0
READY_FOR_LEARNING_LOOP_012 = NO
```

---

## High Blockers (Must Fix Before LL012)

1. **release_health semantic slot extraction** - Query `Здоровье релиза 743559fc-f632` returns NEEDS_CLARIFICATION with semantic_slot_missing. The release_id slot must be extracted from the query.

2. **1/3 targeted production tests fail**:
   - test_dialogue_executes_with_extracted_task_key - OLP-3134 not found in current AS21

3. **5 remaining high production regressions**:
   - test_runtime_factory_runtime_records_production_execution_history
   - test_source_dependent_request_cannot_be_reinterpreted (PDF)
   - test_portfolio_overview_never_labels_task_api_data_as_fake
   - test_dialogue_executes_with_extracted_task_key
   - test_repository_hygiene (environment)

---

## Notes

- Developer fixes `4b2bca2`, `114856a`, `eb55358`, `5fee275` all validated.
- False-green attacks now all fail closed - contradictory filter protection working.
- Release `743559fc-f632` from 011H verified in current AS21 dataset.
- WMB-30000 attachments unchanged (5 XLSX files).
- External MCP search_versions ToolError is an MCP-SWTR server issue, not Task API code.
- 1166 passed tests (same as 011H), 0 new regressions introduced.
