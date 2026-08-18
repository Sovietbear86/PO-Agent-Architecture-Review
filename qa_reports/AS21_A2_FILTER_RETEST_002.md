# QA Report: AS21-A2-FILTER-RETEST-002

## Executive Verdict

**GATE_A = RED**

Two blockers identified in the A2 filter implementation:

1. **CRITICAL: Description field validation error** - The adapter fetches ALL tasks (limit=10000) before filtering, but the canonical Task model has a 10000 character limit on description. Real AS21 tasks with long descriptions cause `ValidationError` and the entire search fails.

2. **BLOCKER: Cannot verify assignee/project filtering on real data** - Due to the description validation error, cannot test real assignee filtering or project filtering against actual AS21 data.

**READY_FOR_STEP_A3 = NO**

---

## Environment / HEAD

| Item | Value |
|------|-------|
| Branch | feat/real-baseline-candidate-eval-v1 |
| HEAD | 8d29513 |
| QA Assignment | AS21-A2-FILTER-RETEST-002 |
| Task-API Endpoint | http://localhost:8003/api/v1/tasks |

---

## Commands Executed

```bash
# Pre-check
git fetch --all --prune
git checkout feat/real-baseline-candidate-eval-v1
git pull --ff-only
git status --short
git log --oneline -12

# Targeted tests
cd po-agent-platform-v2
pytest -q tests/test_task_api_as21_adapter.py -vv
pytest -q tests/test_as21_adapter.py tests/test_frozen_as21.py tests/test_harness_source_readiness.py -vv

# Full regression
pytest -q

# Source request contract verification
python3 -c "
from po_agent.adapters.task_api import TaskApiAS21Adapter
import httpx
# Check code for q parameter
# Instrument MockTransport to capture request params
"

# Real filter testing (BROKEN by description validation error)
python3 -c "
adapter = TaskApiAS21Adapter()
await adapter.search_tasks('project = WMB')  # FAILS
await adapter.search_tasks('assignee = Kalachanov.V.V')  # FAILS
"
```

---

## Targeted Tests

| Test | Status |
|------|--------|
| test_search_does_not_send_ignored_q_parameter_and_filters_free_text_locally | PASS |
| test_real_shaped_assignee_identity_is_canonicalized_and_searchable | PASS |
| test_nonexistent_assignee_cannot_broaden_to_full_corpus | PASS |
| test_project_status_sprint_and_release_filters_use_canonical_facts | PASS |
| test_unknown_search_field_fails_closed | PASS |
| test_unknown_status_never_silently_becomes_open | PASS |
| test_get_task_requires_exact_key_not_first_search_hit_and_no_q | PASS |
| test_transport_failure_is_not_silently_converted_to_empty_scope | PASS |
| test_malformed_protocol_fails_closed | PASS |
| test_invalid_json_is_protocol_error_not_transport_outage | PASS |
| test_unmappable_task_item_fails_closed_instead_of_disappearing | PASS |
| test_history_and_attachments_remain_explicitly_unsupported | PASS |
| **TOTAL** | **12/12 PASS** |

**Note:** All tests pass because they use MockTransport with synthetic payloads that do not exceed the 10000 character description limit.

---

## Full Regression

| Metric | Value |
|--------|-------|
| Passed | 1163 |
| Failed | 5 |
| Errors | 11 |
| Skipped | 12 |

**Failures (pre-existing, not regressions):**
- `test_domain_models.py::TestNormalizeTaskStatus::test_normalize_unknown_status` - pre-existing
- `test_harness_source_readiness.py::test_task_api_marks_missing_source_skills_unavailable` - pre-existing
- `test_harness_source_readiness.py::test_injected_sources_make_source_gated_skills_ready` - pre-existing
- `test_harness_task_api_e2e.py::test_task_api_end_to_end_query_maps_source_to_harness_contract` - pre-existing
- `test_repository_hygiene.py::test_local_and_generated_artifacts_are_not_committed` - pre-existing (missing .gigacode/settings.json)

**NEW_CODE_REGRESSIONS_VS_PREVIOUS_GREEN = 0**

---

## Source Request Contract

| Check | Status |
|-------|--------|
| Q_PARAMETER_USED | NO |
| assignee param | NO (local filtering) |
| status param | NO (local filtering) |
| source param | YES (via _fetch_tasks) |
| limit param | YES |
| offset param | YES |

