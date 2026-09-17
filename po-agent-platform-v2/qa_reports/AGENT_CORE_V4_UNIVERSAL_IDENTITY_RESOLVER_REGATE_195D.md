# Assignment 195D — Agent Core V4 Universal Identity Resolver Re-Gate

**Verdict: `AGENT_CORE_V4_TASK_WAVE_GREEN`**

- **START_HEAD:** `2bb474aeaf8e13429785265145520683b99a54fe` (branch `feat/core8-real-query-hardening-v2`)
- **Permanent rollback:** `0f03fca14fe078c86dca961362915e10cc985401` / `checkpoint/v4-poc-green-a188`
- **Owner fix under test (since `749e993`):** `043823f` (generic morphology grounding seam), `e0fe313` (morphology regression tests), `ab71a8c` (restore universal source-backed assignee resolution in plugin handler), `f6e44ad` (universal resolver contract tests)
- **Date:** 2026-09-17
- **Role:** QA/adversarial tester + service operator (no production/test changes)

## Test stack (fresh, at START_HEAD)

| Service | Port | PID | Health |
|---|---|---|---|
| PO Agent (V4 pluginized, `Qwen/Qwen3.8-27B`) | 8212 | 34644 | `/live` 200; queries healthy |
| Task API (SSE → MCP-SWTR) | 8241 | 34638 | `/api/v1/swtr-read/health` 200 `{"status":"connected","transport":"sse","tool_count":48}` |
| MCP-SWTR (SSE, reused) | 3000 | 45891 | serving task-api |
| Frontend (Vite, proxy → 8212) | 5175 | 22389 | `GET /` 200 |

Worktree: only the 3 known local QA/runtime artifacts (root `GIGACODE.md` memory notes, `.po_agent/learned_policies.json` runtime state, `frontend/vite.config.ts` QA proxy edit). No production files modified.

## Phase 0 — architecture audit: PASS

- **Change boundary:** owner diff touches only `agent_core_v4_pluginized.py` (a generic runtime seam) and the task plugin handler `_task_live_handlers.py`, plus tests/spec. `agent_core_v4.py` (planner), completion machinery, skill catalog, prompts, adapters — **untouched**. No person-name/surname hardcodes anywhere in the diff; the seam operates on the argument name `reference` generically.
- **Contract:** `build_task_search_assignee` now calls `_resolve_assignee_identity` → `runtime._member_resolve({reference[, space]})` (the generic governed resolver) **before** any task collection; task search is issued only with the source-confirmed canonical identity (`assignee = "<canonical>"`).
- **Roster = hint, not population:** `_member_resolve` uses `_team_candidates` only as a fast disambiguation hint and still confirms the hinted login against REAL AS21 (`assignees/resolve`); on mismatch or zero/multi roster matches it falls through to contextual/global REAL AS21 resolution. A non-team person traverses the identical contract.
- **Clarification semantics:** `_member_resolve` raises typed `V4NeedsClarification` for empty/ambiguous/unconfirmed identities; the 409 source payload's `matches` become user options.
- **Hermes/plugin invariant intact:** no Agent Core planner/strategy/completion changes for identity behavior; no local-store fallback introduced.

## Phase 1 — focused tests: GREEN

- `test_v4_owner_fix_contracts.py` 8/8, `test_v4_pluginized_morphology_grounding.py` 6/6, `test_agent_core_v4_reliable.py` 7/7, `test_agent_core_v4_plugin_registry.py` 11/11 — **32/32**.
- Broad selection `-k "v4 and (assignee or identity or ground or plugin or reliable)"`: **45/45**.

## Phase 2 — REAL AS21 identity Oracle B (source routes only)

| Identity class | Login / identity | Live facts |
|---|---|---|
| Team | Zhdanov.A.Ni (Жданов Александр Николаевич) | DMS 7 tasks; all-spaces 10 (CRPV/DMS/STS/WMB) |
| Team | Garanin.R.V (Гаранин Родион Владимирович) | DMS 8; all-spaces 20 (DMS/OLP/STS) |
| Team | Agataeva.A.Z (Агатаева Айна Жумагалиева — from `team_members.yaml`, not guessed) | DMS 11; all-spaces 17 (DMS/STS) |
| Non-team | **Уткин — genuinely ambiguous at source**: `assignees/resolve?reference=Уткин` → 409 with 7 matches: `OUT-Kutkin.R.R, Sigutkin.P.E, SP-Tarchutkina.T.V, Tarchutkina.T.V, Utkin.A.A, Utkin.S.A, Utkin.S.V` | Utkin.S.A = 57 tasks (CRPV/STS/WMB) → chosen as unique follow-up control; Utkin.A.A = 22 (STS); Utkin.S.V = 0 |
| Unknown | Пупкин (verified absent) | `assignees/resolve` → 409, `matches=[]` |

