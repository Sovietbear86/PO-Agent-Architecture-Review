# A204 — Agent Core V4: Sprint/Release Health + Dialog Context Diagnostic

**Verdict: `AGENT_CORE_V4_SPRINT_HEALTH_DIALOG_CONTEXT_RED`**

- **Branch:** `feat/core8-real-query-hardening-v2`
- **START_HEAD:** `5b42e5930d6e2b64f85925f35bb15c2167becf0b`
- **Checkpoint chain:** A201 `ae5caee` → A202 `e580489` (tag `checkpoint/v4-pre-wave-s-a202`) → A203 `2e359d4` → **A204 START `5b42e59`**
- **Production code delta since A202 checkpoint:** none (`git diff --stat e580489..5b42e59 -- po-agent-platform-v2/src/` is empty; only `GIGACODE_NEXT_ACTION.md` and `tests/test_v4_owner_fix_contracts.py` changed via owner fix `0c57346`).
- **Date:** 2026-09-22
- **QA mode:** adversarial black-box + static contract audit; no production code changes; read-only source access.

---

## 1. Phase 0 — Environment & baseline

| Check | Result |
|---|---|
| `git pull --ff-only` to `5b42e59` | OK (78def3f..5b42e59: 28f1c14 spec A204, 5b42e59 spec extended to release) |
| Worktree | 3 known QA-artifact modifications only (GIGACODE.md, learned_policies.json, vite.config.ts) — no owner code |
| `pytest tests/test_v4_owner_fix_contracts.py` | **17/17 pass** (A203 blocker resolved by `0c57346`; re-confirmed at test time and pre-report) |
| Agent restart on START_HEAD | fresh uvicorn PID 42338, `PO_AGENT_EXPECTED_HEAD=5b42e59…`, `/live` 200 |
| task-api 8241 / UI 5175 / MCP 3000 | 200 / 200 / OPEN; `swtr-read/health` connected, transport=sse, 48 tools |
| Plugin registry tests (`pytest -k plugin`) | **21/21 pass** (dummy-55 extensibility set) |

## 2. Phase 1 — Static contract audit (no code edits)

### 2.1 `sprint.health` (v4_plugins/core.py:91)
- Capabilities: `("sprint.resolve", "sprint.health")`.
- Completion: `CompletionRequirement("sprint.health", data_keys=("sprint_id","total"))` — requires an observation **from the `sprint.health` capability itself**.
- UI: `UIContractV4("analysis", preferred_widget="sprint_health")`.
- Binding: `legacy_capability_id="sprint.health"` → `PortfolioCapabilities.sprint_health` (runtime.py:117) which **does compute real metrics** (total/completed/active/blocked/completion_percent) via `adapter.get_sprint_tasks(sprint_id)` → `GET /api/v1/swtr-read/sprints/{id}/tasks` (complete route).

### 2.2 Competing contracts (identity-only eligibility)
- `sprints.discover` (core.py:81): completion = `CompletionRequirement("sprint.search", data_keys=("sprint_id",))` — **satisfied by sprint identity alone**. UI: `sprint`/`sprint_summary`.
- `sprint.current` (core.py:90): `completion=()` — no contract; planner READY is accepted for contract-less skills (agent_core_v4.py:1159–1168).
- **Conclusion (static):** a "health" query can complete without `sprint.health` executing whenever the planner loads `sprints.discover` (deterministic `runtime_contract`) or `sprint.current` (`planner_ready`). The frontier is structural (capability observations), not semantic (user intent).

### 2.3 Completion frontier (agent_core_v4_completion.py)
- `completion_frontier_skills` (line 207): latest loaded skill **without a contract ⇒ empty frontier ⇒ no deterministic completion**; engaged skills (any required capability observed) + latest + pinned form the frontier.
- `completion_frontier_satisfied` (line 248) → deterministic `runtime_contract` completion (agent_core_v4.py:1232) or planner-READY acceptance.
- `_nonempty(0)` is **True** (line 53) — a zero-row health observation would still satisfy `data_keys=("…","total")` (release edge case, §6).

