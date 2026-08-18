# GigaCode Test Instructions

> Canonical QA handoff from ChatGPT/developer to GigaCode. GigaCode is tester/adversarial reviewer only.

## Handoff protocol

1. Pull the target branch and read this file before every run.
2. Do not modify production code, existing tests, fixtures, roadmap docs, or this file.
3. The ONLY repository file you may create/update is `REPORT_PATH` below.
4. Commit and push the report to the same target branch.
5. Never commit credentials, cookies, Authorization headers, tokens, or secrets.
6. Prefer truthful RED/YELLOW/BLOCKED over false GREEN.

## Current assignment

`ASSIGNMENT_ID = AS21-A3-EXTENDED-SOURCE-DISCOVERY-004`

`TARGET_BRANCH = feat/real-baseline-candidate-eval-v1`

`REPORT_PATH = qa_reports/AS21_A3_EXTENDED_SOURCE_DISCOVERY_004.md`

Read first:
- `PO_AGENT_HARNESS_EVOLUTION_PLAN.md`
- `CORE8_AS21_SOURCE_CONTRACT.md`
- `qa_reports/AS21_A2_FILTER_RETEST_003.md`

## Context

A2 base task contract is considered functionally closed on real AS21 data:
- exact lookup works;
- assignee externalId/login filtering works;
- project filtering/intersection works;
- status/free-text works;
- no ignored `q`;
- no false-positive assignee;
- long descriptions do not break mapping.

Do NOT spend this assignment re-proving A2 except as a short smoke/regression.

A3 must discover the richer source contracts needed by Core-8 analytical/task-intelligence skills.

Important architecture already found in repository:
- `task-api/app/services/swtr_sync_service.py` invokes real MCP-SWTR read tools;
- observed tool names include `find_units`, `find_units_by_filter`, `read_unit`, `get_current_sprint` and sprint-task retrieval;
- `task-api/app/routers/swtr_sync.py` exposes read-oriented routes including `/api/v1/swtr/sprints` and `/api/v1/swtr/sprint-tasks`;
- early `SWTRAdapter` had attachment/comment model fields but initialized them empty, so that old mapper is NOT proof of an attachment source;
- historical sync code extracted `scrum_board_plugin_sprint` from full `read_unit` payloads.

Owner-provided real-data clue:
- at least one real task assigned to `Kalachanov.V.V` in space `WMB` has attachment(s).
- Discover it from the source; do not ask owner to send a screenshot/key unless deterministic discovery is impossible.

## QA rules

- READ ONLY against AS21/SWTR/MCP/task-api.
- DO NOT call sync/save/create/update/delete/comment/transition/write methods that mutate local or remote state.
- Prefer direct read-only MCP tools and GET/read methods.
- Do not modify code when a gap is found.
- Sanitize outputs; never publish token/cookie/header values or attachment contents containing sensitive data.
- For attachment discovery, metadata/structure is enough; do not download file contents unless explicitly necessary to prove a read API exists.

## Procedure

### 1. Pre-check

```bash
git fetch --all --prune
git checkout feat/real-baseline-candidate-eval-v1
git pull --ff-only
git status --short
git log --oneline -12
```

Record HEAD and clean tree.

### 2. Short A2 smoke + regression

From `po-agent-platform-v2` run the targeted adapter tests and a minimal real smoke:
- exact `WMB-30000`;
- `assignee = Kalachanov.V.V`;
- `project = WMB AND assignee = Kalachanov.V.V`;
- nonexistent assignee => 0.

Run full `pytest -q` and report `NEW_CODE_REGRESSIONS_VS_PREVIOUS_GREEN`.

### 3. Inventory real MCP-SWTR tool catalog

Locate the MCP-SWTR installation used by `SWTRSyncService` (default path is in service constructor, but verify actual local path). Initialize the MCP server read-only and call `tools/list`.

Record sanitized list of tool names/descriptions relevant to:
- task/unit read;
- task search/filter;
- sprint/current sprint/sprint tasks;
- attachments/files/resources;
- comments/activity/changelog/history;
- releases/fix versions.

Do not execute any tool whose semantics are write/mutate/create/update/delete/comment/transition.

