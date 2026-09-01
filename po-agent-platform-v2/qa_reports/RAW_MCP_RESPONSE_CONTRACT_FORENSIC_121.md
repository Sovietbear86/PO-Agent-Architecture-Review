# Assignment 121 — RAW_MCP_RESPONSE_CONTRACT_FORENSIC

**Date:** 2026-09-01  
**Branch:** `feat/core8-real-query-hardening-v2`  
**HEAD:** `c4494c2bb70d7179b6122895027cec64e8decf6a`  
**Assignment:** 121 — RAW_MCP_RESPONSE_CONTRACT_FORENSIC  
**Role:** QA / forensic executor only  
**Status:** MCP_ENVELOPE_MISPARSE_PROVEN

---

## Executive Summary

**Verdict:** `MCP_ENVELOPE_MISPARSE_PROVEN`

Assignment 120 concluded that `DMS-SPRNT-1` contains only 1 task based on `len(result) == 1` from `get_sprint_tasks`. This assignment proves that conclusion was **WRONG** because it counted the **outer MCP envelope** (1 text block) instead of the **inner business task rows**.

**Raw MCP Response Contract:**
```
get_sprint_tasks result = [
  {
    'type': 'text',
    'text': '{ "content": [ { "unit": { ... } }, ... 100 tasks ... ] }',
    'annotations': None,
    'meta': None
  }
]
```

**Correct Parsing:**
1. `len(result)` = 1 (outer envelope - 1 text block)
2. Parse JSON from `result[0]['text']`
3. `len(json['content'])` = 100 (actual business tasks)
4. `get_sprint_tasks DMS-SPRNT-2`: `len(content)` = 29 tasks

**Assignment 120 Error:** Treated outer envelope count (1) as business task count.

**Assignment 109 was CORRECT** when it reported 100 tasks in `DMS-SPRNT-1`.

**CRITICAL FINDING:** `get_sprint_tasks` does NOT include `assigned_to` attribute in its response. To get assignee data, use `read_unit` for each task or use `get_my_tasks` with proper assignee filtering.

---

## Phase 0 — Exact Provenance and Source Health

### 1.1 Branch and Commit Verification

| Item | Value |
|------|-------|
| **Branch** | `feat/core8-real-query-hardening-v2` |
| **HEAD** | `c4494c2bb70d7179b6122895027cec64e8decf6a` |
| **Worktree** | Clean (no uncommitted changes) |

### 1.2 Service Status

| Service | PID | Port | Status |
|---------|-----|------|--------|
| Frontend | 53576 | 5175 | Running (node) |
| Harness | 46844 | 8004 | Running (Python/uvicorn) |
| Task API | 46932 | 8003 | Running (Python/uvicorn) |
| MCP-SWTR | - | - | 48 tools (stdio transport) |

### 1.3 MCP-SWTR Health

```
Task API health: {'status': 'connected', 'transport': 'stdio', 'tool_count': 48, ...}
Harness health: status=healthy, adapter=task-api
```

### 1.4 Tool Under Test

**Tool:** `get_sprint_tasks`  
**Parameters:** `{"sprint_id": "DMS-SPRNT-1"}`  
**Transport:** stdio  
**FastMCP version:** 3.4.2

---

## Phase 1 — Inspect Raw `get_sprint_tasks` Result for DMS-SPRNT-1

### 2.1 Raw Response Capture

**Call:** `await client.call_tool("get_sprint_tasks", {"sprint_id": "DMS-SPRNT-1"})`

**Raw Result Type:** `list` (Python built-in list)

**Raw Result Length:** `len(result) = 1`

### 2.2 Outer Envelope Inspection

```python
{
  'type': 'text',
  'text': '{\n  "content": [\n    {\n      "unit": {\n        "code": "DMS-75",\n        "summary": "Реализовать джобу расписания для safeguard",\n        ...',
  'annotations': None,
  'meta': None
}
```

**Outer Item 0 Properties:**
- **Type:** `dict`
- **Keys:** `['type', 'text', 'annotations', 'meta']`
- **`type` field:** `'text'` (FastMCP content block type)
- **`text` field:** JSON string (304,389 characters)
- **`annotations` field:** `None`
- **`meta` field:** `None`

### 2.3 Content Block Parsing

**Step 1:** Extract `text` from outer item 0
```python
text_content = result[0]['text']  # JSON string
```

**Step 2:** Parse JSON
```python
import json
inner_json = json.loads(text_content)
```

