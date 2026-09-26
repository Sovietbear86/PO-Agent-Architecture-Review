# A218 — Agent Self-Introspection UX Gate (agent.help)

**Verdict: `AGENT_SELF_INTROSPECTION_GREEN_A218`**
**Inventory classification: `V4_54_INVENTORY_RECONCILIATION_REQUIRED`**

- START_HEAD: `8ddfc84be14cd18c5c6bee96771cf18911253ea8`
- Owner implementation: `5c0ed16` (feat: registry-backed agent self-introspection skill), `f4d03e3` (test: registry-backed self-introspection and ping)
- Frozen baseline: A217D GREEN. Spec rollback checkpoint `checkpoint/v4-batch4-green-a217d` — **the git tag object does not exist in the repo** (docs-only convention in `V4_DOD_LOCK.md`, same as A211/A210); effective base commit = `9432fff` (docs: freeze Batch 4 GREEN after A217D).
- Role: QA/adversarial tester + service operator only. No production/frontend/plugin/test/config code modified.

---

## Phase 0 — Architecture invariants: GREEN

- Diff `9432fff..8ddfc84` limited to `src/` + `tests/` = exactly 2 files:
  - `src/po_agent/harness/v4_plugins/agent_help.py` (+132, new plugin)
  - `tests/test_agent_core_v4_agent_help.py` (+62, new focused tests)
- Zero references to `agent.help` / `agent_help` / `builtin.agent` anywhere in core (`grep -r` over `src/po_agent` excluding the plugin) — **no core routing special case**. The planner sees the skill only via registry/catalog discovery.
- Plugin properties (code review):
  - `agent.help mode=skills` reads `runtime.catalog.skills()` live — **no second hardcoded skill list**;
  - `mode=ping` returns a fixed acknowledgement and touches no source;
  - data carries `catalog_source=LIVE_V4_SKILL_CATALOG` and `availability_semantics=DECLARED_NOT_EQUAL_SOURCE_READY`;
  - answer text explicitly states catalog presence = declared capability, not source readiness;
  - completion contract `data_keys=("mode",)` is satisfied by both modes (deterministic `runtime_contract` completion observed live).
- Discovery determinism retained: sorted trusted-package scan; `builtin.agent.help` sorts first; duplicate ids are structurally rejected by the registry.
- dummy-55 invariant GREEN (plugin registry suite, see Phase 1).

## Phase 1 — Focused/unit tests: GREEN

| Suite | Result |
|---|---|
| `test_agent_core_v4_agent_help.py` + `test_agent_core_v4_plugin_registry.py` + `test_agent_core_v4_planner_signature_parity.py` | **18/18 pass** |
| `tests/test_agent_core_v4*.py` + `tests/test_v4*.py` (full V4 suites) | **198/198 pass** |

Zero unexplained failures. Signature-parity lock (A217C guard) remains green.

## Phase 2 — Live registry truth / 54-target reconciliation: RECONCILIATION_REQUIRED

Independent fresh-process `discover_v4_plugins()` enumeration (QA script `qa_218_p2_registry.py`):

- **plugin_count = 11**
- **skill_count = 62**
- duplicates = **0** (registry rejects duplicate skill/capability/binding/UI ids)
- `agent.help` present **exactly once**
- `dummy.55` **not** in production discovery (test-time dynamic registration only — correct)

Plugin list (11): `builtin.agent.help`, `builtin.batch2.team_current_sprint`, `builtin.batch3.team_release`, `builtin.batch4.release_portfolio`, `builtin.catalog.tasks`, `builtin.core.a188`, `builtin.time_accounting.aggregate`, `builtin.time_accounting.member`, `builtin.time_accounting.task`, `builtin.wave_s1.sprint_flow_release_search`, `builtin.wave_s2.sprint_history_risk`

Per-plugin skill counts: agent.help 1 · batch2 5 · batch3 5 · batch4 5 · catalog.tasks 15 · core.a188 12 · time_accounting.aggregate 4 · time_accounting.member 3 · time_accounting.task 2 · wave_s1 5 · wave_s2 5.

### Exact delta vs the authoritative 54 (canonical `SKILL_CATALOG`, `skill_catalog.py`)

62 ≠ 54 → **`V4_54_INVENTORY_RECONCILIATION_REQUIRED`** (no fabricated missing/extra skills; exact list below for owner review).

- **Covered: 48/54**
  - 42 direct id matches (capability id == V4 skill id): portfolio.overview; release.blockers/dependencies/health/progress/risk_queue/scope; sprint.carryover/current/cycle_time/health/lead_time/predictability/risk_queue/scope/scope_change/throughput/velocity/wip; task.aging/blockers/dependencies/history/lookup/missing_requirements/quality/search_assignee/search_attachments/search_release/search_sprint/search_status/similar/summary/time_in_status; team.assignee_recommendation/blocked/bottlenecks/capacity/competency_match/distribution/wip/workload
  - 6 semantic remaps (V4 id renamed for the same canonical intent): `task.search_text`↔`task.search` (task-search), `tasks.search`↔`task.search_product` (task-search-product), `task.search_excel`↔`task.search_attachment_excel`, `task.search_pdf`↔`task.search_attachment_pdf`, `task.search_msg`↔`task.search_attachment_msg`, `task.acceptance`↔`task.acceptance_analysis`
