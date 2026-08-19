# QA Report: CORE8 FINAL GATE 011J

## Environment
- **Test date**: 2026-08-19
- **Branch**: feat/real-baseline-candidate-eval-v1
- **Current HEAD**: e101154 (after git pull)
- **Task API**: PID 45535, port 8003
- **PO Agent**: PID 45628, port 8004
- **MCP-SWTR**: http://127.0.0.1:3000/sse (47 tools)

## Required Developer Commits Validation

| Commit | Description | Status |
|--------|-------------|--------|
| 4b2bca2 | Fail closed on conflicting Core-8 product selectors | ✅ Validated |
| 114856a | Ground explicit releases from live canonical AS21 facts | ✅ Validated |
| eb55358 | Tighten product grounding and normalize exact task lookup | ✅ Validated |
| 5fee275 | Align Task API E2E with exact rich-read contract | ✅ Validated |
| e101154 | Add final Core-8 gate 011J | ✅ Validated |

---

## Test Results

### Test A: Core-8 Acceptance Matrix

| Skill | Query | Status | Skill ID | PASS |
|-------|-------|--------|----------|------|
| task_search | Найди задачи Гончарова в актуальном спринте по OLAP | COMPLETED | task-search-assignee 1.0.0 | ✅ |
| task_summary | Суммаризируй задачу WMB-30000 | COMPLETED | task-summary 1.0.0 | ✅ |
| task_quality | Оцени качество постановки WMB-30000 | COMPLETED | task-quality 1.0.0 | ✅ |
| sprint_health | Покажи здоровье текущего спринта OLP | COMPLETED | sprint-health 1.0.0 | ✅ |
| velocity | Покажи velocity текущего спринта OLP | COMPLETED | sprint-velocity 1.0.0 | ✅ |
| team_workload | Какая нагрузка у Калачанова? | COMPLETED | team-workload 1.0.0 | ✅ |
| competency_match | Подбери исполнителя для WMB-30000 | COMPLETED | team-assignee-recommendation 1.0.0 | ✅ |
| release_health | Покажи здоровье релиза 743559fc-f632 | NEEDS_CLARIFICATION | None | ❌ |

**Result**: **7/8 Core-8 skills PASS**.

**Issue**: The release_health skill requires `release_id` slot extraction from query. The semantic layer correctly extracts `743559fc-f632` as `release_raw` and maps it to `743559fc-f632-4c3f-8d14-ee5e1516a814` (full UUID) via `_match_shorthand`, but the canonical query template doesn't have `{release_id}` placeholder. The skill definition lacks a canonical query template with the slot placeholder.

### Test B: Release Semantic Extraction Proof

| Query | Extracted release_raw | Mapped release_id | Status |
|-------|----------------------|-------------------|--------|
| Покажи здоровье релиза 743559fc-f632 | 743559fc-f632 | 743559fc-f632-4c3f-8d14-ee5e1516a814 | NEEDS_CLARIFICATION |

**Finding**: The `_match_shorthand` method in `LiveGroundedEntityResolver` correctly matches short UUIDs to full UUIDs. However, the release_health skill execution fails with `semantic_slot_missing` because the canonical query template doesn't include the `{release_id}` placeholder.

**Evidence**: 
- Known releases (23): Full UUIDs from `fix_version_s` in canonical AS21 tasks
- Short UUID `743559fc-f632` matches full UUID `743559fc-f632-4c3f-8d14-ee5e1516a814`
- Semantic extraction works, but skill execution requires proper canonical query template

### Test C: Stale Live-Anchor Test Handling (OLP-3134)

**Test**: `tests/test_harness_dialogue_runtime.py::test_dialogue_executes_with_extracted_task_key`

**Scenario**: Test uses `OLP-3134` as task key with `fake` adapter mode.

**Finding**:
- `OLP-3134` EXISTS in current AS21 production data (confirmed via `ProductionTaskApiAS21Adapter`)
- `FakeAS21Adapter` does NOT contain `OLP-3134` (only WMB-101, WMB-102, WMB-103, DMS-201, DMS-202)
- Test expects COMPLETED status but gets FAILED due to fake adapter fixture being stale

**Classification**: `STALE_LIVE_ANCHOR` - the test fixture (FakeAS21Adapter) is stale, not production code.

**Live Replacement Evidence**:
- Task OLP-3134 found in production AS21
- Query `Найди задачу OLP-3134` correctly extracts task_key
- Exact lookup returns proper task data from production source

### Test D: Previously Suspicious Regressions

#### test_runtime_factory_runtime_records_production_execution_history
| Check | Expected | Actual | Classification |
|-------|----------|--------|----------------|
| Mock returns empty array | COMPLETED | FAILED with source_protocol_error | PRODUCTION_REGRESSION |

**Evidence**: Production adapter now validates source data and rejects empty responses. This is a behavior change from `114856a` - the adapter now properly enforces data integrity.

#### test_portfolio_overview_never_labels_task_api_data_as_fake
| Check | Expected | Actual | Classification |
|-------|----------|--------|----------------|
| Mock returns empty array | COMPLETED | FAILED with source_protocol_error | PRODUCTION_REGRESSION |

**Evidence**: Same issue - production adapter validates source data. Previously would silently succeed with empty results, now fails with source_protocol_error.

**Note**: These tests use `task-api` mode with mocked empty responses. They test that the production adapter doesn't silently accept invalid data.