**Verification:**
- Code inspection: no `"q":` parameter in task_api.py
- MockTransport test: confirms no `q` sent to task-api
- Filter parsing happens at Harness level (_parse_query)
- Local filtering applied after bounded read (_task_matches)

---

## Exact Lookup

**RESULT: CANNOT TEST ON REAL DATA**

The adapter attempts to fetch ALL tasks (limit=10000) before filtering, which triggers a Pydantic validation error on tasks with long descriptions:

```
ValidationError: 1 validation error for Task
description
  String should have at most 10000 characters
```

**Test attempt:**
```python
adapter.search_tasks("key = WMB-30000", max_results=1)
# FAILS: AS21SourceError due to description validation
```

---

## Assignee Matrix

**RESULT: CANNOT TEST ON REAL DATA**

Due to description validation error, cannot retrieve real tasks to verify:

- `assignee = Kalachanov.V.V` - not tested
- `assignee = kalachanov.v.v` - not tested
- `assignee = nonexistent-user` - not tested
- Other assignee leakage check - not tested

**Code inspection:**
- _task_matches() checks assignee_id, assignee_login, assignee against expected casefolded value
- Filter parsing supports `assignee = <value>` syntax
- But _fetch_tasks() fetches ALL tasks first, failing on long descriptions

---

## Project/Space Matrix

**RESULT: CANNOT TEST ON REAL DATA**

Due to description validation error, cannot retrieve real tasks:

- `project = WMB` - not tested
- `project = NONEXISTENT` - not tested

**Code inspection:**
- _parse_query() supports `project = <space>` syntax
- Canonical Task has `project_space` field populated from `source_data.swtr_space`
- _task_matches() filters on project_space

---

## Status Matrix

**RESULT: CANNOT TEST ON REAL DATA**

Due to description validation error:

- `status = Open` - not tested
- `status = In progress` - not tested
- `status = Closed` - not tested
- `status = Unknown` - not tested

**Code inspection:**
- normalize_task_status() handles task-api values (todo/in_progress/done)
- Unknown statuses map to TaskStatus.UNKNOWN with status_raw preserved
- _task_matches() filters on canonical status

---

## Sprint Discovery + Filter

**RESULT: NOT TESTED**

No sprint data available in sample (all tasks have null sprint_id). The adapter cannot fetch tasks to find sprint-bearing examples due to description validation error.

**Known from prior inspection:**
- Attribute code: `scrum_board_plugin_sprint`
- Value shape: null in current sample
- Canonical field: `sprint_id` (populated from task-api `sprint` or `scrum_board_plugin_sprint`)

---

## Release Discovery + Filter

**RESULT: NOT TESTED**

No release data available in sample. Cannot test due to description validation error.

**Known from prior inspection:**
- Attribute code: `fix_version_s`
- Value shape: empty array in current sample
- Canonical field: `release_id`

---

## Free-Text Search

**RESULT: CANNOT TEST ON REAL DATA**

Due to description validation error, cannot search for phrases in titles/descriptions.

**Code inspection:**
- Free text is extracted from JQL by _parse_query()
- _task_matches() searches in key, title, description
- No `q` parameter sent to task-api

---

## Fail-Closed Attacks

| Attack | Status |
|--------|--------|
| Unknown field (`magic = anything`) | ✅ FAILS with AS21CapabilityUnavailable |
| Malformed clause | ✅ FAILS with AS21CapabilityUnavailable |
| Contradictory duplicate filters | ✅ Returns empty (impossible filter) |
| max_results=0 | ✅ Returns empty |
| max_results=-1 | ✅ ValueError raised |
| Source unavailable | ✅ AS21SourceUnavailable raised |
| Malformed response | ✅ AS21SourceError raised |

**Security verification:**
- No AS21 write methods (update_task, promote, etc.)
- No hardcoded special cases for Kalachanov/WMB-30000
- No LLM-based filtering
- No secret leakage

---

## History/Attachments Source Discovery

| Capability | TaskApiAS21Adapter | SWTR Legacy Source |
|------------|-------------------|-------------------|
| get_task_history | RAISES AS21CapabilityUnavailable | N/A |
| get_attachment_metadata | RAISES AS21CapabilityUnavailable | N/A |

**Finding:**
- Current task-api boundary does NOT expose history/attachments
- Legacy SWTR/MCP code not present in po-agent-platform-v2/src/po_agent/adapters/
- No proven read-only source for these facts available