### 2.4 Session context (api/v1/__init__.py)
- **The only cross-turn state is `_pending_clarifications: dict[session_id → PendingClarification]`** (line 38), exclusively for typed clarification continuations.
- `_prepare_query` (line 177): when `clarification_id` is absent it pops stale state and returns the raw query with an **empty continuation** — no prior observations, no resolved entities (sprint_id/space/person), no conversation history reach the planner.
- `HarnessRequest` continuation fields (`resume_loaded_skills`, `resume_observations`, `required_completion_skills`) are populated **only** from `PendingClarification`.
- **Conclusion (static):** a same-session follow-up like «этом спринте» has **no referent channel** by design; each non-clarification turn is stateless for the planner.

### 2.5 Release surface
- `release.health` (core.py:93): completion = `release.health` observation with `release_id`+`total`; UI `analysis`/`release_health`; binding → `PortfolioCapabilities.release_health` → `adapter.get_release_tasks(release_id)`.
- `release.resolve` (agent_core_v4.py:877): `get_release_tasks(reference, space)`; typed clarification only when 0 tasks.
- Adapter path: `get_release_tasks` (task_api.py:496) → `search_tasks("release = X[ AND project = S]")`. Hardened adapter (hardened_production_task_api.py:284–327): **project+release ⇒ fail-closed `AS21SourceUnavailable`**; **release-only ⇒ `super().search_tasks` ⇒ full-tenant `GET /api/v1/swtr-read/task-query` scan + client-side release filter** (no server-side release filter exists).
- Task-api routes: **no release-task collection route**; `/versions` returns version metadata only via MCP `search_versions` — **and that tool is currently broken** (see §6).

## 3. REAL AS21 oracle (DMS, built 2026-09-22 ~12:05–12:10 local)

- September sprint = **`DMS-SPRNT-3`** «Спринт 2026.09 - 1», status IN_PROGRESS, 2026-09-13 → 2026-09-27 (route `spaces/DMS/sprints`).
- `sprints/DMS-SPRNT-3/tasks?space=DMS&complete=true`: **65 tasks** (complete=True, 1 page, `source_path=get_sprint_tasks`).
- Classification (product `TERMINAL_STATUS_TYPES` mirror): **50 open / 15 terminal / 0 undecodable**; status names: Open 21, In progress 9, Resolved 9, Закрыт 3, Closed 3, In review 6, QA 4, Ready for QA 2, Need info 3, Тестирование 2, Ready for review 1, На исправлении 1, Зарегистрирован 1.
- Live drift observed during the session (source actively changing): +DMS-424/+DMS-425 appeared; status counts shifted between fetches. Key sets were re-verified per run; deltas are drift, not agent error.
- Derived oracles (from sprint rows, `assigned_to` + `workflow_status.statusType`): Zhdanov.A.Ni open in DMS-SPRNT-3 = **[DMS-371]** (matches A199 batch-A oracle); Garanin.R.V in DMS-SPRNT-3 = **7 tasks** [DMS-93, DMS-243, DMS-402, DMS-405, DMS-412, DMS-414, DMS-425].
- **Release inventory: unavailable** — `GET /versions` probes (7 variants across 2026-09-21/22) → 502 (space=DMS) / 400 (query-only); MCP `search_versions` tool is the single source of release ids and is failing. No release attribute in sprint task rows (only `workflow_status`, `assigned_to`). → explicit release-id controls impossible this session (SOURCE_CONDITIONAL).

## 4. Phase 2 — Turn 1: «здоровье сентябрьского спринта по DMS» (10× fresh sessions, concurrency 1)

**Result: 10/10 `COMPLETED` — all identity-only. `sprint.health` never executed (0/10).**

| # | loaded | capabilities | completion mode | evidence | UI widget |
|---|---|---|---|---|---|
| p2_01..p2_10 | `sprints.discover` | `space.resolve(DMS)` → `sprint.search(DMS, сентябрь)` | `runtime_contract` (deterministic) | 1 | `sprint_summary` (kind `sprint`) |