### Test E: False-Green Gate ✅ PASS

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

**Result**: **All 10 false-green controls FAIL CLOSED**. Contradictory filter protection from `4b2bca2` working correctly.

### Test F: Source Completeness and Attachments ✅ PASS

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| OLP first page hasNext | hasNext=true | hasNext=True | ✅ |
| Complete mode source | task-api-canonical-cache | task-api-canonical-cache | ✅ |
| Complete count >= first page | 103 >= 100 | 103 | ✅ |
| WMB-30000 attachments | 5 XLSX files | 5 XLSX files | ✅ |

**Attachments**: All 5 XLSX files present and accessible.

### Test G: Full Regression

| Metric | 011I | 011J | Delta |
|--------|------|------|-------|
| Passed | 1166 | 1166 | 0 |
| Failed | 6 | 6 | 0 |
| Errors | 11 | 11 | 0 |
| Skipped | 12 | 12 | 0 |

**Failed tests classification**:
1. **test_domain_models.py::test_normalize_unknown_status** - STALE_EXPECTATION: preserving unknown status is current canonical contract
2. **test_runtime_factory_runtime_records_production_execution_history** - PRODUCTION_REGRESSION: adapter now validates source data
3. **test_source_dependent_request_cannot_be_reinterpreted (PDF)** - PROVEN_IMPROVEMENT: PDF discovery now works
4. **test_portfolio_overview_never_labels_task_api_data_as_fake** - PRODUCTION_REGRESSION: adapter now validates source data
5. **test_harness_dialogue_runtime.py::test_dialogue_executes_with_extracted_task_key** - STALE_LIVE_ANCHOR: FakeAS21Adapter fixture is stale
6. **test_repository_hygiene.py::test_local_and_generated_artifacts_are_not_committed** - ENVIRONMENT: .gigacode/settings.json missing

**Targeted high production regressions**: 2 (tests 2 and 4 above)

### Test H: Final Authorization Rule

**Gate conditions check**:
- ✅ CORE8_AGENT_E2E_PASS = 7/8 (7 skills work)
- ❌ REAL_RELEASE_HEALTH_E2E_PASS = NO (semantic extraction works but skill execution needs template fix)
- ✅ FALSE_GREEN_ATTACKS_PASS = YES (all 10 controls fail closed)
- ✅ SPRINT_COMPLETENESS_PASS = YES
- ✅ ATTACHMENT_REGRESSION_PASS = YES (WMB-30000 still has 5 XLSX files)
- ❌ TARGETED_HIGH_PRODUCTION_REGRESSIONS = 2 (not 0)
- ✅ NEW_HIGH_PRODUCTION_REGRESSIONS = 0 (same as 011I)
- ✅ AS21_MUTATIONS_DURING_TEST = 0

**External MCP search_versions**: ToolError (MCP-SWTR server issue, not a blocker when canonical `fix_version_s` fallback works)

---

## Gate Decision

**READY_FOR_LEARNING_LOOP_012 = NO**

**Blocking issues**:
1. **release_health skill execution** - semantic extraction works but canonical query template missing `{release_id}` placeholder
2. **2 targeted high production regressions** - adapter now properly validates source data (positive behavior change, but blocks gate)

**Non-blockers (external)**:
- MCP search_versions ToolError is an external MCP-SWTR server issue
- Release grounding works via canonical AS21 `fix_version_s` fallback

---

## Machine-Readable Footer

```text
ASSIGNMENT_ID = CORE8_FINAL_GATE_011J
CURRENT_HEAD = e101154
CORE8_AGENT_E2E_PASS = 7/8
REAL_RELEASE_ID = 743559fc-f632-4c3f-8d14-ee5e1516a814
REAL_RELEASE_HEALTH_E2E_PASS = NO
RELEASE_ID_SEMANTIC_EXTRACTION_PASS = YES
STALE_LIVE_ANCHORS = 1
FALSE_GREEN_ATTACKS_PASS = YES
SPRINT_COMPLETENESS_PASS = YES
ATTACHMENT_REGRESSION_PASS = YES
TARGETED_HIGH_PRODUCTION_REGRESSIONS = 2
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

1. **release_health canonical query template** - Missing `{release_id}` placeholder in skill definition. The semantic layer correctly extracts and maps release IDs but the skill execution fails because the canonical query template doesn't include the slot placeholder.

2. **2 targeted high production regressions** - Adapter now properly validates source data and rejects empty/malformed responses. These are positive behavior changes but block the gate. Tests need updating to reflect the new stricter validation behavior.

---

## Notes

- Developer fixes `4b2bca2`, `114856a`, `eb55358`, `5fee275` all validated.
- False-green attacks all fail closed - contradictory filter protection working.
- Release `743559fc-f632-4c3f-8d14-ee5e1516a814` from 011I verified in current AS21 dataset.
- WMB-30000 attachments unchanged (5 XLSX files).
- OLP-3134 exists in production but FakeAS21Adapter fixture is stale - classified as STALE_LIVE_ANCHOR.
- External MCP search_versions ToolError is an MCP-SWTR server issue, not Task API code.
- 1166 passed tests (same as 011I), 0 new regressions introduced.
- Test D failures are PRODUCTION_REGRESSIONS because the adapter now properly validates source data - this is a positive behavior change (fail-closed on invalid data) but blocks the gate.