Report machine-readable:
- `MCP_TOOL_CATALOG_AVAILABLE`
- `MCP_READ_UNIT_TOOL`
- `MCP_SPRINT_TOOLS`
- `MCP_ATTACHMENT_TOOLS`
- `MCP_HISTORY_TOOLS`
- `MCP_RELEASE_TOOLS`

### 4. Prove current sprint source

Use the existing read path, preferably both where safe:
- `GET /api/v1/swtr/sprints?space=WMB`
- underlying MCP `get_current_sprint`

Record sanitized real response shape:
- sprint id/code;
- name;
- dates/state if present;
- space;
- any other identifiers needed for deterministic lookup.

If endpoint/service errors, capture exact non-secret reason.

Report:
- `CURRENT_SPRINT_READ = PASS/FAIL/NOT_FOUND`
- `REAL_SPRINT_ID`
- `REAL_SPRINT_SOURCE_PATH`
- `REAL_SPRINT_VALUE_SHAPE`

### 5. Prove sprint-task source

If a real sprint is obtained, call the proven read-only sprint-task route/tool:
- `/api/v1/swtr/sprint-tasks?sprint_id=<REAL>&space=WMB` or the exact underlying MCP read tool.

Record:
- task count;
- bounded task keys;
- whether each returned task can be cross-checked against source sprint evidence;
- actual shape used to associate task -> sprint.

Do not use cached `/api/v1/tasks` absence as evidence that sprint source is unavailable.

Report:
- `SPRINT_TASK_READ = PASS/FAIL/NOT_FOUND`
- `SPRINT_TASK_COUNT`
- `SPRINT_TASK_RELATION_SOURCE`

### 6. Discover the known WMB attachment task assigned to Kalachanov

Start with the already-proven production adapter/filter to obtain real WMB tasks assigned to `Kalachanov.V.V`.

For each bounded candidate key, use **read-only full source read** (`read_unit` or equivalent) and inspect only structure/metadata until a task with attachment/file evidence is found.

Do not print attachment content. For the discovered task record only:
- task key;
- attachment count if available;
- where attachment metadata appears (top-level field / attribute / dedicated tool/resource);
- attachment metadata field names (id/name/contentType/size/url/etc., whichever actually exist);
- whether a dedicated read/download tool exists.

Owner says such a WMB/Kalachanov task exists; therefore search those candidates before declaring NOT_FOUND.

Report:
- `REAL_ATTACHMENT_TASK_KEY`
- `ATTACHMENT_METADATA_AVAILABLE = YES/NO`
- `ATTACHMENT_SOURCE_PATH`
- `ATTACHMENT_VALUE_SHAPE`
- `ATTACHMENT_CONTENT_READ_TOOL = <name/NONE>`

### 7. History/changelog discovery

From `tools/list`, full `read_unit` payload, and repository service code, determine whether a read-only source exists for:
- status transitions;
- activity/history/changelog;
- comments/timestamps if relevant to flow analytics.

If a read tool exists, call it on one real WMB task and record only sanitized structural fields. If none exists, explicitly report NONE.

Do not derive fake history from `created_at/updated_at/current status`.

Report:
- `TASK_HISTORY_AVAILABLE = YES/NO`
- `TASK_HISTORY_SOURCE_PATH`
- `TASK_HISTORY_VALUE_SHAPE`

### 8. Release/fix-version discovery

Use full `read_unit` on bounded real WMB tasks and tool catalog to inspect:
- `fix_version_s`;
- release/version-like fields;
- any dedicated release/version read tool.

Search more intelligently than the prior cached 200-task scan: use full source payload and, if supported, read-only filtered search/tooling.

If a populated release is found, record sanitized shape and task key. If no populated example is found, distinguish:
- attribute exists but values empty;
- no release tool exists;
- release source truly unavailable.

Report:
- `REAL_RELEASE_SAMPLE`
- `REAL_RELEASE_ATTRIBUTE_CODE`
- `REAL_RELEASE_VALUE_SHAPE`
- `RELEASE_SOURCE_PATH`

### 9. Compare early vs current source architecture

Review early commit `6b3bee08c920f5ea32083313481385eb06935b48`, especially:
- `task-api/src/s21_agent/connectors/s21_swtr_adapter.py`
- `task-api/src/s21_agent/models/task.py`

Compare with current:
- `task-api/app/services/swtr_sync_service.py`
- `task-api/app/routers/swtr_sync.py`
- `po-agent-platform-v2/src/po_agent/adapters/task_api.py`