- Resolved sprint_id = **DMS-SPRNT-3** in all 10 (correct source identity).
- The answers **self-admit the missing deliverable** while status is COMPLETED, e.g. p2_01: «Спринт найден и находится в статусе IN_PROGRESS. **Детальные метрики здоровья (прогресс задач, burndown, скорость) в текущих данных отсутствуют** — для их получения потребуется дополнительный запрос по задачам спринта.»
- Latency 21–55s. Zero fabrication; source provenance live (`swtr-read`).

**Classification (per assignment):** **RED — completes without `sprint.health` observation; identity-only.** Deterministic 10/10, not LLM variance: the planner loads `sprints.discover` for a health intent, and its sprint-search contract auto-completes the trajectory (frontier is structural, §2.3). The correct `sprint.health` capability is source-backed and functional (proven via p4a task collection), so this is a routing/completion-contract defect, not a source gap.

## 5. Phase 3 — Same-session follow-up: «Покажи список задач в этом спринте и их статусы» (10 session pairs)

- **Turn 1:** 10/10 COMPLETED identity-only (identical to P2: `sprints.discover` → sprint DMS-SPRNT-3, no health, no tasks).
- **Turn 2 (same session_id): 10/10 FAILED** in 2–16s:
  - `data._agent_core_v4.error = "unknown skill: sprint.list"`, `warnings=["v4_runtime_failure"]`, answer «Agent Core v4 не смог безопасно завершить траекторию.»
  - Trajectory: planner `load_skill sprint.current` → deterministic cardinality guard remap → `SkillCatalogV4.load("sprint.list")` → `V4ContractError`.

### D-A204-2 — deterministic crash: cardinality guard targets a nonexistent skill id
- `agent_core_v4_reliable.py:472–475`:
  ```python
  if skill_id == "sprint.current" and self.query_requests_sprint_collection(query):
      return "sprint.list"
  ```
  but the catalog skill id is **`sprints.list`** (core.py:57; discovered catalog verified: 27 skills, `sprints.list` present, `sprint.list` **absent**). `sprint.list` is the **capability** id, not the skill id — the guard conflates the two.
- Trigger = `query_requests_sprint_collection` (agent_core_v4.py:1039): sprint noun + collection marker («список») — **false positive for task-list queries** («список **задач** в этом спринте» asks for tasks, not a sprint set).
- **Latent since `a4fce91` (2026-09-12, A183).** The unit test pins the wrong value: `tests/test_agent_core_v4_sprint_discovery.py:170` asserts `_reconcile_loaded_skill("sprint.current", "Активные спринты в DMS") == "sprint.list"` — so CI is green on the bug. Never surfaced before because prior QA batches never combined planner-`sprint.current` with a collection-marker query.
- **Owner fix (proposed, not implemented):** (1) remap to `"sprints.list"`; (2) tighten the heuristic so the marker+sprint-noun rule does not fire when the collection object is tasks (e.g. «задач/задачи» present); (3) fix the unit test to assert `"sprints.list"` and add a non-mocked regression for the follow-up phrasing.

### D-A204-3 — architectural: no session referent channel (root cause, masked by D-A204-2)
- Even with the crash fixed, «этом спринте» is **unresolvable**: turn 1's resolved sprint_id (DMS-SPRNT-3) is never passed to turn 2 (§2.4). The planner's `sprint.current` fallback is a guess (happens to be the right sprint only because DMS-SPRNT-3 is also the current one — an accident of the calendar, not context).
- **Classification:** the same-session follow-up capability is **not implemented**; observed behavior = deterministic hard crash (D-A204-2) instead of a typed clarification. Product decision required: either add a session entity-context channel (persist resolved sprint/space/person per session_id and expose to the planner as validated context) or explicitly scope V4 to single-turn + typed-clarification continuations.

## 6. Phase 4 — Explicit controls