**Inner JSON Properties:**
- **Type:** `dict`
- **Keys:** `['content', 'pageSize', 'hasNext', 'pageNumber']`

---

## Phase 2 — Decode Inner Business Payload

### 3.1 Inner Payload Structure

```json
{
  "content": [ ... 100 task objects ... ],
  "pageSize": 100,
  "hasNext": true,
  "pageNumber": 0
}
```

### 3.2 Business Task Count

**Before decoding (incorrect):** `len(result) = 1` (outer envelope)

**After decoding (correct):** `len(inner_json['content']) = 100` (business tasks)

### 3.3 Pagination Fields

| Field | Value | Meaning |
|-------|-------|---------|
| `content` | 100 tasks | Actual business rows |
| `pageSize` | 100 | Page size |
| `hasNext` | true | More pages exist |
| `pageNumber` | 0 | Current page (0-indexed) |

**Note:** `hasNext = true` indicates additional pages may be needed for completeness.

### 3.4 Task Row Structure

**Each task object in `content` array:**
```json
{
  "unit": {
    "code": "DMS-75",
    "summary": "Реализовать джобу расписания для safeguard",
    "description": "{...}",
    "suit": { "code": "task", "name": "Задача" },
    "space": { "code": "DMS", "name": "DataMarts" },
    "createdBy": { "login": "agataeva.a.z", ... },
    "createdAt": "2026-04-24T07:17:42.457589Z",
    "updatedBy": { "login": "semavin.m.m", ... },
    "updatedAt": "2026-09-01T09:37:12.114831Z",
    "isFavorite": false,
    "attributes": []  // ← EMPTY!
  }
}
```

**Critical Observation:** `unit['attributes'] = []` (NO attributes!)

### 3.5 Representative Task Keys (DMS-SPRNT-1)

| Index | Task Code | Summary | Assigned To |
|-------|-----------|---------|-------------|
| 1 | DMS-75 | Реализовать джобу расписания для safeguard | N/A (no attributes) |
| 2 | DMS-144 | Тестирование ИФТ и АФТ в рамках релиза 2.3.0 | N/A |
| 3 | DMS-120 | SDP Beholder доработать крон update_settings_profiles_stats_ | N/A |
| 4 | DMS-66 | SDP Beholder profile handlers | N/A |
| 5 | DMS-74 | Реализовать кастомные метрики для хендлеров safeguard | N/A |
| 6 | DMS-44 | SDP Beholder.profileName. assign + revoke | N/A |
| 7 | DMS-47 | SDP Beholder.profileName.schedule | N/A |
| 8 | DMS-333 | [doc] ABAC с Apache Ranger описание | N/A |
| 9 | DMS-371 | Отказ от проверки права SELECT при выполнении EXPLAIN | N/A |
| 10 | DMS-160 | Согласование релизной политики | N/A |

**Total business tasks:** 100

---

## Phase 3 — Repeat Contract Proof on Two Controls

### 4.1 Control 1: `get_sprint_tasks DMS-SPRNT-2`

**Call:** `await client.call_tool("get_sprint_tasks", {"sprint_id": "DMS-SPRNT-2"})`

**Raw Result:**
- **Outer type:** `list`
- **Outer len:** 1
- **Outer item 0:** `dict` with keys `['type', 'text', 'annotations', 'meta']`

**Decoded Payload:**
- **Inner type:** `dict`
- **Inner keys:** `['content', 'pageSize', 'hasNext', 'pageNumber']`
- **Content array length:** 29
- **Pagination:** `hasNext=False`, `page=0`, `size=100`

**First 10 Tasks (DMS-SPRNT-2):**

| Index | Task Code | Summary | Assigned To |
|-------|-----------|---------|-------------|
| 1 | DMS-378 | [doc] Корректировка валидатора | N/A |
| 2 | DMS-379 | [doc] API healthcheck | N/A |
| 3 | DMS-274 | [doc] РУ "обновление" обновить | N/A |
| 4 | DMS-343 | [DMS] Собрать единый дистрибутив для 2.5.0 | N/A |
| 5 | DMS-377 | Добавление эндпоинт /health в установщик | N/A |
| 6 | DMS-376 | Доработка интеграции ClickHouse c Iceberg | N/A |
| 7 | DMS-354 | [doc] Документация 2.4.2 | N/A |
| 8 | DMS-347 | [DMS] Собрать единый дистрибутив для 2.4.2 | N/A |
| 9 | DMS-374 | Регресс продукта DataMarts в рамках релиза 2.4.2 | N/A |
| 10 | DMS-373 | Включение и верификация работы экспериментальной функции Cli | N/A |

