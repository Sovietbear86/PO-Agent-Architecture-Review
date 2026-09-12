# Assignment 184 — Agent Core v4 Representative POC Recheck (183 owner fixes)

**Date:** 2026-09-12
**QA role:** GigaCode (QA/tester only; no production modifications)
**Final verdict:** `V4_BOUNDED_RED` (details in Section 6)

---

## 0. Test base and environment

| Item | Value |
|---|---|
| Branch | `feat/core8-real-query-hardening-v2` |
| Test base HEAD | `21a6275` (A183 complete: `8903db3` + A184 assignment commit) |
| Owner commits under test (verified ancestors of HEAD) | `796c466` (bounded resilient transport), `a4fce91` (sprint discovery/list + plural governance), `7be4e6b` (source-authority identity governance), `814ab44` (A183 spec, context) |
| Model/provider | `Qwen/Qwen3.8-27B` (unchanged) |
| Agent under test | **fresh** PO Agent, port **8020**, started from HEAD `21a6275` via `qa_184_start_po_agent.sh`; `/health`: `status=healthy`, `agent_core_v4_ready=true`, `adapter=task-api`, `source_status=healthy` |
| Task API | port 8013 (running from A183 session, SSE → MCP-SWTR) |
| MCP-SWTR | `http://127.0.0.1:3000/sse` → REAL AS21 |
| Disposable fail-closed probe runtime | port **8021**, same HEAD, `PO_AGENT_TASK_API_BASE_URL=http://127.0.0.1:8099` (dead port) — used only for the genuine-outage probe; never touches the real source |
| Concurrency | 1 (fresh session per run; agent call timeout ≤ 600 s) |
| Stale-runtime rule | honored — 8004–8019 not reused; fresh 8020 + 8021 |

Pre-reads performed: `AGENT_CORE_V4_FINAL_POC_DECISION_182.md`, `AGENT_CORE_V4_SKILL_NATIVE_SPEC.md`, `V4_DOD_LOCK.md`, `qa_183_phase4_results.json`, `qa_183_phase4_runner.py`.

---

## 1. Phase 0 — Focused build/protocol gate → **GREEN**

### 1.1 Focused suites (A184-specified command)

```
./.venv/bin/python -m pytest -q \
  tests/test_adapter_transport_resilience.py \
  tests/test_agent_core_v4_sprint_discovery.py \
  tests/test_agent_core_v4_identity_governance.py \
  tests/test_agent_core_v4_skill_native.py \
  tests/test_agent_core_v4_robust_protocol.py \
  tests/test_agent_core_v4_reliable.py
```
→ **58 passed** in 0.64 s (all GREEN).

### 1.2 Static invariants (`qa_184_p0_static.py`) → **12/12 PASS**

1. Production V4 runtime = `RobustReliableAgentCoreV4Runtime` referencing `RobustSkillNativePlannerV4` (robust/action-only planner path).
2. `runtime_factory` wires `RobustReliableAgentCoreV4Runtime`.
3. All `semantic_prepass_used` emissions on the V4 path are `false` (7/7 emission sites); **no `prepass(` call-site** in any V4 module.
4. No entity/phrase/person/surname/trajectory hardcode introduced in owner-changed production code (tokenize-based scan of executable code across all 7 changed `src/` files in `814ab44..8903db3`; the only raw-diff literal hits were docstrings, comments, and the generic Russian month-stem vocabulary in `sprint_period.py`, which is authorized lexical month normalization).
5. V4 capability catalog = 15 capabilities including the two new ones `sprint.search` and `sprint.list` (full expected set present; note: the A184 instruction text said "16 = prior 14 + 2" — the actual prior catalog was 13, so 15 is the correct total; all expected names verified).
6. Action-only recovery: `_decode_dsl("READY …", allow_ready=False)` → `None` (recovery-minted terminal READY rejected); primary READY decodes; recovery `CALL` still decodes.

### 1.3 Broader po-agent suite — no new failures from 183

- HEAD `21a6275`: `16 failed, 1334 passed, 12 skipped, 11 errors`.
- Pre-183 base `4f096b7` (parent of `814ab44`, worktree run): **27 failed+errored node IDs — byte-identical set to HEAD** (`diff` of sorted FAILED/ERROR lists = empty).
- All 16 failures + 11 errors are therefore **pre-existing** (real-LLM integration env, SWTR live-integration, and order-dependent isolation cases such as `test_skill_registry::test_get_active_skills`, which passes in isolation in both trees). **Zero new regressions from the 183 owner changes.**