| Control | Runs | Result |
|---|---|---|
| «Покажи список задач в **DMS-SPRNT-3** и их статусы» (fresh) | 3/3 | **COMPLETED, exact**: `task.search(sprint_id=DMS-SPRNT-3, space=DMS)` → **65/65 key parity vs live oracle**, statuses present (backlog 22 / active 10 / testing 6 / review 6 / qa 2 / waiting 3 / completed_pending 9 / completed 6 / review_queue 1); UI `task_table`. 92–101s. |
| «Покажи список задач **сентябрьского спринта DMS** и их статусы» (fresh) | 3/3 | **COMPLETED — identity-only false**: planner loads `sprints.discover` (not `task.search_sprint`), runtime_contract on sprint.search; answer: «**Список задач спринта не был получен в рамках текущего запроса**. Для вывода задач с их статусами необходимо выполнить дополнительный запрос…» — same class as Phase 2. |
| «…в **этом** спринте…» (in-session after pair t1) | 2/2 | **FAILED** `unknown skill: sprint.list` (D-A204-2). |

**Isolation:** explicit sprint id works end-to-end (GREEN); the NL-period phrasing for a *task listing* degrades to identity-only completion (planner skill choice, D-A204-1 class); the session-reference phrasing crashes (D-A204-2). All three failure modes are now separated.

## 7. Phase 5 — Release health: «здоровье релиза по DMS» (10× fresh sessions)

**Result: 10/10 FAILED `source_unavailable` (fail-closed, zero fabrication).** Elapsed 15.6–293s.

Uniform signature:
- loaded `release.health` → `release.resolve(reference="DMS")` — **the planner binds the space name as the release id** (10/10). «по DMS» (in space DMS) is misread as release=DMS; no clarification is offered despite DMS being a known space, not a release.
- `release.resolve("DMS")` → `get_release_tasks("DMS")` (no space) → hardened adapter release-only branch → **full-tenant `task-query` scan** with client-side `release_id == "DMS"` filter → 0 rows after 79–293s, or earlier transport failure → `AS21SourceUnavailable` → typed FAILED.

**Classification: RED (capability unusable on the certified live path), fail-closed intact.** Two independent causes:
1. **Planner grounding defect:** a space token is accepted as a release reference without validation (should be rejected/clarified: DMS is in the approved-spaces list, not a release shape).
2. **Source architecture gap (A196/A197 D2 class):** no release-task collection route; release-only queries are O(tenant-wide scan). The explicit real-release-id control is **blocked by proven source outage**: `GET /api/v1/swtr-read/versions` → 502 (MCP `search_versions` transport failure) on 5 probes 2026-09-22 and 2 earlier on 2026-09-21; query-only variants → 400 (`SWTRMCPProtocolError`). No real release id obtainable ⇒ explicit control marked **SOURCE_CONDITIONAL (blocked)**, not RED.
- Note: had the scan returned 0 rows instead of failing, `release.health(total=0)` would satisfy its contract (`_nonempty(0)=True`) — a latent zero-row false-completion edge (not observed; the scan failed first).

## 8. Phase 6 — Same-session release follow-up: «Покажи список задач в этом релизе и их статусы» (5 pairs)

- **t1:** 5/5 FAILED `source_unavailable` (same signature as P5, `release.resolve(reference="DMS")`).
- **t2:** 5/5 **NEEDS_CLARIFICATION** (safe, 5.5–25.8s): free-text question, no options, `clarification_id` present. Examples: «Фраза "в этом релизе" не позволяет однозначно определить, о каком именно релизе идёт речь» / «Уточните … идентификатор релиза (release id)».
- **Comparison with sprint:** the release follow-up degrades to a **typed safe clarification**, while the sprint follow-up **crashes** (D-A204-2). Both share the D-A204-3 root cause (no session context); the differing surface behavior is which fallback path each intent hits.

## 9. Phase 7 — Regression safety (retained controls)