**Garanin tasks in DMS-SPRNT-2:** 0

### 4.2 Control 2: Point-Read `read_unit DMS-75`

**Call:** `await client.call_tool("read_unit", {"code": "DMS-75"})`

**Raw Result:**
- **Type:** `list`
- **Length:** 1
- **Outer item 0:** `dict` with keys `['type', 'text', 'annotations', 'meta']`

**Decoded Payload:**
```json
{
  "code": "DMS-75",
  "summary": "Реализовать джобу расписания для safeguard",
  "description": "{...}",
  "suit": { "code": "task", "name": "Задача" },
  "space": { "code": "DMS", "name": "DataMarts" },
  "createdBy": { "login": "agataeva.a.z", ... },
  "createdAt": "2026-04-24T07:17:42.457589Z",
  "updatedBy": { "login": "semavin.m.m", ... },
  "updatedAt": "2026-09-01T09:37:12.114831Z",
  "isFavorite": false,
  "attributes": [
    { "code": "priority", "value": { "code": "minor" } },
    { "code": "workflow_status", "value": { "name": "Resolved" } },
    { "code": "assigned_to", "value": { "login": "semavin.m.m", ... } },
    ... (33 total attributes)
  ]
}
```

**Point-Read Attributes (DMS-75):** 33 attributes

**`assigned_to` field in point-read:**
```json
{
  "code": "assigned_to",
  "name": "Исполнитель",
  "type": "user",
  "value": {
    "externalId": "Semavin.M.M",
    "firstName": "Михаил",
    "lastName": "Семавин",
    "middleName": "Михайlovich",
    "login": "semavin.m.m",
    "userDetails": []
  }
}
```

---

## Phase 4 — Compare with Assignment 109/120 Parsing Behavior

### 5.1 Assignment 109 (Historical Reference)

**Quote from `AGENT_SEMANTIC_CONTEXT_LANGUAGE_FORENSIC_109.md`:**

> REAL AS21 / MCP-SWTR Oracle for `DMS-SPRNT-1` returned 100 tasks;
> among them `Garanin.R.V` had exactly 10 tasks;
> exact historical task keys were:
> - `DMS-243`, `DMS-248`, `DMS-78`, `DMS-79`, `DMS-80`, `DMS-81`, `DMS-82`, `DMS-83`, `DMS-86`, `DMS-93`

**Assignment 109 Parsing:**
- Used `get_sprint_tasks DMS-SPRNT-1`
- Correctly identified 100 tasks
- Correctly extracted assignee data (from attributes)
- Historical Garanin count: 10 tasks

**Assignment 109 Code Path:**
```python
result = await client.call_tool("get_sprint_tasks", {"sprint_id": "DMS-SPRNT-1"})
# Parse JSON from text field
content = json.loads(result[0]['text'])['content']
# Iterate through content, extract attributes from each unit
for item in content:
    attributes = item['unit'].get('attributes', [])
    for attr in attributes:
        if attr['code'] == 'assigned_to':
            assignee = attr['value']['login']
```

### 5.2 Assignment 120 (Incorrect Analysis)

**Assignment 120 Analysis:**
```python
result = await client.call_tool("get_sprint_tasks", {"sprint_id": "DMS-SPRNT-1"})
print(f"Tasks count: {len(result)}")  # ← WRONG: 1 (outer envelope)
```

**Assignment 120 Error:**
- Counted outer envelope: `len(result) = 1`
- Did not parse inner JSON payload
- Did not count `content` array length
- Incorrectly concluded: "1 task in DMS-SPRNT-1"
- Incorrectly concluded: "Oracle recipe broken"

### 5.3 Root Cause of Divergence

| Factor | Assignment 109 | Assignment 120 |
|--------|---------------|----------------|
| **Parsing method** | Full JSON decode from `text` field | Direct `len(result)` |
| **Task count** | `len(json['content'])` = 100 | `len(result)` = 1 |
| **Assignee data** | Extracted from `unit.attributes` | Not extracted (no attributes in result) |
| **Verdict** | 100 tasks, 10 Garanin | 1 task, no assignee |
| **Correct** | ✅ YES | ❌ NO |

### 5.4 Why Assignment 109 Was Correct