Semavin.M.M all-spaces 312 (DMS/OLP/STS) and WMB-30000 files (5 Excel) refreshed for Phase 6.

## Phase 3 — API identity matrix (fresh sessions, concurrency 1): **9/9**

| # | Query | Expected | Got | Parity / detail |
|---|---|---|---|---|
| T1 | `Задачи Александра Жданова в DMS` (A195B RED case) | COMPLETED | **COMPLETED** | **7/7 EXACT**; planner ref `Александр Жданов`; canonical Zhdanov.A.Ni |
| T2 | `Задачи Родиона Гаранина в DMS` (A195B RED case) | COMPLETED | **COMPLETED** | **8/8 EXACT**; Garanin.R.V |
| T3 | `Задачи Жданова в DMS` | COMPLETED | COMPLETED | 7/7 EXACT |
| T4 | `Задачи Гаранина в DMS` | COMPLETED | COMPLETED | 8/8 EXACT |
| T5 | `Задачи Агатаевой` | COMPLETED | COMPLETED | **17/17 EXACT** (unscoped, DMS+STS) |
| T6 | `Задачи Айны Агатаевой` | COMPLETED | COMPLETED | **17/17 EXACT** (genitive natural order) |
| N1 | `Задачи Уткина` (non-team, ambiguous) | NEEDS_CLARIFICATION | **NEEDS_CLARIFICATION** | question "Не удалось однозначно определить пользователя «Уткин»." + all 7 REAL candidates as options; `clarification_id` non-null; warning `v4_capability_clarification`; **no task collection call** (log) |
| N2 | `Задачи Utkin.S.A` (non-team unique follow-up) | COMPLETED | **COMPLETED** | **57/57 EXACT**; `member_login=Utkin.S.A`, `source_reference=Utkin.S.A` in response data |
| X1 | `Задачи Пупкина` (invented) | typed safe result | **NEEDS_CLARIFICATION** | "Не удалось однозначно определить пользователя «Пупкин»." options=[] (source has no match); no fabricated tasks, no `AS21 invalid data` text |

All cases: `loaded_skills=[task.search_assignee]`, `semantic_prepass_used=false`, zero local `/api/v1/tasks` reads (agent log).

## Phase 4 — source/route provenance (agent log, per case)

Observed sequence for every factual completion:
```
task.search_assignee plugin
  -> GET /api/v1/swtr-read/assignees/resolve?reference=<hinted|raw>      (REAL AS21 identity via MCP-SWTR)
  -> GET /api/v1/swtr-read/task-query?limit=100&max_pages=100&assignee=<canonical>[&space=...]
```
- Team member (Zhdanov): resolve reference=`Zhdanov.A.Ni` (roster hint **confirmed by source call**, not used directly) → task-query.
- Non-team (Utkin.S.A): **no roster entry** — resolve reference=`Utkin.S.A` straight from REAL AS21 → task-query. Works entirely source-backed.
- Non-team ambiguous (Уткин): resolve reference=`Уткин` → 409 → clarification; **no** task-query call.
- Invented (Пупкин): resolve only → typed clarification.
- Local `/api/v1/tasks` reads: **0**; no SQLite/snapshot/fake fallback anywhere in the log.

## Phase 5 — Browser C adversarial matrix (real UI): **5/5** (all first attempts)