| Control | Result |
|---|---|
| P7a «Текущий спринт в DMS» ×2 | **GREEN 2/2** — `sprint.current`, DMS-SPRNT-3, 20–47s |
| P7b «Какой спринт в DMS идёт в сентябре» ×2 | **GREEN 2/2** — `sprints.discover`, DMS-SPRNT-3 + IN_PROGRESS + dates, source-accurate |
| P7c «Открытые задачи Жданова в текущем спринте DMS» ×3 | **GREEN 3/3** — 2/3 batch exact **[DMS-371]** (oracle parity, A199 class retained); 1 run FAILED `source_unavailable` after 3 healthy steps (SSE latency spike) → re-probe **COMPLETED [DMS-371] exact** (170.7s). No regression. |
| P7d «задачи Гаранина в сентябрьском спринте» → continuation, ×2 pairs | **1/2 pairs usable.** Pair 2: t1 typed NEEDS_CLARIFICATION (space) → t2 (DMS + clarification_id) **COMPLETED — but identity-only**: continuation executed `space.resolve`+`sprint.search` under `sprints.discover` and completed `runtime_contract` without any task search; answer admits «данные о задачах Гаранина … отсутствуют». Pair 1: t1 FAILED 261.5s `planner failed robust bounded repair: [ValidationError, ReadTimeout, invalid_recovery_action, ReadTimeout]` (F1 LLM degradation, fail-closed). |
| Plugin registry / dummy-55 extensibility | **21/21 pass**; live responses carry `plugin_ids=['builtin.catalog.tasks','builtin.core.a188']`, `runtime=agent_core_v4` |
| Owner fix contracts (A203) | **17/17 pass** at START_HEAD |