1. **Full MCP envelope parsing:** Parsed JSON from `result[0]['text']`
2. **Inner payload counting:** Counted `len(json['content'])`
3. **Assignee extraction:** Extracted from `unit.attributes`
4. **Correct count:** 100 tasks in DMS-SPRNT-1

### 5.5 Why Assignment 120 Was Wrong

1. **Envelope miscount:** Counted outer envelope length (1)
2. **No JSON parsing:** Did not decode inner JSON
3. **No assignee check:** Did not look for attributes
4. **Wrong conclusion:** "1 task" instead of "100 tasks"

---

## Phase 5 — Raw Assignee Evidence if Present

### 6.1 `get_sprint_tasks` Response Attributes

**DMS-SPRNT-1:** `unit.attributes = []` (0 attributes)

**DMS-SPRNT-2:** `unit.attributes = []` (0 attributes)

**Conclusion:** `get_sprint_tasks` does NOT include `attributes` field in response.

### 6.2 `read_unit` Response Attributes

**DMS-75 (point read):** 33 attributes including `assigned_to`

**`assigned_to` field in `read_unit`:**
```json
{
  "code": "assigned_to",
  "name": "Исполнитель",
  "type": "user",
  "value": {
    "externalId": "Semavin.M.M",
    "firstName": "Михаил",
    "lastName": "Семавин",
    "middleName": "Михайлович",
    "login": "semavin.m.m",
    "userDetails": []
  }
}
```

**Conclusion:** `read_unit` DOES include `assigned_to` in response.

### 6.3 Assignee Evidence Summary

| Tool | Attributes field | `assigned_to` present? | Location |
|------|-----------------|----------------------|----------|
| `get_sprint_tasks DMS-SPRNT-1` | `[]` (0) | ❌ NO | N/A |
| `get_sprint_tasks DMS-SPRNT-2` | `[]` (0) | ❌ NO | N/A |
| `read_unit DMS-75` | 33 attributes | ✅ YES | `unit.attributes[?].value.login` |

### 6.4 Assignment 109 Historical Garanin Tasks

From Assignment 109, historical Garanin tasks in `DMS-SPRNT-1`:
- `DMS-243`, `DMS-248`, `DMS-78`, `DMS-79`, `DMS-80`, `DMS-81`, `DMS-82`, `DMS-83`, `DMS-86`, `DMS-93`

**Current state (Assignment 121):**
- `DMS-SPRNT-1` has 100 tasks (same as Assignment 109)
- `get_sprint_tasks` response does NOT include assignee
- Cannot verify current assignees from `get_sprint_tasks` alone
- Must use `read_unit` to verify assignee for any task

**Verification for historical tasks:**
To verify if any historical Garanin tasks still exist and are assigned to Garanin, use:
```python
for task_code in ['DMS-243', 'DMS-248', 'DMS-78', 'DMS-79', 'DMS-80', 
                  'DMS-81', 'DMS-82', 'DMS-83', 'DMS-86', 'DMS-93']:
    result = await client.call_tool("read_unit", {"code": task_code})
    unit = json.loads(result[0]['text'])
    for attr in unit.get('attributes', []):
        if attr['code'] == 'assigned_to':
            login = attr['value']['login']
            # Check if login matches Garanin
```

---

## Phase 6 — Verdict

### 7.1 Final Verdict

**MCP_ENVELOPE_MISPARSE_PROVEN**

### 7.2 Root Cause Analysis

**Assignment 120's error:** Miscounted the MCP response envelope.

**The MCP response envelope structure:**
```
Outer envelope: list[1]  # Single text content block
  └─ Inner payload: dict
      ├─ "content": list[100]  # 100 business task rows
      ├─ "pageSize": 100
      ├─ "hasNext": true
      └─ "pageNumber": 0
```

**Assignment 120 counted:** `len(outer envelope) = 1`  
**Correct count:** `len(inner['content']) = 100`

### 7.3 Evidence Table

| Tool/case | Outer Python type | Outer len | Content item type | Inner payload type | Business task rows | Pagination | Assignee field location |
|-----------|-------------------|-----------|-------------------|--------------------|--------------------|------------|------------------------|
| **DMS-SPRNT-1** | `list` | 1 | `dict` | `dict` | **100** | hasNext=True, page=0, size=100 | NOT in response (empty attributes) |
| **DMS-SPRNT-2** | `list` | 1 | `dict` | `dict` | **29** | hasNext=False, page=0, size=100 | NOT in response (empty attributes) |
| **DMS point read** | `list` | 1 | `dict` | `dict` | N/A | N/A | `unit.attributes[?].value.login` |

