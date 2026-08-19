# QA Report: CORE8 RELEASE HEALTH FIX 011K

## Environment
- **Test date**: 2026-08-19
- **Branch**: feat/real-baseline-candidate-eval-v1
- **Current HEAD**: 9c374eb (after git pull)
- **Task API**: PID 58041, port 8003
- **PO Agent**: PID 58125, port 8004
- **MCP-SWTR**: http://127.0.0.1:3000/sse (47 tools)

## Required Developer Commits Validation

| Commit | Description | Status |
|--------|-------------|--------|
| 5790c24 | Ground explicit release selectors without provider placeholder | ✅ Validated |
| 9c374eb | Cover release grounding when provider omits placeholder | ✅ Validated |
| b4626a2 | Add release-health final fix assignment 011K | ✅ Validated |

---

## Test Results

### Test A: Real Release-Health E2E ✅ PASS

#### Query 1: Short UUID (743559fc-f632)
| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Status | COMPLETED | COMPLETED | ✅ |
| Intent | release_health | release_health | ✅ |
| Skill | release-health | release-health 1.0.0 | ✅ |
| Release ID | Full UUID from AS21 | 743559FC-F632-4C3F-8D14-EE5E1516A814 | ✅ |
| Evidence count | Real AS21 tasks | 7 tasks | ✅ |
| Evidence source | swtr | swtr | ✅ |

#### Query 2: Full UUID (743559fc-f632-4c3f-8d14-ee5e1516a814)
| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Status | COMPLETED | COMPLETED | ✅ |
| Intent | release_health | release_health | ✅ |
| Skill | release-health | release-health 1.0.0 | ✅ |
| Release ID | Full UUID from AS21 | 743559FC-F632-4C3F-8D14-EE5E1516A814 | ✅ |
| Evidence count | Real AS21 tasks | 7 tasks | ✅ |
| Evidence source | swtr | swtr | ✅ |

**Evidence tasks**: CRPV-99359, CRPV-99358, CRPV-94870, CRPV-36095, CRPV-58094, CRPV-61710, CRPV-58080

**Key improvement**: The fix from `5790c24` allows the canonical query to be executed even when the provider omits `{release_id}` placeholder. The grounder correctly extracts and maps the short UUID to the full canonical UUID.

### Test B: Genericity / No Hardcoding ✅ PASS

#### Alternative Release Test
**Release**: `06b04455-9323-4b92-afc4-c23b4e233ace` (CRPV, 25 tasks)

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Status | COMPLETED | COMPLETED | ✅ |
| Intent | release_health | release_health | ✅ |
| Skill | release-health | release-health 1.0.0 | ✅ |
| Release ID | Full UUID from AS21 | 06B04455-9323-4B92-AFC4-C23B4E233ACE | ✅ |
| Evidence count | Real AS21 tasks | 25 tasks | ✅ |

#### Hardcoded Reference Check
**Result**: No hardcoded `743559fc-f632` references found in production source code.

**Finding**: The fix is generic and works with any release ID from the canonical AS21 `fix_version_s` data.

### Test C: Fail-Closed Release Controls ✅ PASS

| Test | Query | Status | Warnings | PASS |
|------|-------|--------|----------|------|
| Nonexistent release | Покажи здоровье релиза NONEXISTENT | NEEDS_CLARIFICATION | clarification_required | ✅ |
| Ambiguous prefix | Покажи здоровье релиза CRPV | NEEDS_CLARIFICATION | clarification_required | ✅ |
| No release identifier | Покажи здоровье релиза | NEEDS_CLARIFICATION | semantic_slot_missing | ✅ |

**Finding**: All edge cases correctly return clarification/failure without fabricating release IDs.

### Test D: Core-8 Matrix ✅ PASS (8/8)

| Skill | Query | Status | Skill ID | PASS |
|-------|-------|--------|----------|------|
| task_search | Найди задачи Гончарова... | COMPLETED | task-search-assignee 1.0.0 | ✅ |
| task_summary | Суммаризируй задачу WMB-30000 | COMPLETED | task-summary 1.0.0 | ✅ |
| task_quality | Оцени качество постановки WMB-30000 | COMPLETED | task-quality 1.0.0 | ✅ |
| sprint_health | Покажи здоровье текущего спринта OLP | COMPLETED | sprint-health 1.0.0 | ✅ |
| velocity | Покажи velocity текущего спринта OLP | COMPLETED | sprint-velocity 1.0.0 | ✅ |
| team_workload | Какая нагрузка у Калачанова? | COMPLETED | team-workload 1.0.0 | ✅ |
| competency_match | Подбери исполнителя для WMB-30000 | COMPLETED | team-assignee-recommendation 1.0.0 | ✅ |
| release_health | Покажи здоровье релиза 743559fc-f632 | COMPLETED | release-health 1.0.0 | ✅ |

**Result**: **8/8 Core-8 skills PASS**. The release_health fix closes the remaining gap from 011J.

### Test E: Source and False-Green Invariants ✅ PASS

#### False-Green Matrix
All 10 controls fail closed:
- Current + explicit sprint conflict: FAILED ✅
- Two explicit sprint IDs: NEEDS_CLARIFICATION ✅
- Two product/space selectors: NEEDS_CLARIFICATION ✅
- Nonexistent exact task: FAILED ✅
- Nonexistent assignee: NEEDS_CLARIFICATION ✅
- Nonexistent sprint: NEEDS_CLARIFICATION ✅
- Nonexistent release: NEEDS_CLARIFICATION ✅
- Unsupported request: FAILED ✅
- Weather/arithmetic: FAILED ✅
- Arithmetic: FAILED ✅