- **P7d pair-2 detail:** turn 1 mis-routed to `sprints.discover` (intent drift: person-tasks query → sprint-discovery skill). The A201 continuation fix pins the contract of the **loaded** skill — structurally correct, but it cannot detect that the loaded skill does not match the original intent. This is the same semantic-agnostic-frontier class as D-A204-1/D-A200-1, now observed on the continuation path (A201's certified 3/3 TRUE continuations used `tasks.search` routing; routing non-determinism under LLM degradation re-exposes the hole).
- No A201/A202/A203 regression on retained GREEN paths.

## 10. Safety & hygiene audit (all 70+ live runs)

- **Local store reads `GET /api/v1/tasks`: 0** (A198-F2 class retained closed).
- Live source calls: 305 `swtr-read` (tasks/{code} 203, spaces 38, task-query 32, sprints 17, assignees/resolve 14, health 1). Zero fabrication observed in any answer; every FAILED/NEEDS_CLARIFICATION is typed.
- **F1 LLM endpoint degradation (ongoing since A200):** 44× HTTP 429, single calls up to ~4 min, `ValidationError`/`ReadTimeout` repair failures. Affected runs: 11 batch runs (all fail-closed, re-run clean where product-relevant) + p7d_01t1 + 1 client-side 330s timeout on re-probe. Environmental, not product logic.
- **F2 (new, non-blocking) N+1 validation:** `task.search` over 65 tasks triggers 65 per-task `GET swtr-read/tasks/{code}` evidence-validation calls (195 = 3×65 in p4a) → 92–101s wall time per explicit-sprint query.
- **F3 (source outage):** MCP `search_versions` (backing `/versions`) 502/400 across all probes — blocks release inventory and any real-release-id control.
- `task-api /api/v1/health` → 404 (route absent at this HEAD; root `/health` is the A202-fixed scoped one); `swtr-read/health` fast/healthy.

## 11. Defect summary

| ID | Phase | Severity | Description | Determinism |
|---|---|---|---|---|
| **D-A204-1** | 2/4b/7d | **RED (blocking)** | Health/list intent completes **identity-only**: planner loads `sprints.discover` for «здоровье…»/NL-sprint task-list queries; its sprint-search contract auto-completes (`runtime_contract`) without `sprint.health`/`task.search`; answer self-admits missing data while status=COMPLETED; UI shows `sprint_summary` not the requested deliverable. Structural frontier cannot see intent. | 16/16 (10 P2 + 3 P4b + 1 P3t1-class + 1 P7d-continuation) |
| **D-A204-2** | 3/4c | **RED (blocking)** | `agent_core_v4_reliable.py:475` remaps `sprint.current`→`"sprint.list"` (capability id) but the skill id is `sprints.list` → `V4ContractError: unknown skill` → deterministic FAILED. Unit test `test_agent_core_v4_sprint_discovery.py:170` asserts the wrong id. Latent since `a4fce91` (A183). Secondary: collection heuristic false-positives on task-list queries. | 12/12 |
| **D-A204-3** | 3/6 | **RED (architectural)** | No same-session entity-context channel outside typed clarification continuation → «этом спринте»/«этом релизе» unresolvable by design; crash (sprint) or safe clarification (release) depending on fallback. Product decision required. | 10/10 + 5/5 |
| **D-A204-4** | 5/6t1 | **RED (capability) + SOURCE_CONDITIONAL (control)** | `release.health` unusable on certified live path: planner binds space as release ref (15/15); release-only fetch = full-tenant scan → `AS21SourceUnavailable` fail-closed; no release-task route; `/versions` source outage blocks real-release-id controls. Fail-closed intact; latent `total=0` false-completion edge (contract accepts 0). | 15/15 fail-closed |

**Retained GREEN:** explicit-sprint-id task listing (65/65 exact w/ statuses), current-sprint identity, period discovery, person+sprint+space multi-filter (incl. re-probe), clarification-continuation mechanics (session_id+clarification_id preserved), plugin registry, owner contracts, zero local-store reads, zero fabrication.

## 12. Owner fix directions (proposed, not implemented)

1. **D-A204-1:** intent-aware completion at the planner/skill boundary — e.g. deterministic mapping of «здоровье/progress/health» intent to `sprint.health` (and release analog), or reject `runtime_contract`/planner READY when the terminal skill's UI result_kind does not match the requested deliverable class; at minimum never mark COMPLETED when the loaded skill's contract was satisfied by a resolver-only observation for a collection/analysis intent.
2. **D-A204-2:** remap to `"sprints.list"`; tighten `query_requests_sprint_collection` (do not fire when the collection object is tasks); fix `test_agent_core_v4_sprint_discovery.py:170` and add a non-mocked regression for «Покажи список задач в этом спринте…».
3. **D-A204-3:** either implement a bounded session entity-context channel (persist resolved sprint/space/person per session_id from COMPLETED turns and expose to the planner as validated, source-confirmed context for definite references like «этом спринте») or explicitly document/scope V4 as single-turn + typed-clarification continuations only.
4. **D-A204-4:** validate `release.resolve` references against release shape/space list (reject a known space as a release ref → typed clarification); add a bounded release-task collection (server-side release filter on `task-query` or a dedicated `releases/{id}/tasks` route per A185 B1 pattern); restore the `search_versions` MCP tool; consider making `total=0` non-satisfying for health contracts.

## 13. Services left running

| Service | Port | PID |
|---|---|---|
| UI (vite, ::1) | 5175 | 55236 |
| agent (5b42e59) | 8212 | 42338 |
| task-api (SSE) | 8241 | 55200 |
| MCP-SWTR | 3000 | 55196 |

**QA artifacts (untracked, root):** `qa_204_restart_agent.sh`, `qa_204_poll_live.py`, `qa_204_oracle.py`, `qa_204_batch_runner.py`, `qa_204_p7_runner.py`, `qa_204_p7_reprobe.py`; `/tmp/qa204_*.jsonl|json|log` (runs, oracle, batch/p7 logs, agent log `/tmp/qa204_agent.log`).

**Next (owner):** fix bundle D-A204-1…4, then one consolidated re-gate (P2 10×, P3 10 pairs, P4 controls, P5/P6 after `/versions` restored with a real release id, P7 retained). **STOP after this report — no Wave S, no new skills.**