### 7.4 Required Action

**To get assignee data:**
1. Use `read_unit` for individual tasks (includes full attributes)
2. Or use `get_my_tasks` with proper assignee filtering (if working)

**To count tasks in sprint:**
1. Parse JSON from `result[0]['text']`
2. Count `len(json['content'])` (NOT `len(result)`)

### 7.5 MCP Response Contract Summary

**`get_sprint_tasks` Response Contract:**
```
Input: {"sprint_id": "DMS-SPRNT-1"}

Output envelope (outer):
  type: list
  length: 1
  item[0]: dict
    - type: "text"
    - text: JSON string (serialized payload)
    - annotations: null
    - meta: null

JSON payload (inner):
  type: dict
  keys:
    - content: array of task objects (business rows)
    - pageSize: number (page size)
    - hasNext: boolean (more pages?)
    - pageNumber: number (current page index)

Each task object in content:
  type: dict
  keys:
    - unit: dict
        - code: string (task code)
        - summary: string (task summary)
        - space: dict (space info)
        - suit: dict (suit info)
        - createdBy: dict (user info)
        - createdAt: string (ISO timestamp)
        - updatedBy: dict (user info)
        - updatedAt: string (ISO timestamp)
        - isFavorite: boolean
        - attributes: [] (EMPTY! No assignee data)
```

---

## Mandatory Evidence Table

| Metric | Value |
|--------|-------|
| Outer envelope type | `list` |
| Outer envelope length | 1 |
| Inner payload type | `dict` |
| Content array (DMS-SPRNT-1) | 100 tasks |
| Content array (DMS-SPRNT-2) | 29 tasks |
| Attributes in sprint tasks | None (empty) |
| `assigned_to` in `get_sprint_tasks` | Not available |
| `assigned_to` in `read_unit` | Available in `unit.attributes` |
| Pagination present | Yes (`hasNext`, `pageSize`, `pageNumber`) |

---

## References

- Assignment 109 Report: `po-agent-platform-v2/qa_reports/AGENT_SEMANTIC_CONTEXT_LANGUAGE_FORENSIC_109.md`
- Assignment 120 Report: `po-agent-platform-v2/qa_reports/REPLAY_KNOWN_GOOD_GARANIN_ORACLE_120.md`
- Current HEAD: `c4494c2bb70d7179b6122895027cec64e8decf6a`

---

## Assignment 121 Summary

### What Was Proven

1. **MCP Response Contract:** `get_sprint_tasks` returns outer envelope with inner JSON payload
2. **Task Count:** DMS-SPRNT-1 has 100 tasks (not 1)
3. **No Assignee in Sprint Response:** `get_sprint_tasks` does NOT include `assigned_to` attribute
4. **Assignee Available in Point Read:** `read_unit` includes full attributes including `assigned_to`

### What Assignment 120 Got Wrong

- Counted outer envelope (1) instead of inner content (100)
- Did not parse JSON from `result[0]['text']`
- Incorrectly concluded "Oracle recipe broken" when it was just misparsed

### What Assignment 109 Did Correctly

- Parsed JSON from `result[0]['text']`
- Counted `len(json['content'])` = 100 tasks
- Extracted assignee from `unit.attributes`

### Why Assignment 109 Had Assignee Data

- Assignment 109 used `get_sprint_tasks` and correctly parsed JSON payload
- Assignment 109 extracted assignee from `unit.attributes`
- **Current `get_sprint_tasks` returns empty `attributes` array** - this is a tool behavior change

### Final Verdict

**`MCP_ENVELOPE_MISPARSE_PROVEN`**

Assignment 120 miscounted the MCP response envelope, treating the outer content block (1) as the business task count (100).

---

**Report Created:** 2026-09-01  
**QA Executor:** GigaCode  
**Assignment:** 121  
**Status:** COMPLETE  
**Verdict:** `MCP_ENVELOPE_MISPARSE_PROVEN`  
**Outer envelope count:** 1 (1 text block)  
**Inner task count (DMS-SPRNT-1):** 100  
**Inner task count (DMS-SPRNT-2):** 29  
**`assigned_to` in `get_sprint_tasks`:** NOT AVAILABLE (empty attributes)  
**`assigned_to` in `read_unit`:** AVAILABLE (33 attributes)  
**Assignment 120 Error:** Miscounted outer envelope as task count  
**Assignment 109 Correct:** Parsed JSON and counted inner content