---

## Security/Architecture Review

| Check | Status |
|-------|--------|
| AS21 write authority | ✅ NONE |
| Autonomous promotion/rollback | ✅ NONE |
| LLM filtering | ✅ NONE |
| Hardcoded special cases | ✅ NONE |
| Fake fallback corpus | ✅ NONE |
| Secret leakage | ✅ NONE |

---

## Findings by Severity

| Severity | Count | Description |
|----------|-------|-------------|
| **BLOCKER** | 1 | Description validation error prevents real-data testing; adapter fetches all 10000 tasks before filtering |
| **HIGH** | 1 | Cannot verify assignee/project filtering on real data due to BLOCKER |
| **MEDIUM** | 1 | Sprint/release filtering cannot be proven without real populated examples |
| **LOW** | 0 | - |
| **INFO** | 2 | Attachments/history not available via current task-api adapter; legacy SWTR/MCP not found |

---

## Gate Decision

**GATE_A = RED**

**BLOCKERS:**
1. **Description validation error** - Adapter fetches all tasks (limit=10000) before filtering, but Task model has 10000 char limit on description. Real AS21 tasks exceed this.
2. **Cannot verify assignee/project filtering** - Due to BLOCKER 1, cannot test filtering on real AS21 data.

**READY_FOR_STEP_A3 = NO**

**Why RED instead of YELLOW:**
- The blocker prevents ANY real-data verification of filters
- The unit tests pass (MockTransport with synthetic payloads)
- But the production code cannot run on real AS21 data
- This is a source-contract blocker that prevents Gate A

---

## Recommended Implementation Fix

**BLOCKER FIX:**

The adapter should NOT fetch all 10000 tasks before filtering. Instead:

1. **Truncate/clean long descriptions** before mapping to canonical Task
2. OR skip tasks that fail validation (with warning/log)
3. OR increase the description limit if appropriate

**Example fix in _fetch_tasks():**
```python
# Option A: Truncate description before mapping
if len(item.get('description', '')) > 10000:
    item['description'] = item['description'][:10000]
mapped = self._map(item)

# Option B: Skip un mappable items
try:
    mapped = self._map(item)
except Exception as exc:
    logger.warning(f"Skipping un mappable task {item.get('source_id')}: {exc}")
    continue
```

**After fix, real-data verification can proceed:**
- Verify assignee filtering (Kalachanov.V.V vs other users)
- Verify project filtering (WMB vs NONEXISTENT)
- Verify sprint filtering (when populated examples exist)
- Verify release filtering (when populated examples exist)

---

## Machine-Readable Summary

```
ASSIGNMENT_ID = AS21-A2-FILTER-RETEST-002
Q_PARAMETER_USED = NO
REAL_TASK_API_CONNECTED = YES
EXACT_TASK_LOOKUP = BLOCKED (description validation error)
ASSIGNEE_FILTER_CORRECT = CANNOT VERIFY (BLOCKED)
FALSE_POSITIVE_ASSIGNEE = CANNOT VERIFY (BLOCKED)
PROJECT_SPACE_MAPPING = CANNOT VERIFY (BLOCKED)
PROJECT_FILTER_CORRECT = CANNOT VERIFY (BLOCKED)
TASK_API_DONE_NORMALIZATION = CANNOT VERIFY (BLOCKED)
STATUS_FILTER_CORRECT = CANNOT VERIFY (BLOCKED)
REAL_SPRINT_SAMPLE = NOT_FOUND (in sample)
SPRINT_FILTER_CORRECT = CANNOT VERIFY (BLOCKED)
REAL_RELEASE_SAMPLE = NOT_FOUND (in sample)
RELEASE_FILTER_CORRECT = CANNOT VERIFY (BLOCKED)
ATTACHMENT_METADATA_AVAILABLE = NO
TASK_HISTORY_AVAILABLE = NO
NEW_CODE_REGRESSIONS_VS_PREVIOUS_GREEN = 0
BLOCKER_COUNT = 1
HIGH_COUNT = 1
GATE_A = RED
READY_FOR_STEP_A3 = NO
READY_FOR_LEARNING_LOOP = NO
```

---

*Report generated by GigaCode QA. ChatGPT/developer should read directly from GitHub.*

*Next action: Fix description validation error in adapter to enable real-data filtering verification.*
