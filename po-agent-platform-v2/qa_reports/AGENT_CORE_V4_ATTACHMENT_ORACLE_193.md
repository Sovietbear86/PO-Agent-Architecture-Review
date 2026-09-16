# A193 — Agent Core V4: Attachment Oracle + Browser-C Clarification Continuity

**Assignment:** 193 — Bounded QA-only attachment-source investigation + clarification-continuity defect verification
**Verdict:** `AGENT_CORE_V4_ATTACHMENT_ORACLE_CONFIRMED_DEFECT`
**Clarification finding:** `RED_BOTH_UI_AND_BACKEND_CONTINUATION`
**Branch:** `feat/core8-real-query-hardening-v2`
**START_HEAD (post-pull):** `b649da553347782098ce890dbffcdf94fe6a834f`
**Pre-pull HEAD (A192 report):** `96f22b97a38b880a24dccfbdf776e890814d89a5`
**Date:** 2026-09-16
**Role:** QA/adversarial tester + service operator (no production/frontend/test/config modifications)
**Rollback checkpoint (unchanged):** `0f03fca14fe078c86dca961362915e10cc985401` / `checkpoint/v4-poc-green-a188`

---

## Executive summary

1. **REAL AS21 provably exposes attachments for WMB-30000** — 5 Excel files with full metadata (name, contentType, size, createdAt) via the live `get_unit_files` surface, both through the task-api route and raw MCP-SWTR. The agent's `task.search_attachments` returns **0** for the same task/space/assignee. **False REAL_EMPTY / wrong-source defect, confirmed at the live boundary.**
2. The entire Kalachanov.V.V WMB collection (5 tasks, live) contains **16 attachments across 3 tasks** (Excel, PDF, PNG). All four canonical attachment skills (#3–#6) return 0.
3. Root cause (code path, unmodified, cited): the candidate corpus of `task_search_attachments` is `adapter.search_tasks("")` → `GET /api/v1/tasks` — the **empty local synced store** — not the live SWTR read routes. The live attachment route and its mapping are healthy; the loop over the empty corpus never reaches them. Same wrong-source class as A192 `task.search_text`.
4. Second layer (single-task case A2-2): `task.lookup` loads attachments from the live route into the domain object, but the capability serializer `PortfolioCapabilities.task()` **drops the `attachments` field**, so the planner/answer layer cannot see them.
5. A192's `SOURCE_CONDITIONAL` classification for rows #3–#6 is **not sufficient**: the source surface is proven available. Rows #3–#6 are now **RED**.
6. Browser-C clarification continuation reproduces the owner's manual defect end-to-end: clicking `DMS` sends `{query: "DMS", session_id: <same>}` and the backend re-plans `DMS` as a brand-new standalone query (English generic clarification, 0 evidence). Neither the UI (sends bare token) nor the backend (no pending-clarification state, `clarification_id` null) preserves the original `Гаранин + сентябрьский спринт` constraints.
7. All three A192 defects (text search, NL assignee, status-only) still reproduce on current HEAD.

**Owner recommendation (expected):** fix the entire Task Wave source boundary together — text search + attachments + natural-language assignee + status search — **plus the clarification-continuity fix in the same bundle**, then run one consolidated QA re-gate before Wave S.

---

## Phase 0 — Services and operational keepalive

Existing project stack reused after verification (rule: healthy project process may be reused after branch/HEAD/config verification).

- The running PO Agent was started at HEAD `66a8c10` (`PO_AGENT_EXPECTED_HEAD` from process env). `git diff --stat 66a8c10..b649da5` contains **only docs/qa files** (GIGACODE_NEXT_ACTION.md, V4_54_SKILL_MIGRATION_PLAN.md, V4_DOD_LOCK.md, A192 report) → production code served by the running stack is **byte-identical** to current HEAD. Reuse valid.

| Service | URL | Port | PID | Health |
|---|---|---|---|---|
| Frontend (Browser C, Vite) | `http://localhost:5175` | 5175 | 22389 (node) | serving; proxy `/api` → `127.0.0.1:8212` |
| PO Agent backend (V4) | `http://localhost:8212` | 8212 | 90176 (python) | `/api/v1/health` 200: `runtime=harness-dialogue-v2`, `browser_runtime=agent_core_v4`, `agent_core_v4_ready=true`, plugins `["builtin.catalog.tasks","builtin.core.a188"]`, `source_status=healthy` |
| Task API | `http://localhost:8211` | 8211 | 90132 (python) | `/api/v1/swtr-read/health` 200: `status=connected`, transport=stdio, 48 tools, read_unit/get_unit_files/get_current_sprint/get_sprint_tasks/search_sprints/search_versions all `true` |
| MCP-SWTR (SSE, QA direct-probe instance) | `http://127.0.0.1:3000/sse` | 3000 | 67951 (python, `mcp-swtr/mcp_server.py`) | SSE session + `initialize` + `tools/call get_unit_files` all OK |

Environment: `PO_AGENT_AS21_MODE=task-api`, `PO_AGENT_TASK_API_BASE_URL=http://127.0.0.1:8211`, `LLM_MODEL_NAME=Qwen/Qwen3.8-27B` (`https://api.ai.sbt/openai/v1`), team roster `task-api/config/team_members.yaml`. Concurrency 1 for all agent QA. No fake/local source used as Oracle. No unrelated processes killed.

Worktree before pull: no uncommitted production/test changes. Modified tracked files: `GIGACODE.md` (QA memory file), `po-agent-platform-v2/.po_agent/learned_policies.json` (runtime learning-loop artifact, written by the running agent), `po-agent-platform-v2/frontend/vite.config.ts` (QA service-operator edit from the prior session: proxy target 8004 → 8212 to connect the UI to the live agent; kept for the owner's manual testing, **not committed**). All other untracked files are QA scratch artifacts.

---

## Phase 1 — Direct REAL Oracle for attachment-bearing tasks

All probes read-only against live source routes (task-api → MCP-SWTR → REAL AS21). Artifacts: `qa_193_p1_oracle.json`, `qa_193_p1_files_route_raw.json`, `qa_193_p1_assignee_wmb.json`, `qa_193_p1_files_rest.json`, `qa_193_mcp_raw.json`.

### 1.1 `WMB-30000` exists and is live
`GET /api/v1/swtr-read/tasks/WMB-30000` → 200. Unit: `[OLP] OLAP Analytics Подготовка к БП2027 (ДУП)`, space WMB, updated 2026-07-10.

### 1.2 Attachment metadata for `WMB-30000` (Oracle A — two independent surfaces agree)

Live task-api route `GET /api/v1/swtr-read/tasks/WMB-30000/files` → **5 files**, each with `fileId`, `filePathParsedDto.fileName`, `fileMetadataDto.contentType/contentLength`, `createdAt`, `createdBy`:

| # | fileName | contentType | size (bytes) | createdAt |
|---|---|---|---|---|
| 1 | Справочно_3ЛТП_Типовая трудоемкость_2025-2026 (прогноз).xlsx | application/vnd.openxmlformats-officedocument.spreadsheetml.sheet | 13 205 287 | 2026-07-10T07:44:03Z |
| 2 | Справочно_Ресурсы 2026 (БП и ПГК).xlsx | …spreadsheetml.sheet | 25 882 | 2026-07-10T07:44:01Z |
| 3 | Шаблон_Календаризация (опционально).xlsx | …spreadsheetml.sheet | 13 504 | 2026-07-10T07:44:01Z |
| 4 | strata27_template_0707(1)(1)(1)(1).xlsx | …spreadsheetml.sheet | 41 496 | 2026-07-10T07:44:01Z |
| 5 | Шаблон к заполнению (согласования ПШЕ).xlsx | …spreadsheetml.sheet | 12 310 | 2026-07-10T07:44:01Z |

Raw MCP-SWTR `get_unit_files({"unit_code":"WMB-30000","safe":true})` via SSE (direct, bypassing task-api) returns the identical 5-file payload → the source surface is authoritative and not a task-api artifact.

### 1.3 Kalachanov.V.V WMB collection (Oracle B — proven assignee route)

`GET /api/v1/swtr-read/assignee-tasks?assignee=Kalachanov.V.V&space=WMB&limit=100` → `source=REAL_AS21`, `route=search_users->find_units_by_filter`, 29 pages read, **5 tasks**: WMB-30000, WMB-29890, WMB-29995, WMB-29830, WMB-29242.

Files probe per task (live route):

| task | files | names (types) |
|---|---|---|
| WMB-30000 | **5** | 5 × .xlsx (Excel) |
| WMB-29890 | **1** | Re: Планирование закупочного релиза на 2027 год.pdf |
| WMB-29995 | **10** | 6 × .xlsx, 3 × .pdf, 2 × .png |
| WMB-29830 | 0 | — |
| WMB-29242 | 0 | — |

**Oracle summary (tested surface):** attachment-bearing tasks = **3 of 5**; Excel-bearing = WMB-30000, WMB-29995; PDF-bearing = WMB-29890, WMB-29995; **MSG-bearing = none in the tested surface** (no `.msg` among the 16 files). The full space-WMB surface (all assignees) was not exhaustively enumerated; the MSG row conclusion is scoped to the tested surface and to the mechanism proof in Phase 3.

---

## Phase 2 — Canonical attachment skills A/B (public `/api/v1/query`, fresh session each, concurrency 1)

Artifact: `qa_193_p2_results.json` (full responses incl. V4 metadata).

| ID | Query | Loaded skill | Trajectory (capability calls) | Status / completion | Returned | Oracle B comparison |
|---|---|---|---|---|---|---|
| A2-1 | Задачи Калачанова с вложениями в пространстве WMB | `tasks.search` + `task.search_attachments` | space.resolve(WMB) → member.resolve(Калачанов, WMB) → task.search(assignee=Kalachanov.V.V, space=WMB) → **task.search_attachments()** | COMPLETED / runtime_contract | `count=0`, answer: «5 задач найдено, однако ни одна из них не содержит вложений» | **RED** — 3/5 candidate tasks have attachments; the same run's own `task.search` returned the 5 correct keys, then the attachment capability returned 0 (180.8 s) |
| A2-2 | Проверь на наличие вложений задачу WMB-30000 | `task.lookup` | task.lookup(WMB-30000) | COMPLETED / runtime_contract | answer: «в полученных данных о задаче информация о вложениях отсутствует» | **RED** — live source has 5 Excel files (Phase 1); `task.lookup` observation carries no attachment data (see Phase 3, layer 2) |
| A2-3 | Найди задачи с вложениями Excel в WMB | `task.search_excel` | task.search_excel() (fixed `attachment_type=excel`) | COMPLETED / runtime_contract | `count=0` | **RED** — WMB-30000 (5 xlsx), WMB-29995 (6 xlsx) |
| A2-4 | Найди задачи с PDF-вложениями в WMB | `task.search_pdf` | task.search_pdf() (fixed `attachment_type=pdf`) | COMPLETED / runtime_contract | `count=0` | **RED** — WMB-29890 (1 pdf), WMB-29995 (3 pdf) |
| A2-5 | Найди задачи с MSG-вложениями в WMB | `task.search_msg` | task.search_msg() (fixed `attachment_type=msg`) | COMPLETED / runtime_contract | `count=0` | Tested-surface oracle = 0, but the mechanism is the same proven wrong corpus (Phase 3); classified RED on mechanism (see Classification) |

Notes:
- A2-1 is the strongest single piece of evidence: within **one run**, the V4 runtime held the 5 live WMB keys from its own `task.search` step, then the legacy attachment capability independently re-derived its corpus and returned 0.
- None of the five queries emitted a raw `REAL_EMPTY` marker string, but the effect is identical: a COMPLETED answer asserting absence while the direct Oracle contains matching attachments → **false REAL_EMPTY / wrong-source defect** per the assignment definition.
- Where the current skill contract cannot accept a space/person filter directly: A2-3/A2-4/A2-5 capabilities accept **no arguments at all** (fixed `attachment_type` only) — the WMB space in the query is not bindable to the capability. Recorded separately; queries were not rewritten.
- `semantic_prepass_used=false` in all five; no clarification emitted.

---

## Phase 3 — Code-path confirmation (no code modified)

### Layer 1 — candidate corpus (rows #3–#6)

Exact production path for `task.search_attachments` / `task.search_excel` / `task.search_pdf` / `task.search_msg`:

1. **SkillSpec** — `po-agent-platform-v2/src/po_agent/harness/v4_plugins/task_catalog.py:108-135` (four SkillSpecs; procedures say "Call task.search_attachments for the full attachment-bearing task set" etc.).
2. **Capability binding** — `task_catalog.py:219-222`:
   ```python
   CapabilityBindingV4("task.search_attachments", legacy_capability_id="task.search_attachments"),
   CapabilityBindingV4("task.search_excel", legacy_capability_id="task.search_attachments", fixed_arguments={"attachment_type": "excel"}),
   CapabilityBindingV4("task.search_pdf",   legacy_capability_id="task.search_attachments", fixed_arguments={"attachment_type": "pdf"}),
   CapabilityBindingV4("task.search_msg",   legacy_capability_id="task.search_attachments", fixed_arguments={"attachment_type": "msg"}),
   ```
   All four rows funnel into **one** legacy capability.
3. **Legacy capability** — `po-agent-platform-v2/src/po_agent/harness/runtime.py:89` (`PortfolioCapabilities.task_search_attachments`):
   ```python
   tasks = await self.a.search_tasks("")          # <- UNSCOPED candidate corpus
   for t in tasks:
       items = await self.a.get_attachment_metadata(t.key)   # only reached for corpus members
   ```
4. **Adapter** — `adapters/production_task_api.py:169` (`ProductionTaskApiAS21Adapter.search_tasks`): the **live** `GET /api/v1/swtr-read/assignee-tasks` route is used **only when the JQL carries an `assignee` filter**; with the empty query `""` it falls through to `super().search_tasks(...)`.
5. **Base adapter** — `adapters/task_api.py:450` → `_fetch_tasks` (`task_api.py:412`) → `GET /api/v1/tasks` with `limit/offset` — the **local synced task store** (the same wrong source A192 proved for `task.search_text`; locally empty on this deployment).

Consequences, all proven live:
- Corpus = local `/api/v1/tasks` (empty) → loop body never executes → `get_attachment_metadata` (the live files route) is **never touched** → `count=0`.
- The attachment metadata route itself is **healthy**: `task_api.py:532` calls `GET /api/v1/swtr-read/tasks/{code}/files` and `_attachment_fields` (`task_api.py:257`) correctly maps the nested MCP shape (`filePathParsedDto.fileName`, `fileMetadataDto.contentLength/contentType`) — Phase 1 proves both the route and the mapping against real payloads.
- So the defect for rows #3–#6 is **single-layer at the corpus**: `search_tasks("")` → local `/api/v1/tasks`. Not the metadata route, not the field mapping.

### Layer 2 — single-task lookup (A2-2)

- `TaskApiAS21Adapter.get_task` (`task_api.py:440-447`) **does** fetch live attachments: `attachments = await self.get_attachment_metadata(normalized)` → `task.model_copy(update={"attachments": attachments})`. The domain `Task` carries `attachments: list[Attachment]` (`domain/models.py:71`).
- But `PortfolioCapabilities.task_lookup` (`runtime.py:81-84`) serializes via `PortfolioCapabilities.task(t)` (`runtime.py:77`), whose dict projection **omits `attachments`** (keeps key/id/title/description/status/assignee/priority/sprint/release/source/source_data only).
- Result: the V4 observation and the final answer cannot reference attachment data even though the adapter loaded it → «информация о вложениях отсутствует». A second, independent layer for the single-task case.

### Conclusion on mission question 3

The defect is the **candidate-task corpus** (`search_tasks("")` / local `/api/v1/tasks`) for the search rows — **plus** a serializer-level field drop for the single-task lookup row. The live attachment route and MCP field mapping are correct. "More than one layer" is true across the row set; each search row's failure is fully explained by the corpus alone.

---

## Phase 4 — Bounded A192 retained-defect re-confirmation (current HEAD)

Artifact: `qa_193_p4_results.json` + supplemental probes. One case per A192 defect:

| ID | Query | Result | A192 defect status |
|---|---|---|---|
| R1 (task.search_text) | Найди задачи по слову аутентификация | COMPLETED, `count=0` | **Still reproduces** — live Oracle: DMS-380 title «В компоненте Lineager не работает аутентификация в режиме mTLS, TLS, SSL» contains the phrase exactly; skill scanned the empty local corpus |
| R2 (task.search_assignee, NL person) | Задачи Андрея Жданова → NEEDS_CLARIFICATION «Не удалось однозначно определить пользователя «Андрей Жданов»» (member.resolve 2-token full name ambiguous); contrast: «Задачи Жданова» (surname only) → COMPLETED 10 tasks (Zhdanov.A.Ni), «Задачи Калачанова В.В.» → COMPLETED 2863 tasks | **Still reproduces** (shape-dependent: surname-initial forms resolve, 2-token full names dead-end in clarification) |
| R3 (task.search_status) | Открытые задачи в WMB → NEEDS_CLARIFICATION «Для skill-native POC task.search нужен исполнитель и/или спринт; уточните фильтр.» (V4 guard rejects space+status without assignee/sprint) | **Still reproduces** verbatim |

Owner-fix bundling confirmed: all three A192 defects are alive on HEAD `b649da5`.

---

## Phase 5 — Browser-C clarification continuity

### 5.1 Reproduction (Playwright, real UI on `http://localhost:5175`)

Spec (QA scratch, not committed): `po-agent-platform-v2/frontend/e2e/qa193-clarification.spec.ts`. Artifact: `qa_193_p5_ui_results.json`. Screenshot/trace: `frontend/test-results/qa193-clarification-*/`.

Fresh Browser-C session, exact query `задачи Гаранина в сентябрьском спринте`, then a **real click of the rendered `DMS` option button** (no manual query rewrite). Successful run on session `ui-da38a15c-2992-47d9-badf-2575f5031c27`:

**Turn 1**
- Request payload: `{"query": "задачи Гаранина в сентябрьском спринте", "session_id": "ui-da38a15c-2992-47d9-badf-2575f5031c27"}`
- Response: `NEEDS_CLARIFICATION` (61.5 s), question «Не удалось подтвердить пространство «?»», `options=["CRPV","DMS","OLP","STS","WMB"]`, **`clarification_id: null`**, evidence: `as21 · Garanin.R.V · Гаранин` (person **was** resolved), V4 trace present.
- UI rendered the 5 option buttons (`.option-row button`).

**Turn 2 (clicked `DMS`)**
- Request payload captured at the network layer: `{"query": "DMS", "session_id": "ui-da38a15c-2992-47d9-badf-2575f5031c27"}` — **bare token, same session, no original query, no clarification binding field**.
- Response: `NEEDS_CLARIFICATION` (3.0 s), **English**: «The query "DMS" is too ambiguous to act on. Could you clarify what you'd like to do? …», `options=[]`, **evidence: 0** — the original `Гаранин + сентябрьский спринт` constraints and the resolved `Garanin.R.V` grounding are gone.
- `session_before == session_after` (the UI holds the session correctly; the loss is not a UI session reset).

This matches the owner's manual Browser-C reproduction exactly (English generic/incomplete-query message after clicking DMS).

### 5.2 API-level control (same session id, same two turns, no UI)

Artifact: `qa_193_p5_api_control.json`. Session `20216e17-e6ba-4aa8-b9a4-87df6aee12b3`:
- Turn 1 `задачи Гаранина в сентябрьском спринте` → `NEEDS_CLARIFICATION`, options `["CRPV","DMS","OLP","STS","WMB"]`, `clarification_id: null`, trajectory: `member.resolve(Гаранин)` → `sprint.search(period=сентябрь)` (space slot unresolved).
- Turn 2 `DMS` → `NEEDS_CLARIFICATION`, English «Your query "DMS" is too brief for me to determine what you need…», `options=[]`, **`loaded_skills: []`**, trajectory: **single turn `(1, ready)`** with rationale «The user provided only "DMS" with no verb, intent, or additional context…».

The API control proves the backend, not just the UI, is broken: with the identical `session_id` and a bare `DMS`, the V4 runtime starts a **new standalone plan** — no pending-clarification state is stored or looked up, the original skill trajectory (`tasks.search` + `member.resolve` + `sprint.search`) is not resumed, and the response is the LLM's English fallback (wording differs between runs → LLM-generated, not a fixed string).

### 5.3 Code-path evidence (read-only)

Frontend:
- `po-agent-platform-v2/frontend/src/recovery/WorkspaceApp.tsx:205` — option button: `onClick={() => void send(option)}` (sends only the option token).
- `WorkspaceApp.tsx:128-139` — `send(textOverride?)`: `agent.query({ query: text, session_id: requestSessionId })` — payload is `{query, session_id}` only; the original query is never re-sent and no clarification reference field exists.

Backend:
- Turn-1 clarification response carries **no `clarification_id`** (null) and no pending-slot payload in `data._agent_core_v4`; the V4 runtime exposes no session-keyed pending-clarification state for `/api/v1/query` continuations. Turn-2 trajectory proves replanning from zero.

### 5.4 Target-semantics delta (for the owner fix)

Per the assignment's target semantics, a clarification answer must bind unresolved slot(s) of the pending original request with original grounded constraints surviving. Current behavior fails every one of those points:
- a button click **does** degrade into parsing bare `DMS` as a standalone query;
- if pending state is absent, the runtime does **not** fail explicitly in Russian with a typed clarification-state error — it silently treats the option as a new query and returns an LLM English fallback.

Incidental observation (not a separate verdict item): the exact turn-1 clarification shape is LLM-non-deterministic on this query — 3 consecutive API runs: 1× options-list («Не удалось подтвердить пространство «?»»), 2× free-text question with `options=[]`; one earlier UI batch produced 1× `FAILED` (153 s) + 2× `FAILED` (15 ms) for the same query before subsequent runs stabilized (3/3 `NEEDS_CLARIFICATION` + 1 `COMPLETED`). Qwen3.8 endpoint non-determinism (A179/A186 lineage), not a new code defect; the owner may want the clarification contract pinned deterministically alongside the continuity fix.

### 5.5 Classification

**`RED_BOTH_UI_AND_BACKEND_CONTINUATION`** — the UI sends only the bare option token (context not re-sent), and the backend retains no pending-clarification state bound to `session_id` (turn 2 is a new standalone query). Both layers must change for the target semantics; either layer alone would still fail.

---

## Classification of canonical rows #3–#6

| Row | Skill | Classification | Basis |
|---|---|---|---|
| #3 | task.search_attachments | **RED_FALSE_REAL_EMPTY_WRONG_SOURCE** | A2-1: live Oracle 3/5 tasks with attachments; skill 0; corpus = empty local `/api/v1/tasks` |
| #4 | task.search_excel | **RED_FALSE_REAL_EMPTY_WRONG_SOURCE** | A2-3: WMB-30000 + WMB-29995 carry xlsx; skill 0; same wrong corpus |
| #5 | task.search_pdf | **RED_FALSE_REAL_EMPTY_WRONG_SOURCE** | A2-4: WMB-29890 + WMB-29995 carry pdf; skill 0; same wrong corpus |
| #6 | task.search_msg | **RED_FALSE_REAL_EMPTY_WRONG_SOURCE** | Tested-surface oracle has no `.msg` (so 0 happens to match), but the capability's corpus is provably the empty local store — it can never return a correct non-zero result for any space; same single defect mechanism, fixed `attachment_type=msg` binding |

`SOURCE_CONDITIONAL` is **not** available: the direct REAL Oracle proves the attachment source surface (`get_unit_files` / `GET /api/v1/swtr-read/tasks/{code}/files`) is live and fully mapped. An empty local corpus is not source unavailability.

---

## Mission questions — direct answers

1. **Does REAL AS21/SWTR expose attachments for WMB-30000 or another fresh WMB task of Kalachanov.V.V?** Yes — WMB-30000 has 5 Excel attachments (full metadata); WMB-29890 has 1 PDF; WMB-29995 has 10 files (6 xlsx / 3 pdf / 2 png).
2. **Can attachment metadata be obtained through a direct live/source-backed route even when `task.search_attachments` returns 0?** Yes — `GET /api/v1/swtr-read/tasks/{code}/files` (and raw MCP `get_unit_files`) return complete metadata on demand for any task key.
3. **Is the defect the candidate-task corpus, the metadata route, field mapping, or more than one layer?** The candidate-task corpus (`search_tasks("")` → local `/api/v1/tasks`) for the search rows; plus a serializer field-drop in `task.lookup` (attachments loaded but projected away) for the single-task row. The metadata route and MCP field mapping are correct.
4. **Should rows #3–#6 remain SOURCE_CONDITIONAL?** No — all four are **RED_FALSE_REAL_EMPTY_WRONG_SOURCE** (see table).
5. **Can Browser C be left running after QA?** Yes — all services left running (Phase 0 table + final health below).
6. **Does the same `session_id` retain enough pending state?** No — the second turn becomes a new standalone query; the backend has no pending-clarification state and the UI sends only the bare token.

---

## Owner-fix bundle (for the next owner assignment)

Fix together, then one consolidated QA re-gate before Wave S:
1. **Live-source corpus for text/attachment search** — `task_search_text` / `task_search_attachments` (and `task_search_status`, `task_search_composite` which share the same `search_tasks("")` corpus) must derive candidate corpora from live SWTR read routes (assignee/sprint/space-scoped), never the local `/api/v1/tasks` store; the attachment scan should accept an explicit candidate set (e.g., keys from a prior `task.search` observation in the same V4 trajectory).
2. **Natural-language assignee** — `member.resolve` 2-token full-name ambiguity (Андрей Жданов → clarification dead-end) needs deterministic team-roster-scoped resolution.
3. **Status-only / space+status search** — V4 `task.search` guard currently rejects space+status without assignee/sprint; the status row needs a source-backed space+status path.
4. **Single-task attachment visibility** — `PortfolioCapabilities.task()` serializer must expose `attachments` (already loaded by `get_task`).
5. **Clarification continuity (do not postpone to a later UI wave)** — either (a) backend pending-clarification state keyed by `session_id` with a typed `clarification_id`, slot-binding of the selected option, and an explicit Russian typed clarification-state error on absent/expired/mismatched state; or (b) UI re-send of the original grounded query plus the selected slot value. Pin the turn-1 clarification contract deterministically (stable options list) to remove the LLM shape non-determinism.

---

## Final service keepalive (kept running after report commit)

| Service | URL | Port | PID | Final health |
|---|---|---|---|---|
| Frontend (Browser C) | `http://localhost:5175` | 5175 | 22389 (node) | 200 serving; `/api` proxy → 8212 verified |
| PO Agent backend | `http://localhost:8212` | 8212 | 90176 (python) | `/api/v1/health` 200, `agent_core_v4_ready=true`, `source_status=healthy` |
| Task API | `http://localhost:8211` | 8211 | 90132 (python) | `/api/v1/swtr-read/health` 200, `status=connected`, 48 tools |
| MCP-SWTR (SSE, QA probe instance) | `http://127.0.0.1:3000/sse` | 3000 | 67951 (python) | SSE session OK |

Stopped after this report. Awaiting owner command.