| Case | Query | Backend | UI rendering |
|---|---|---|---|
| B1 | `Задачи Александра Жданова в DMS` | COMPLETED (7) | factual `task_table`, V4 `SUCCESS_WITH_DATA` |
| B2 | `Задачи Родиона Гаранина в DMS` | COMPLETED (8) | factual `task_table`, `SUCCESS_WITH_DATA` |
| B3 | `Задачи Агатаевой` | COMPLETED (17) | factual `task_table`, `SUCCESS_WITH_DATA` |
| B4 | `Задачи Уткина` | NEEDS_CLARIFICATION | real clarification row with 7 source candidate buttons (not a red error panel); click `Utkin.S.A` → request carries same `session_id` + `clarification_id` + `clarification_option: "Utkin.S.A"` (context preserved) → **turn 2 COMPLETED, 57 evidence, `SUCCESS_WITH_DATA`** |
| B5 | `Задачи Пупкина` | NEEDS_CLARIFICATION | meaningful safe text "Не удалось однозначно определить пользователя «Пупкин».", `Evidence 0`, no error panel |

- `has_stale_source_error_text=false` in every case — no `AS21 вернул некорректные данные` / `invalid data` for ordinary ambiguity/not-found.
- One transient planner-routing anomaly was observed on an earlier exploratory run of B1 (planner asked a confused "status report space" question); API re-probe of the identical query: 3/3 COMPLETED with the correct `task.search_assignee` trajectory, and the official P5 run passed B1 on attempt 1. Classified as Qwen3.8 routing non-determinism (A179/A186 lineage), not an identity-resolver defect; no code involvement.

## Phase 6 — retained regression: GREEN

| Case | Result |
|---|---|
| R1 `Покажи DMS-380 и затем задачи его исполнителя` | COMPLETED; **312/312 unique keys EXACT** vs live Semavin.M.M oracle (evidence lists DMS-380 twice — lookup + search, cosmetic dup, A195B-class) |
| R2 `Вложения задачи WMB-30000` | COMPLETED; **5/5 attachment names EXACT** vs live files route (10 raw entries = 5×2 nested payload duplication in QA extraction) |
| R3 sprint clarification continuation | turn1 NEEDS_CLARIFICATION (non-null cid) → turn2 COMPLETED same session, DMS-SPRNT-3 found (A194 behavior retained) |
| R4 plugin/dummy-55 structural gate | `test_agent_core_v4_plugin_registry.py` **11/11** |

No full Task Wave rerun was needed (no retained case failed).

## GREEN checklist (per spec)

1. A195B morphology full-name failures fixed — T1/T2 API + B1/B2 UI, exact parity ✓
2. Configured team members work through generic source-backed identity resolution (roster hint always source-confirmed) — T1–T6 + Phase 4 logs ✓
3. Source-proven non-team identity works: `Utkin.S.A` 57/57 exact (API) and via UI clarification→option continuation (B4 turn 2, 57 evidence) ✓; genuinely ambiguous surname `Уткин` produced correct typed clarification with all real source candidates and a successful unique follow-up ✓
4. Ambiguity/not-found never collapse into generic source-corruption messaging — N1/X1/B4/B5 typed, `staleErr=false` ✓
5. Anti-invention + live-only invariants GREEN — invented person fails closed, 0 local store reads, REAL AS21 authoritative everywhere ✓
6. No retained regression — Phase 6 all GREEN ✓
7. Hermes/plugin extensibility intact — Phase 0 audit + 11/11 registry tests, no person-specific production hardcodes ✓

**Recommendation: Re-close Wave T (#1-20) and proceed to owner Wave S (#21-32 Sprint/flow) through the existing plugin surface.**

## Owner items (non-blocking observations)

- Transient Qwen3.8 planner-routing anomaly (one-off, A179/A186 class) remains an environmental reliability item, not a resolver defect.
- Agent `/health` readiness still probes the unscoped full-scan `task-query` route (A195B F2); UI pre-query label may show `Legacy Harness` until the first result. Unchanged by this fix; not in scope for this gate.

## QA artifacts (untracked)

`qa_195d_oracle.json`, `qa_195d_p3_runner.py`, `qa_195d_p3_results.json`, `qa_195d_p6_runner.py`, `qa_195d_p6_results.json`, `po-agent-platform-v2/frontend/e2e/qa195d-universal-resolver.spec.ts`, `qa_195d_p5_results.json`, `po-agent-platform-v2/frontend/test-results/`.

## Services left running

- UI: http://127.0.0.1:5175 (PID 22389)
- PO Agent backend: http://127.0.0.1:8212 (PID 34644) — `/live` 200
- Task API: http://127.0.0.1:8241 (PID 34638) — `/api/v1/swtr-read/health` 200, connected, 48 tools
- MCP-SWTR SSE: http://127.0.0.1:3000 (PID 45891)