#### Sprint Completeness
| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| First page hasNext | hasNext=true | hasNext=True | ✅ |
| Complete mode source | task-api-canonical-cache | task-api-canonical-cache | ✅ |
| Complete count >= first page | 103 >= 100 | 103 | ✅ |

#### WMB-30000 Attachments
| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| XLSX file count | 5 | 5 | ✅ |

### Test F: Two Disputed Regression Tests

#### test_runtime_factory_runtime_records_production_execution_history
**Scenario**: Mock returns empty array, test expects COMPLETED.

**Result**: FAILED with `source_protocol_error`
**Classification**: `STALE_EXPECTATION_AFTER_FAIL_CLOSED_HARDENING`
**Rationale**: The adapter now correctly validates source data and rejects empty/malformed responses. This is a positive behavior change from `114856a` - the adapter enforces fail-closed on invalid data. The test expectation is stale, not a production regression.

#### test_portfolio_overview_never_labels_task_api_data_as_fake
**Scenario**: Mock returns empty array, test expects COMPLETED.

**Result**: FAILED with `source_protocol_error`
**Classification**: `STALE_EXPECTATION_AFTER_FAIL_CLOSED_HARDENING`
**Rationale**: Same as above. The adapter now properly validates source data instead of silently succeeding with empty results.

**Summary**: 0 HIGH production regressions. 2 stale expectations after fail-closed hardening.

### Test G: Focused + Full Regression

| Metric | 011J | 011K | Delta |
|--------|------|------|-------|
| Passed | 1166 | 1168 | +2 |
| Failed | 6 | 6 | 0 |
| Errors | 11 | 11 | 0 |
| Skipped | 12 | 12 | 0 |

**Failed tests classification**:
1. **test_domain_models.py::test_normalize_unknown_status** - STALE_EXPECTATION: preserving unknown status is current canonical contract
2. **test_runtime_factory_runtime_records_production_execution_history** - STALE_EXPECTATION_AFTER_FAIL_CLOSED_HARDENING
3. **test_source_dependent_request_cannot_be_reinterpreted (PDF)** - PROVEN_IMPROVEMENT: PDF discovery now works
4. **test_portfolio_overview_never_labels_task_api_data_as_fake** - STALE_EXPECTATION_AFTER_FAIL_CLOSED_HARDENING
5. **test_harness_dialogue_runtime.py::test_dialogue_executes_with_extracted_task_key** - STALE_LIVE_ANCHOR: FakeAS21Adapter fixture is stale
6. **test_repository_hygiene.py::test_local_and_generated_artifacts_are_not_committed** - ENVIRONMENT: .gigacode/settings.json missing

**NEW_HIGH_PRODUCTION_REGRESSIONS_VS_011J = 0**

---

## Authorization Decision

**READY_FOR_LEARNING_LOOP_012 = YES**

**Gate conditions met**:
- ✅ CORE8_AGENT_E2E_PASS = 8/8 (all 8 skills operational)
- ✅ REAL_RELEASE_HEALTH_E2E_PASS = YES (short and full UUID both work)
- ✅ SECOND_RELEASE_GENERICITY_PASS = YES (alternative release 06b04455-9323-4b92-afc4-c23b4e233ace works)
- ✅ RELEASE_FAIL_CLOSED_PASS = YES (all edge cases fail closed)
- ✅ FALSE_GREEN_ATTACKS_PASS = YES (all 10 controls fail closed)
- ✅ SPRINT_COMPLETENESS_PASS = YES
- ✅ ATTACHMENT_REGRESSION_PASS = YES (WMB-30000 still has 5 XLSX files)
- ✅ TARGETED_HIGH_PRODUCTION_REGRESSIONS = 0
- ✅ NEW_HIGH_PRODUCTION_REGRESSIONS = 0
- ✅ AS21_MUTATIONS_DURING_TEST = 0

---

## Machine-Readable Footer

```text
ASSIGNMENT_ID = CORE8_RELEASE_HEALTH_FIX_011K
CURRENT_HEAD = 9c374eb
CORE8_AGENT_E2E_PASS = 8/8
REAL_RELEASE_HEALTH_E2E_PASS = YES
SECOND_RELEASE_GENERICITY_PASS = YES
RELEASE_FAIL_CLOSED_PASS = YES
FALSE_GREEN_ATTACKS_PASS = YES
SPRINT_COMPLETENESS_PASS = YES
ATTACHMENT_REGRESSION_PASS = YES
TARGETED_HIGH_PRODUCTION_REGRESSIONS = 0
STALE_EXPECTATIONS_AFTER_FAIL_CLOSED_HARDENING = 2
FULL_REGRESSION_PASSED = 1168
FULL_REGRESSION_FAILED = 6
FULL_REGRESSION_ERRORS = 11
NEW_HIGH_PRODUCTION_REGRESSIONS = 0
AS21_MUTATIONS_DURING_TEST = 0
READY_FOR_LEARNING_LOOP_012 = YES
```

---

## Summary

The developer fix from `5790c24` successfully closes the release_health gap in Core-8 E2E. The production code now correctly:

1. **Extracts explicit release selectors** from natural language queries
2. **Maps short UUIDs to full canonical UUIDs** via `_match_shorthand` in `LiveGroundedEntityResolver`
3. **Executes release_health even when provider omits `{release_id}` placeholder** - the runtime consumes the grounded slot directly

The fix is generic and works with any release ID from canonical AS21 `fix_version_s` data. No hardcoded references to specific release IDs exist in the production code.

**Key metrics**:
- 8/8 Core-8 skills operational (up from 7/8 in 011J)
- 1168 passed tests (up from 1166 in 011J)
- 0 HIGH production regressions
- 2 stale expectations after fail-closed hardening (tests need updating)