---

## 2. Oracle B (fresh, REAL AS21 only, collected during this run — nothing hardcoded)

Artifacts: `qa_184_oracle_b.json`, `qa_184_oracle_b2.json`, `qa_184_oracle_b3.json`, `qa_184_oracle_b4_fresh.json`, `qa_184_oracle_b5_styp.json`, `qa_184_oracle_longdesc.json`, `qa_184_oracle_kuznetsov.json`, `qa_184_oracle_sprnt1_route.json`.

| Fact | Value (fresh) |
|---|---|
| DMS-380 | space DMS, sprint DMS-SPRNT-2, status «Тестирование», assignee `semavin.m.m` / `Semavin.M.M` (MCP direct + swtr-read cross-check agree) |
| Semavin.M.M task collection (TQL `assigned_to`) | **306** (all approved spaces) |
| Zhdanov.A.Ni tasks | 12 (TQL; 11 in approved spaces — `PLEN-112` is space PLEN, outside approved scope, and the assignee route filters it out by design) |
| Kalachanov.V.V tasks | 2858 (STS 2693, CRPV 160, WMB 5) |
| Kuznetsov.M.Se tasks (DMS-99's assignee) | 62 |
| Ivanov.P.Se tasks | 36; **0** in DMS-SPRNT-2 |
| DMS sprints | `DMS-SPRNT-1` (NEW, 12–26 Apr 2026), `DMS-SPRNT-2` (NEW, 16–30 Aug 2026); both non-closed → active set = both |
| DMS current sprint | `DMS-SPRNT-1` |
| DMS-SPRNT-1 tasks | **104** (TQL ground truth); the sprint-tasks route first page = 100 unique keys (live `get_sprint_tasks` schema accepts only `sprint_id` — no page input) |
| DMS-SPRNT-2 tasks | 39 (route and TQL agree) |
| OLP sprints overlapping August 2026 | `OLP-SPRNT-5` (Aug 4–18, FINISH) and `OLP-SPRNT-6` (Aug 24–Sep 7, FINISH) → ambiguity control |
| Identity resolve (route) | `Петр Иванов` → `Ivanov.P.Se` (200); `Александр Жданов` → 409 globally ambiguous (agent uses roster hint `Zhdanov.A.Ni` + source re-validation); `Семанин` → 409; `Неизвестный Псевдоним` → 409 |
| Long-description tasks | DMS-99 (5473 chars, `kuznetsov.m.se`, «Resolved»/done, DMS-SPRNT-1), DMS-336 (4745 chars, `agataeva.a.z`, «In review»/progress, DMS-SPRNT-1) |
| PVM-Guru | **does not exist in the current source** (TQL exact/like `code` = 0 rows; no `PVM` space; summary `like "%Guru%"` = 0). It was a benchmark label from A178–A181; the source has since changed. |

---

## 3. Phase 1 — Mandatory 10× DMS-380 gate (the 182 blocker) → **10/10 PASS**

Query: `Покажи DMS-380 и затем задачи его исполнителя` (`qa_184_p1_runner.py`, artifact `qa_184_p1_results.json`).

| run | status | keys | parity | recovery turns | bad lookup | recovery-minted READY | latency |
|---|---|---|---|---|---|---|---|
| 01 | COMPLETED | 306 | exact | 0 | no | no | 32.7 s |
| 02 | COMPLETED | 306 | exact | 0 | no | no | 26.6 s |
| 03 | COMPLETED | 306 | exact | 0 | no | no | 32.7 s |
| 04 | COMPLETED | 306 | exact | 0 | no | no | 34.0 s |
| 05 | COMPLETED | 306 | exact | 0 | no | no | 16.6 s |
| 06 | COMPLETED | 306 | exact | 0 | no | no | 26.6 s |
| 07 | COMPLETED | 306 | exact | 0 | no | no | 25.2 s |
| 08 | COMPLETED | 306 | exact | 0 | no | no | 29.8 s |
| 09 | COMPLETED | 306 | exact | 0 | no | no | 21.7 s |
| 10 | COMPLETED | 306 | exact | 0 | no | no | 24.3 s |

- **10/10 exact key-set parity (306/306) vs the fresh TQL Oracle B**; canonical trajectory in every run: `load_skill tasks.lookup_then_assignee → task.lookup(DMS-380) → task.search(assignee=semavin.m.m) [JSON] → ready`.
- Zero wrong `task.lookup` recovery, zero recovery-time `READY`, `semantic_prepass_used=false` in all 10 runs.
- **Transport check:** no run failed at the `assignee-tasks` read-through; no retry/refresh events in the agent log (source was healthy under load today). The bounded policy (90 s × 3 + backoff + client refresh) is proven at the protocol level by the 9 GREEN unit tests (Phase 0) and by the bounded dead-source probe (Section 5, 8021: bounded attempts, typed failure, 7.1 s).
- **Bounded-exhaustion check:** the P2-4 runs below (Section 4) demonstrate the same bounded policy exhausting its budget (289–303 s ≈ 3×90 s + backoff) and still failing **closed with a typed source message, zero keys** — no infinite retry, no empty/fabricated collection.

**The 182 `BLOCKED_BY_PROVEN_SOURCE_OUTAGE` is closed at the gate.**

---

## 4. Phase 2 — Mixed representative generalization matrix → **15/19 exact; 2 pre-existing bounded defect boundaries**

`qa_184_p234_runner.py`, artifact `qa_184_p234_results.json`. All expected sets from the fresh Oracle B.

| Case | Query (abridged) | Oracle | Result | Verdict |
|---|---|---|---|---|
| P2-1a | Задачи Семавина М.М. | 306 | 306 exact, 30.4 s | PASS |
| P2-1b | Задачи Жданова А.Н. | 11 (approved-scope) | 11 exact | PASS (see note ①) |
| P2-1c | Задачи Калачанова В.В. | 2858 | 2858 exact, 57.9 s | PASS |
| P2-2a | Открытые задачи Семавина в OLP | 166 | 166 exact | PASS |
| P2-2b | Открытые задачи Жданова в WMB | 0 | 0 exact | PASS (see note ①) |
| P2-2c | Открытые задачи Калачанова в STS | 404 true non-terminal | **2609** | **RED — defect B2** (pre-existing) |
| P2-3a–c ×3 | Покажи PVM-Guru и затем задачи его исполнителя | typed not-found (source: task absent) | 3/3 COMPLETED typed not-found, 0 keys, **no `task.search`** | PASS |
| P2-3d | Покажи DMS-99 и затем задачи его исполнителя | 62 (Kuznetsov.M.Se) | 62 exact | PASS |
| P2-4a–c ×3 | Задачи в текущем спринте DMS | DMS-SPRNT-1 (104 TQL / 100 route page) | **3/3 FAILED** typed «Источник AS21 временно недоступен», 0 keys, 289–303 s | **RED — defect B1** (pre-existing) |
| P2-5a | Покажи DMS-99 (5473-char desc) | DMS-99 facts exact | COMPLETED, exact facts | PASS |
| P2-5b | Покажи DMS-336 (4745-char desc) | DMS-336 facts exact | COMPLETED, exact facts | PASS |
| P2-6a | Проверь качество формулировки DMS-380 | task.quality | COMPLETED | PASS |
| P2-6b | Покажи здоровье спринта DMS-SPRNT-2 | sprint.health (39 tasks) | COMPLETED, 39-task health table | PASS |
| P2-7a | Сколько незакрытых задач у Семавина в OLP? | 166 | answer = 166 | PASS |
| P2-7b | Кто исполнитель задачи DMS-380? | Семавин | answer names Семавин | PASS |

Note ① — the first-pass "failures" of P2-1b/P2-2b were **QA oracle-construction errors, not agent defects** (proven by re-collection `qa_184_oracle_b4/b5`): (a) the assignee route by design filters out non-approved spaces (`swtr_assignee.py:253-254`, `PLEN` excluded → 12 TQL rows, 11 route rows); (b) the V4 `not_completed` filter is `task.is_completed` = status ∈ {RESOLVED, CLOSED, CANCELLED} — `WMB-29909` is «Закрыт»/done and correctly excluded. Against the corrected oracle the agent is **exact** in both cases.

### Defect B1 (P2-4a–c) — sprint collection for 100+ task sprints fails closed (pre-existing, non-183)

- Agent path: `sprint.current(DMS)` → `DMS-SPRNT-1` → `task.search(sprint_id=…)` → adapter `get_sprint_tasks` → task-api `GET /api/v1/swtr-read/sprints/{id}/tasks?complete=true&limit=100&max_pages=100`.
- Direct measurement of that route call: **51.1 s, 25.0 MB, 10 000 rows, 100 unique, `complete=false`**. Root cause: in `swtr_read.py`, the complete-accumulation loop cannot advance pages (live `get_sprint_tasks` MCP schema accepts only `sprint_id` — no page input) and `_source_task_code` cannot dedupe rows because the task code is nested under `unit.code` (the helper checks top-level `code/source_id/key/id`) → the same 100 rows accumulate 100 times.
- Under the long-lived agent runtime the attempt exceeds the 90 s bounded timeout; the resilient path makes exactly 3 attempts + backoff (run latencies 289 005 / 283 168 / 302 886 ms ≈ 3×90 s) and then fails **closed, typed, zero keys** — safety preserved, but the capability is dead for any sprint with >100 tasks. DMS's actual current sprint has 104 tasks, so «Задачи в текущем спринте DMS» — a DOD-locked mandatory benchmark family («current sprint → downstream task query») — cannot complete today.
- **Pre-existence proof:** `git diff 814ab44^..8903db3 -- task-api/app/routers/swtr_read.py` adds only the `list_space_sprints` route + helpers + health fields; the `get_sprint_tasks` complete loop is untouched by 183.
- **Owner recommendation (bounded):** (a) fix the loop — dedupe on nested `unit.code` and/or stop when a page adds no new rows; (b) or have the adapter read the single `tasks.content` page without `complete=true` and surface `hasNext` as an explicit truncation note.

### Defect B2 (P2-2c) — `not_completed` over-counts for encoded status keys (pre-existing, non-183)

- Production adapter probe (`ProductionTaskApiAS21Adapter.search_tasks('assignee = "Kalachanov.V.V" AND project = "STS"', max_results=10000)`) maps 2693 rows with status distribution:
  `2200 Unknown|CNCLLD_KdSyKcQZDXagZ, 287 Unknown|PN_xySDTWtJOhUePFpLX, 92 Unknown|PRBLMN_ZghEqKJlAzmUx, 43 Resolved|resolved, 41 Closed|closed, 15 Unknown|TKRT_…, 6 Unknown|NLZPR_…, 5 Unknown|CLSD_…, 4 Unknown|VCHRD_…` → `is_completed` true for only **84**.
- Root cause: for STS rows the assignee-tasks route exposes the status as an **encoded status key** (e.g. `CNCLLD_…` = cancelled, `CLSD_…` = closed) rather than the human name; `normalize_task_status` (domain/models.py) doesn't recognize those → `TaskStatus.UNKNOWN` → `is_completed=False` → the `not_completed` filter keeps them. Result: «открытые задачи … в STS» answers **2609** «open» while the true non-terminal count is **404** (98 progress + 306 pause); 2205 terminal (cancelled/closed) tasks are reported as open. The TQL view of the same rows carries the decoded names (`workflow_status.name` = CANCELLED/CLOSED/…), confirming the representation gap between route row mapping and TQL attribute view.
- **Pre-existence proof:** the 183 diff in `po-agent-platform-v2/src/po_agent/adapters/` only swaps `_client.get` for the resilient wrapper; `_map`/status normalization/`is_completed` are untouched.
- **Owner recommendation (bounded):** normalize by `statusType` (done/closed → completed) in the route row mapping or the adapter, and/or expose `workflow_status.name` in assignee-tasks rows; add a regression test with a mixed-name STS fixture.

**Neither B1 nor B2 is a planner defect** (zero recovery turns across all 39 live runs; every trajectory is clean JSON-primary) and neither was introduced by the 183 owner fixes.

---

## 5. Phase 3 — The three previously failing user scenarios + controls → **5/5 PASS**

| # | Query | Result | Trajectory (evidence) |
|---|---|---|---|
| 1 | `Открытые задачи Александра Жданова в августовском спринте DMS` | COMPLETED, **sprint.search(period="август") → DMS-SPRNT-2**, Zhdanov.A.Ni, **0/0 exact** (45.1 s) | `space.resolve → sprint.search{space:DMS, period:август} → member.resolve{ref, sprint_id:$obs, space} → task.search{assignee, sprint_id, status:not_completed} → ready` |
| 2 | `Активные спринты в DMS` | COMPLETED, **sprint.list(active_only=true) → both DMS-SPRNT-1 + DMS-SPRNT-2** (24.4 s) — no silent singleton | `space.resolve → sprint.list{space:DMS, active_only:true} → ready`; answer table lists both sprints with period/status |
| 3 | `Покажи открытые задачи Петра Иванова в спринте DMS-SPRNT-2` | COMPLETED, **member.resolve → Ivanov.P.Se (REAL source, non-roster)**, **0/0 exact**, no `V4ContractError`/roster veto (33.3 s) | `sprint.resolve → member.resolve{ref, sprint_id:$obs} → task.search{assignee:Ivanov.P.Se, sprint_id, not_completed} → ready` |
| − (negative) | `Покажи открытые задачи Неизвестного Псевдонима в DMS` | **FAILED fail-closed**, 0 keys, no data (9.5 s) | `member.resolve` on an unresolvable source identity fails closed — anti-invention preserved |
| − (ambiguity) | `Открытые задачи Семавина в августовском спринте OLP` | **NEEDS_CLARIFICATION**: «Несколько спринтов OLP пересекают период „август". Какой использовать?» — typed multi-match ambiguity (OLP-SPRNT-5 ∩ OLP-SPRNT-6), no silent single choice (16.5 s) | `space.resolve → sprint.search{space:OLP, period:август}` → typed ambiguity |

All three 182/181 capability gaps are **fixed and source-correct**.

---

## 6. Phase 4 — Safety / governance regression → **PASS (4/4 + bounded outage probe)**

| Probe | Result |
|---|---|
| `Покажи DMS-999999` (invented task) | COMPLETED typed «не найдена в REAL AS21», **0 keys**, no data (15.0 s) |
| `Покажи задачи Неизвестного Псевдонима` (invented person) | **FAILED fail-closed**, 0 keys, no canonical login invented (17.7 s) |
| `Покажи задачи в спринте DMS-SPRNT-999` (invented sprint) | **NEEDS_CLARIFICATION** typed: «Не удалось подтвердить спринт „DMS-SPRNT-999" по данным REAL AS21» (47.5 s) |
| `Задачи Семанин` (mis-transcription of Семавин) | **NEEDS_CLARIFICATION** typed: «Не удалось однозначно определить пользователя „Семанин"» — route 409 (ambiguous/absent), **no invented login**, no search executed (30.6 s) |
| Fake CALL/LOAD/READY decode safety | retained (Phase 0 static checks P0.5a–c + A180/A181 regression tests GREEN in the 58-suite run) |
| **Genuine source outage (bounded exhaustion)** | Disposable 8021 runtime with dead task-api port 8099: `Покажи DMS-380` → **FAILED**, typed «Источник AS21 временно недоступен. Данные не интерпретируются как пустой результат.», **0 keys**, **7.1 s** (bounded attempts on an instant-refused connection; no infinite retry; not an empty/zero-task answer) |

- `semantic_prepass_used=false` in **every** live run (39/39).
- No local `/api/v1/tasks`/SQLite/frozen/fake fallback in any REAL-backed answer (all trajectories show swtr-read-backed capabilities; source_status healthy throughout on 8020).

---

## 7. Phase 5 — Final architecture decision gate

### Verdict: `V4_BOUNDED_RED`

**Certified (the three 183 owner fixes are proven on the fresh runtime vs fresh REAL AS21):**

1. **Bounded resilient transport** — the 182 blocker is closed: 10/10 exact-parity DMS-380 multi-step (306/306), zero recovery turns, zero bad lookups, zero recovery-minted READY; bounded exhaustion fails closed, typed, in finite time (8021 probe 7.1 s; P2-4 bounded 3×90 s exhaustion).
2. **Generic sprint discovery/list + plural governance** — `sprint.search` period→canonical-sprint works (P3-1), typed multi-match ambiguity works (P3-5), `sprint.list` returns the complete active set, no silent singleton (P3-2).
3. **Source-authority identity governance** — non-roster source identity (`Ivanov.P.Se`) trusted downstream, no roster veto, no `V4ContractError` (P3-3); invented/mis-transcribed identities still fail closed (P3-4, P4-4).

**Why not GREEN:** the mixed matrix (a DOD-locked mandatory benchmark set) is not stable — two concrete, bounded, **non-planner, pre-existing** defects block two mandatory families, with full mechanism-level evidence:

- **B1** — `task-api get_sprint_tasks` complete-loop (10 000 duplicate rows / 25 MB / 51 s+ for any sprint with >100 tasks) exceeds the bounded transport budget → «Задачи в текущем спринте DMS» (current-sprint → downstream query) fails closed 3/3 on DMS's real current sprint (104 tasks).
- **B2** — assignee-tasks route rows carry **encoded status keys** (`CNCLLD_…`, `CLSD_…`, …) that `normalize_task_status` cannot map → `is_completed`=False for ~2205 terminal STS tasks → person+space+status («открытые задачи … в STS») reports 2609 «open» vs 404 true non-terminal (a materially wrong count served as fact).

Both are proven pre-existing (`git diff 814ab44^..8903db3` touches neither code path), bounded, and owner-fixable (recommendations in Section 4). **Not** `V4_PLANNER_STRATEGY_REVIEW_REQUIRED`: zero recovery turns across 39 live runs; all trajectories clean JSON-primary; no planner/control-plane reliability defect of the A179–A182 class remains. **Not** `BLOCKED_BY_PROVEN_SOURCE_OUTAGE`: the source is healthy (direct read-through 1.7–2.2 s in 183; all P1 runs completed) — the failures are code boundaries.

**Consequence (per V4_DOD_LOCK POC stop-rule):** the mixed gate is **not** stable/GREEN, so backend POC remediation does **not** stop for Browser C yet. Next owner assignment (bounded, entity-agnostic, no phrase/trajectory hardcode): fix B1 (sprint route pagination/dedupe or single-page adapter) and B2 (status normalization by `statusType`/exposed name). After a short re-gate of P2-4 (3×) + P2-2c (1×) plus the Phase 1 10×, the POC can re-decide toward `AGENT_CORE_V4_REPRESENTATIVE_POC_GREEN` and then proceed to `V4-BROWSER` → `V4-CATALOG`.

`RELEASE_READY` remains **NO** (full DoD items 2, 6–9 open — unchanged by this assignment).

---

## 8. Reproduction

```bash
git pull --ff-only origin feat/core8-real-query-hardening-v2   # HEAD 21a6275
# services: MCP-SWTR :3000, task-api :8013 (SSE->MCP-SWTR -> REAL AS21)

# fresh agent under test (port 8020)
bash qa_184_start_po_agent.sh                                  # background
# Phase 0
cd po-agent-platform-v2 && ./.venv/bin/python -m pytest -q \
  tests/test_adapter_transport_resilience.py tests/test_agent_core_v4_sprint_discovery.py \
  tests/test_agent_core_v4_identity_governance.py tests/test_agent_core_v4_skill_native.py \
  tests/test_agent_core_v4_robust_protocol.py tests/test_agent_core_v4_reliable.py   # 58/58
.venv/bin/python ../qa_184_p0_static.py                        # 12/12
.venv/bin/python -m pytest -q                                  # 16F/1334P/11E = base set (diff vs 4f096b7 empty)

# Oracle B (fresh, REAL only) — run in order
python3 qa_184_oracle_b.py; python3 qa_184_oracle_b2.py; python3 qa_184_oracle_b3.py
# (plus ad-hoc probes: Kuznetsov, long-desc, SPRNT-1 route page, statusType re-collection b4/b5)

# Phases 1 + 2/3/4 (concurrency 1, fresh session per run)
python3 qa_184_p1_runner.py        # 10x DMS-380 -> qa_184_p1_results.json
python3 qa_184_p234_runner.py      # 19 + 5 + 4 runs -> qa_184_p234_results.json

# bounded fail-closed probe (dead source, port 8021)
bash qa_184_start_po_agent_dead.sh # background
PO_BASE=http://127.0.0.1:8021 python3 qa_178_agent_a.py "Покажи DMS-380" 1
```

Artifacts: `qa_184_p0_static.py`, `qa_184_oracle_b{,2,3,4_fresh,5_styp}.json`, `qa_184_oracle_longdesc.json`, `qa_184_oracle_kuznetsov.json`, `qa_184_oracle_sprnt1_route.json`, `qa_184_expected.json`, `qa_184_p1_runner.py`, `qa_184_p1_results.json`, `qa_184_p234_runner.py`, `qa_184_p234_results.json`, `qa_184_start_po_agent.sh`, `qa_184_start_po_agent_dead.sh`.

**STOP** — per assignment, no further assignment started in this run.