- **Missing from V4 live: 6/54**
  - `release.forecast` (entry release-forecast)
  - `po.attention_queue` (po-attention-queue)
  - `po.daily_brief` (po-daily-brief)
  - `po.status_report` (po-status-report)
  - `po.reminder_draft` (po-reminder-draft)
  - `po.local_task_draft` (po-local-task-draft)
- **Extra in V4 live (beyond canonical 54): 14**
  - `agent.help` (new, A218 meta skill)
  - time accounting (9): `member.time_spent`, `member.utilization_actual`, `member.worklogs`, `release.time_spent`, `sprint.time_spent`, `task.time_spent`, `task.worklogs`, `team.time_spent`, `team.utilization_actual`
  - discovery/collection (4): `release.search`, `sprints.discover`, `sprints.list`, `tasks.lookup_then_assignee`
- Cross-check: 48 + 6 = 54 (canonical) ✓; 48 + 14 = 62 (V4 live) ✓; delta +8 = 14 − 6 ✓

## Phase 3 — NL full-catalog gate: 12/12 PASS

4 queries × 3 runs each (`qa_218_p35_runner.py`, results `qa_218_p35_results.json`):

| Query | Result |
|---|---|
| «покажи полный список навыков, которые ты поддерживаешь» | 3/3 |
| «какие навыки ты умеешь» | 3/3 |
| «что ты умеешь» | 3/3 |
| «show all supported skills» | 3/3 |

Every run: `status=COMPLETED` (completion `runtime_contract`), `loaded_skills=['agent.help']`, trajectory = `agent.help(mode=skills)` **only** (no task/sprint/release/business skill), capability data `skill_count=62` with **exact id-set parity** to the independent registry (sorted 62/62, 0 duplicates), `plugin_count=11` + exact plugin id set, `catalog_source=LIVE_V4_SKILL_CATALOG`, `availability_semantics=DECLARED_NOT_EQUAL_SOURCE_READY`, and **0 task-api/MCP lines per run** (no AS21/source call). Latency 4.6–15.7 s.

## Phase 4 — Browser C catalog UX: 7/7 PASS

Real UI on `[::1]:5175` (`qa_218_browser_c.mjs`, results `qa_218_p4_browser.json`, screenshots `qa_218_browser_c/`):

| Case | Result |
|---|---|
| C1 «задачи в текущем спринте DMS» (generic V4 health) | COMPLETED, space.resolve→sprint.current→task.search, DMS-SPRNT-3 visible |
| C2 «релиз 24Q1 в WMB» (standalone identity) | COMPLETED, release.search only, no analytic capability |
| C3 «прогресс релиза 24Q1 в WMB» | typed SOURCE_CONDITIONAL (`v4_capability_unavailable`), release.progress executed, no fabricated metrics |
| C4 «здоровье релиза 24Q1 в WMB» | typed SOURCE_CONDITIONAL, release.health executed, no fabricated metrics |
| C5 «обзор портфеля продуктов» | COMPLETED, portfolio.overview |
| C6 «покажи полный список навыков…» | COMPLETED, agent.help only, `skill_count=62` in payload, **rendered UI text exposes 62/62 ids**, semantics note visible |
| C7 «что ты умеешь» | COMPLETED, agent.help only, `skill_count=62` in payload, **rendered UI text exposes 62/62 ids**, semantics note visible |

No V4 ERROR, no generic failure text, no session-id leak, no silent truncation of the rendered data (both catalog cases: `ids_in_ui_text = 62/62`).

**Finding F1 (non-blocking, UX polish):** UIContract `preferred_widget="skill_catalog"` has **no corresponding frontend widget** (zero references in `frontend/src`). The generic `V4ResultPanel` fallback renders the capability payload as one scrollable JSON line (all ids present and inspectable, but not a readable dedicated catalog).

**Finding F2 (non-blocking):** the top-level presentation answer is an LLM re-render whose id completeness is **non-deterministic**: across the 12 API runs the prose contained 0–62 of the 62 ids (e.g. C7 prose had 0, one API run had all 62 in a markdown table). The authoritative data layer (`data.results[0].data.skills`) is always exact 62/62. Per the spec's allowance ("prose summarization omits ids but the rendered catalog exposes all ids → acceptable") this is not RED, but the owner should consider rendering the catalog widget from `data` instead of relying on LLM prose.

## Phase 5 — Conversational ping: 15/15 PASS

