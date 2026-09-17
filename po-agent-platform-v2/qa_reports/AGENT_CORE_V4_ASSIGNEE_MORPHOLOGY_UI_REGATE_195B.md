# Assignment 195B — Agent Core V4 Assignee Morphology UI Regate

**Verdict: `AGENT_CORE_V4_TASK_WAVE_REOPENED_RED`**
**Classification: `RED_MORPHOLOGY_GROUNDING_GUARD`**

- **START_HEAD:** `6a08167c54d6dafb62dc7ce0d3af3eefa772786f` (branch `feat/core8-real-query-hardening-v2`)
- **Permanent rollback:** `0f03fca14fe078c86dca961362915e10cc985401`
- **Date:** 2026-09-17
- **Role:** QA/adversarial tester + service operator (no production changes; only QA artifacts + this report)

## Test stack (fresh, at START_HEAD)

| Service | Port | PID | Health |
|---|---|---|---|
| PO Agent (uvicorn, `PO_AGENT_AGENT_CORE_V4_ENABLED=true`, model `Qwen/Qwen3.8-27B`) | 8212 | 95088 | `/live` 200; `/health` (readiness) HANGS — see Finding F1 |
| Task API (uvicorn, SSE → MCP) | 8241 | 95082 | `/api/v1/swtr-read/health` 200 `{"status":"connected","tool_count":48}` |
| MCP-SWTR (SSE, reused from A195) | 3000 | 45891 | serving task-api (48 tools) |
| Frontend (Vite, existing A195 process; proxy → 8212) | 5175 | 22389 | `GET /` 200 |

Worktree note: 3 pre-existing local QA/runtime artifacts were present (untracked/uncommitted, not production): root `GIGACODE.md` (local QA memory notes), `po-agent-platform-v2/.po_agent/learned_policies.json` (runtime learning state), `po-agent-platform-v2/frontend/vite.config.ts` (QA proxy edit 8004→8212). No production files modified.

## Phase 1 — REAL AS21 oracle (live source via fresh task-api 8241, agent output NOT used as oracle)

| Person (canonical login) | Space | n_tasks | Key set | Route latency |
|---|---|---|---|---|
| Zhdanov.A.Ni | DMS | 7 | DMS-1, DMS-103, DMS-154, DMS-371, DMS-6, DMS-69, DMS-71 | 3.4s |
| Garanin.R.V | DMS | 8 | DMS-243, DMS-248, DMS-262, DMS-326, DMS-36, DMS-402, DMS-405, DMS-93 | 3.4s |
| Semavin.M.M | (all) | 312 | saved in `qa_195b_p5_oracle.json` | 2.1s |
| DMS open (statusType progress/pause) | DMS | 84 | saved in `qa_195b_p5_oracle.json` (408 total; 134 done; 190 rows without workflow_status attribute → not-open per B2 fail-closed) | 2.2s |

Source drift vs A190/A191: Semavin 310 → 312 (live truth).

## Phase 2 — API morphology matrix (fresh sessions, concurrency 1, via public `POST /api/v1/query`)

| # | Query | Status | Loaded skill | Planner reference arg | Rejected value | Failure point | Source confirmation | Parity |
|---|---|---|---|---|---|---|---|---|
| Z1 | `Задачи Александра Жданова в DMS` | **FAILED** | task.search_assignee | `Александр Жданов` | same | `_validate_call_literals` generic `reference` guard, `agent_core_v4_reliable.py:427` | never reached (rejected pre-call) | 0 |
| Z2 | `Задачи Жданова в DMS` | COMPLETED | task.search_assignee | (grounded surname path) | — | — | Zhdanov.A.Ni confirmed | **7/7 EXACT** |
| Z3 | `Покажи задачи Александру Жданову в DMS` | **FAILED** | task.search_assignee | `Александр Жданов` | same | same guard | never reached | 0 |
| Z4 | `Что делает Александр Жданов в DMS` | COMPLETED | task.search_assignee | `Александр Жданов` (verbatim in query) | — | — | Zhdanov.A.Ni | **7/7 EXACT** |
| Z5 | `Задачи Zhdanov.A.Ni в DMS` | COMPLETED | task.search_assignee | canonical login | — | — | Zhdanov.A.Ni | **7/7 EXACT** |
| G1 | `Задачи Родиона Гаранина в DMS` | **FAILED** | task.search_assignee | `Родион Гаранин` | same | same guard | never reached | 0 |
| G2 | `Задачи Гаранина в DMS` | COMPLETED | task.search_assignee | (grounded surname path) | — | — | Garanin.R.V | **8/8 EXACT** |
| G3 | `Покажи задачи Родиону Гаранину в DMS` | **FAILED** | task.search_assignee | `Родион Гаранин` | same | same guard | never reached | 0 |
| G4 | `Что делает Родион Гаранин в DMS` | COMPLETED | task.search_assignee | `Родион Гаранин` (verbatim in query) | — | — | Garanin.R.V | **8/8 EXACT** |
| G5 | `Задачи Garanin.R.V в DMS` | COMPLETED | task.search_assignee | canonical login | — | — | Garanin.R.V | **8/8 EXACT** |