Answer:
- which old capabilities were only model placeholders;
- which real SWTR read capabilities exist today but are not wired into Harness;
- which data should come from `/api/v1/tasks` vs richer MCP/SWTR source;
- exact recommended adapter/service boundary for Core-8.

Description only. Do not implement.

### 10. Formal Core-8 source readiness matrix

Produce a matrix for the 8 skills:

`SKILL | REQUIRED_FACT | PROVEN_SOURCE | STATUS | BLOCKING_GAP`

At minimum include:
- task search facts;
- attachment facts for summary/quality when referenced;
- sprint/current sprint/sprint tasks;
- history facts needed by sprint health/velocity formula;
- team assignee/workload facts;
- competency config (non-AS21 if appropriate);
- release/fix-version facts.

Classify each fact:
- `PROVEN_REAL`
- `PROVEN_UNAVAILABLE`
- `UNPROVEN`

Do not mark a skill GREEN merely because a synthetic unit test exists.

### 11. Security/adversarial check

Confirm all discovery calls were read-only and no:
- AS21 mutation;
- local sync/save mutation;
- autonomous learning/promotion;
- secret leakage;
- attachment content leakage;
- hardcoded task-specific behavior.

## Gate logic

A3 can be `GREEN` even if a source fact is genuinely unavailable, but only if:
- unavailability is proven;
- affected Core-8 skill behavior/formula can be explicitly marked unavailable or redesigned without fabricated facts;
- no silent fallback exists.

`READY_FOR_A4 = YES` only when the source requirements for Core-8 are sufficiently classified (`PROVEN_REAL` or `PROVEN_UNAVAILABLE`) to build a reproducible real test corpus/query pack.

`READY_FOR_LEARNING_LOOP = NO` always for this assignment.

## Report format

Create `qa_reports/AS21_A3_EXTENDED_SOURCE_DISCOVERY_004.md` with:
1. Executive verdict
2. Environment / HEAD
3. A2 smoke/regression
4. MCP tool catalog
5. Current sprint source
6. Sprint-task source
7. Attachment discovery (including discovered WMB/Kalachanov task)
8. History/changelog discovery
9. Release discovery
10. Early-vs-current architecture comparison
11. Core-8 source readiness matrix
12. Security/read-only audit
13. Findings by severity
14. Recommended next implementation (description only)
15. Gate decision

End with exactly:

```text
ASSIGNMENT_ID = AS21-A3-EXTENDED-SOURCE-DISCOVERY-004
REAL_TASK_API_CONNECTED =
A2_SMOKE =
MCP_TOOL_CATALOG_AVAILABLE =
MCP_READ_UNIT_TOOL =
MCP_SPRINT_TOOLS =
MCP_ATTACHMENT_TOOLS =
MCP_HISTORY_TOOLS =
MCP_RELEASE_TOOLS =
CURRENT_SPRINT_READ =
REAL_SPRINT_ID =
REAL_SPRINT_SOURCE_PATH =
SPRINT_TASK_READ =
SPRINT_TASK_COUNT =
REAL_ATTACHMENT_TASK_KEY =
ATTACHMENT_METADATA_AVAILABLE =
ATTACHMENT_SOURCE_PATH =
ATTACHMENT_CONTENT_READ_TOOL =
TASK_HISTORY_AVAILABLE =
TASK_HISTORY_SOURCE_PATH =
REAL_RELEASE_SAMPLE =
REAL_RELEASE_ATTRIBUTE_CODE =
RELEASE_SOURCE_PATH =
NEW_CODE_REGRESSIONS_VS_PREVIOUS_GREEN =
BLOCKER_COUNT =
HIGH_COUNT =
GATE_A =
A3 =
READY_FOR_A4 =
READY_FOR_LEARNING_LOOP = NO
```

## Publish

```bash
git add qa_reports/AS21_A3_EXTENDED_SOURCE_DISCOVERY_004.md
git commit -m 'qa: report AS21 A3 extended source discovery 004'
git push origin feat/real-baseline-candidate-eval-v1
git status --short
```

Final working tree clean. Tell the user only:

`QA report published: qa_reports/AS21_A3_EXTENDED_SOURCE_DISCOVERY_004.md`