3 queries × 5 runs: «ты тут?», «ты на связи?», «are you there?». Every run: COMPLETED, trajectory = `agent.help(mode=ping)` only, raw capability answer exactly `Да, я на связи.`, top-level answer `Да, я на связи. Чем могу помочь?` (concise, no «могу работать со спринтами…» boilerplate), **0 clarifications**, **0 task-api/MCP lines**, fresh sessions (no stale-state resurrection). Latency 2.1–12.9 s.

## Phase 6 — Source-free audit: PASS

- All 27 agent.help runs (12 catalog + 15 ping): **0 task-api log lines per run** (per-run line-delta audit, live).
- Whole task-api log before/after the A218 window (`qa_218_p6_audit.py`):
  - local factual reads (`GET /api/v1/tasks` non-swtr): **0 → 0**
  - mutations (POST/PUT/DELETE on data routes): **0 → 0**
  - unscoped `task-query`: **0 → 0** (all 114 task-query calls space/release-scoped; +8 during A218 from retained-regression business queries)
  - unscoped `GET /versions`: **7 → 7** (all pre-A218, all `400 Bad Request` = A217B no-space hardening rejections)
- Agent log: **0 TypeError, 0 v4_runtime_failure, 0 traceback** across the whole A218 session.

## Phase 7 — Retained regression: 12/12 PASS

| Case | Runs | Result |
|---|---|---|
| `Покажи DMS-380` (task.lookup) | 2/2 | COMPLETED, DMS-380 in answer |
| `текущий спринт DMS` (sprint.current) | 2/2 | COMPLETED, DMS-SPRNT-3 |
| `трудозатраты Семавина … сентябрьском спринте DMS` (member.time_spent) | 2/2 | COMPLETED, **A215G parity exact: 64 h / 8 entries / 5 tasks (DMS-411 24, DMS-408 16, DMS-267 8, DMS-390 8, DMS-403 8), all 4Р_Тестирование** |
| `обзор портфеля продуктов` (portfolio.overview) | 2/2 | COMPLETED |
| `релиз 24Q1 в WMB` (standalone identity) | 2/2 | COMPLETED, release.search only, no analytic capability |
| `прогресс релиза 24Q1 в WMB` | 2/2 | typed SOURCE_CONDITIONAL (`v4_capability_unavailable`), release.progress executed, zero fabricated metrics, bounded source calls |
| `здоровье релиза 24Q1 в WMB` | 2/2 | typed SOURCE_CONDITIONAL, release.health executed, zero fabricated metrics |

Zero planner signature/runtime failures (A217C class remains closed — parity test + 198/198 suites). dummy-55 retained GREEN via plugin registry suite (Phase 1).

Note: the QA runner initially misclassified the two typed-SC cases as `runtime_failure` because a typed `v4_capability_unavailable` response sets `v4.error` by design; manual reclassification confirms behavior is the certified A214/A217D terminal.

## Phase 8 — Safety/semantics: 4/4 PASS (with finding F4)

- «умеешь анализировать здоровье релиза?» (2/2) and «умеешь считать утилизацию команды?» (2/2):
  - Planner answers on turn 1 with `decision=ready`, **no skill loaded, no capability executed, 0 source calls** (warning `v4_ready_without_source_observation`, status NEEDS_CLARIFICATION with continuation `clarification_id`);
  - s1 text: «Да, у меня есть capability `release.health` … Однако она работает только при наличии авторитетной привязки релиза к задачам (release-to-task membership) в источнике. … Назовите релиз — я попробую.»
  - s2 text: conditional description of `team.utilization_actual` / `team.capacity` with «Доступность данных зависит от того, подключён ли источник в данный момент».
  - All Phase-8 expectations met: capability described **conditionally**, catalog declaration explicitly **not** equated with current source readiness, no fabricated release source maturity, no business source call.

**Finding F4 (non-blocking, owner decision):** meta «умеешь …» questions route to the planner's conditional-READY path (typed NEEDS_CLARIFICATION + `v4_ready_without_source_observation`) rather than to `agent.help`. Semantically correct per spec, but inconsistent with the explicit-list phrasings that do route to `agent.help`. Unify or accept.

---

## Services (left running)

- UI: `[::1]:5175` (vite, PID 47416)
- Agent: `127.0.0.1:8212` (PID 43578 @ `8ddfc84`, `PO_AGENT_EXPECTED_HEAD=8ddfc84…`, V4 enabled, task-api mode)
- Task API: `127.0.0.1:8241` (PID 81954, system python3)
- MCP-SWTR SSE: `127.0.0.1:3000` (PID 29268)

## Recommendation

**GREEN.** Recommend an immutable self-introspection checkpoint (e.g. `checkpoint/v4-self-introspection-green-a218` — note the tag convention is currently docs-only; consider creating the actual git tag). Then stop and return to owner the exact registry delta (62 live vs 54 target: 48 covered / 6 missing / 14 extra) so the owner decides whether the next step is full V4-54 A/B/C certification or narrowly identified missing-skill implementation (the 6 missing are `release.forecast` + the 5 `po.*` entries; the 14 extras are time accounting + discovery/collection + `agent.help`).