**Score 6/10.** Every failure carries the exact backend error (captured in response `data._agent_core_v4.error`):

```
planner literal is not grounded in user query: reference=Александр Жданов   (Z1, Z3 — 2/2 each)
planner literal is not grounded in user query: reference=Родион Гаранин     (G1, G3 — 2/2 each)
```

All 4 failures reproduced on a second independent pass (reproducibility 2/2 per case; deterministic, not LLM noise): `qa_195b_p2_rerun_errors.json`.

## Phase 3 — Grounding forensics (read-only)

Guard chain for `member.resolve.reference` vs `task.search_assignee.reference` in `agent_core_v4_reliable.py`:

- `:396` `_validate_call_literals`
- `:421` `key == "reference" and capability_id == "member.resolve"` → `_reference_is_safe_normalization` (`:382`), which is morphology-aware:
  1. `_literal_is_query_derived` (substring / single-token prefix)
  2. `_reference_is_query_derived_person` — every name token matched against query tokens under `_token_equivalent` (prefix OR common-prefix ≥ max(4, shorter−1)); would ACCEPT `Александр Жданов` against `Задачи Александра Жданова в DMS` (ЖДАНОВ~ЖДАНОВА, АЛЕКСАНДР~АЛЕКСАНДРА)
  3. fallback: `_team_candidates(raw)` == exactly 1 roster entry
- `:427` generic branch `key in {"reference","space","sprint_id","release_id","task_key","product"}` → **`_literal_is_query_derived` only** (`agent_core_v4.py:224`): exact substring OR single-token long prefix. A two-token nominative name that is not a verbatim substring of the inflected query is **always rejected**.

Per-failure record (all 4 failures):

| Query | Planner-emitted person value | Normalized to nominative? | Rejecting guard/branch | Trusted source identity already confirmed? |
|---|---|---|---|---|
| `Задачи Александра Жданова в DMS` | `Александр Жданов` | yes (genitive → nominative) | `:427` generic, `_literal_is_query_derived` = False (not a substring; multi-token) | **No** — `member.resolve` never invoked; rejection precedes any source call |
| `Покажи задачи Александру Жданову в DMS` | `Александр Жданов` | yes (dative → nominative) | same | No |
| `Задачи Родиона Гаранина в DMS` | `Родион Гаранин` | yes (genitive → nominative) | same | No |
| `Покажи задачи Родиону Гаранину в DMS` | `Родион Гаранин` | yes (dative → nominative) | same | No |

**Defect class:** generic morphology grounding — NOT identity resolution (A195's `_authorized_identity_hint` team-directory bridge is healthy and is never reached for these inputs), NOT planner normalization (nominative normalization is the correct, safe behavior), NOT source.

**Pre-dates A195 — proven:**
- The generic guard line was introduced in `de75115` (2026-09-11, "fix(v4): harden source identity and observation binding") — before the plugin wave `2c2b75d` (2026-09-16) that made it reachable via `task.search_assignee.reference`, and before A195 (test base `b3180f5`).
- The A195 report itself (`AGENT_CORE_V4_TASK_ASSIGNEE_FINAL_REGATE_195.md`, lines 83/85/187) documents the identical case: `Задачи Александра Жданова` | FAILED | "V4 grounding guard (pre-existing)… same defect class as A172/174/175 (person morphology) and is NOT introduced by A195."
- A195's "Zhdanov 10/10 exact" was measured on word orderings that avoid the guard (`Задачи Жданова Александра`, `Задачи Жданов`); the user-facing canonical ordering `Задачи Александра Жданова` was already failing in A195. This assignment confirms the user-visible gap is exactly that ordering class, now with space suffix `в DMS` and for both target people.

## Phase 4 — Browser C (real UI, Vite 5175 → agent 8212; Playwright, fresh conversation per case)

| Case | Query | Backend status | UI-visible message | V4 panel | Exact backend cause visible in UI? |
|---|---|---|---|---|---|
| Z1-full | `Задачи Александра Жданова в DMS` | FAILED | "Agent Core v4 не смог безопасно завершить траекторию." + "Agent Core v4 · FAILED · 6394 ms" | `ERROR`, Evidence 0 | **No** — `planner literal is not grounded…` is only in response JSON (`data._agent_core_v4.error`); `V4ResultPanel.stateFor` maps to generic `ERROR` |
| Z2-surname | `Задачи Жданова в DMS` | COMPLETED | "У Жданова (Zhdanov.A.Ni) в DMS найдено **7 задач**…" + 7 keys | `SUCCESS_WITH_DATA`, widget `task_table` | n/a |
| G1-full | `Задачи Родиона Гаранина в DMS` | FAILED | "Agent Core v4 не смог безопасно завершить траекторию." + "Agent Core v4 · FAILED · 6740 ms" | `ERROR`, Evidence 0 | **No** |
| G2-surname | `Задачи Гаранина в DMS` | COMPLETED | "У Гаранина (Garanin.R.V) в пространстве **DMS** найдено **8 задач**…" + 8 keys | `SUCCESS_WITH_DATA`, widget `task_table` | n/a |

Both full-name Browser C cases fail due to the generic morphology/grounding guard → per spec rule the verdict must be `AGENT_CORE_V4_TASK_WAVE_REOPENED_RED`. Frontend request payloads captured (`ui-*` session ids, single `POST /api/v1/query` per turn): `qa_195b_p4_results.json`.

## Phase 5 — Tiny regression (one run each)

| Case | Query | Result |
|---|---|---|
| R1 multistep | `Покажи DMS-380 и затем задачи его исполнителя` | COMPLETED; DMS-380 lookup (Closed, mTLS) → assignee Semavin.M.M → **312/312 unique keys EXACT** vs live oracle (evidence lists DMS-380 twice — lookup + search, cosmetic dup, see F3) |
| R2 DMS open | `Открытые задачи в DMS` | COMPLETED; **84/84 EXACT** vs B2-semantics oracle (190 statusless rows correctly NOT counted open — B2 fail-closed retained) |
| R3 clarification continuation | turn1 `задачи Гаранина в сентябрьском спринте` → turn2 `DMS` | turn1 NEEDS_CLARIFICATION with non-null `clarification_id` (34a690bb); turn2 COMPLETED in same session — context restored, DMS-SPRNT-3 found (IN_PROGRESS, 13–27 сентября 2026). Consistent with A194 GREEN behavior |

No A188/A190/A191/A195 regression.

## Findings

- **F1 (primary defect, RED):** `task.search_assignee.reference` is validated by the generic `_literal_is_query_derived` guard (`agent_core_v4_reliable.py:427`), which lacks the morphology-aware person check that `member.resolve` gets (`:421` → `_reference_is_safe_normalization`, `:382`). Deterministic rejection of safe nominative-normalized full names in inflected (genitive/dative) queries. Pre-existing (guard since `de75115`, 2026-09-11; documented in A195 report; A172/174/175 lineage). UI hides the specific cause behind generic `ERROR`/answer text (Phase 4).
- **F2 (environmental/UX, non-blocking):** agent `/health` readiness probes the unscoped full-scan `task-query` route, which currently hangs >90s (intermittent 502 under load; DMS-scoped scan is 2.2s). Consequence: before the first query the UI runtime label shows `Legacy Harness` (health null), flipping to `Agent Core v4` after any V4 result. Same source-latency class as A182/A186. Queries themselves are unaffected.
- **F3 (cosmetic):** in the DMS-380 multistep trajectory the lookup target key appears twice in final evidence (lookup observation + assignee-search row). No factual error.

## Owner fix proposal (generic, entity-agnostic, no planner change)

In `_validate_call_literals` (`agent_core_v4_reliable.py:427`), route person-reference literals through the same morphology-aware check used by `member.resolve`: for `key == "reference"`, use `self._reference_is_safe_normalization(raw, query)` (which subsumes `_literal_is_query_derived`) instead of `_literal_is_query_derived(raw, query)`. Safety invariant preserved: the downstream plugin handler already re-validates the identity against REAL AS21 (`_authorized_identity_hint` is a hint only; `assignee-tasks` route resolves the canonical external id), so the guard remains anti-invention, not authoritative. Add a non-mocked regression test asserting `reference=Александр Жданов` is accepted for query `Задачи Александра Жданова в DMS` and still rejects invented two-token names not derivable from the query.

Secondary (owner's choice): bound or scope the `/health` readiness probe (e.g., space-scoped probe with short timeout) so UI pre-query label is not degraded by unscoped scan latency (F2).

## QA artifacts (untracked)

`qa_195b_start.sh`, `qa_195b_p2_runner.py`, `qa_195b_p2_results.json`, `qa_195b_p2_rerun_errors.json`, `qa_195b_z1_raw.json`, `qa_195b_oracle.json`, `qa_195b_p5_runner.py`, `qa_195b_p5_oracle.json`, `qa_195b_p5_dms_raw.json`, `qa_195b_p5_results.json`, `po-agent-platform-v2/frontend/e2e/qa195b-morphology.spec.ts`, `qa_195b_p4_results.json` (+ `.summary.json`), `po-agent-platform-v2/frontend/test-results/` (Playwright trace for the first, fixed-gate failed run).

## Services left running

- UI: http://127.0.0.1:5175 (PID 22389)
- PO Agent backend: http://127.0.0.1:8212 (PID 95088) — `/live` 200, `/version` 200; `/health` readiness hangs (F2)
- Task API: http://127.0.0.1:8241 (PID 95082) — `/api/v1/swtr-read/health` 200 connected, 48 tools
- MCP-SWTR SSE: http://127.0.0.1:3000 (PID 45891)
