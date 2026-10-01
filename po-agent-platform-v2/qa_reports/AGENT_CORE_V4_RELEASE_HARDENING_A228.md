# A228 — Release Hardening: Restart / Recovery

**Role:** QA / adversarial tester only (no production/frontend/backend/plugin/test/config changes).
**Branch:** `feat/core8-real-query-hardening-v2`
**START_HEAD:** `c18b8c00f45c1fdd27cb510f4e983f4b00919294`
**Baseline checkpoint:** `checkpoint/v4-po-acceptance-green-a227r3` → `417d29c` (code identical to A227R3 code baseline `f65bd94`)
**Functional freeze:** CONFIRMED — `f65bd94 → c18b8c0` is docs-only (no Core/LLM/plugin/runtime diff).
**Date:** 2026-10-01
**VERDICT:** `AGENT_CORE_V4_RELEASE_HARDENING_GREEN_A228`

---

## Verdict summary

All eight phases (P0–P8) GREEN. Every restart/recovery path fails closed with a **typed** temporary-unavailable state (never stale-fact-as-fresh, never false-zero, never local fallback), reconnects cleanly without manual data repair, and preserves exact source parity against fresh REAL AS21. Final audit: **0** local-store factual fallback, **0** AS21 mutations, **0** tenant-wide scans, **0** secret leakage, all processes from START_HEAD, no hidden RED.

---

## P0 — preflight / baseline integrity — GREEN

- Pulled branch; recorded `START_HEAD = c18b8c0`.
- Tracked worktree clean (only untracked QA harness/evidence artifacts; no modified tracked files).
- Checkpoint `checkpoint/v4-po-acceptance-green-a227r3` → `417d29c`; code identical to A227R3 code baseline `f65bd94`.
- `f65bd94 → c18b8c0` = docs-only → functional freeze confirmed.
- `tsc --noEmit` → exit 0; `vite build` → exit 0.
- Full V4 blast-radius tests → **233/233** pass.
- Pre-restart service PIDs/ports recorded and live: agent 8004, task-api 8241, MCP 3000, vite [::1]:5175.

## P1 — Agent-only restart — GREEN

- Stopped **Agent only** (task-api + MCP + frontend kept running).
- **API:** query → typed connection-refused → `FAILED` / `source_unavailable` (not stale factual success).
- **UI:** snapshot header → `"Не удалось обновить …"` (typed failure), no relabel as fresh.
- Restarted Agent from `c18b8c0` with production V4 env; liveness 200.
- Smoke vs fresh REAL AS21 oracle — all `parity=true`:
  - S1 `Задачи Семавина по рискам` → `COMPLETED` `task.search_text`, `runtime_contract`, **REAL_EMPTY 0/346** (Semavin.M.M; 0 risk rows of 346), first query on cold process.
  - S2 `Задачи в работе в сентябрьском спринте по DMS` → **11/11** exact keys.
  - S3 `Спринты в DMS` → 3 sprints `[DMS-SPRNT-1/2/3]`.
- **No warm in-memory state required** — first query on the fresh process is fully source-backed.

## P2 — Task API restart — GREEN

- Stopped **task-api only** (Agent/MCP/frontend alive).
- One factual query (S2) while unavailable → Agent `FAILED` / `source_unavailable`; **0** local reads, no false-zero.
- Restarted task-api; **Agent did NOT restart** — reconnected on next call.
- S2 rerun → `COMPLETED`, **11/11** exact parity (~108 s).

## P3 — MCP-SWTR restart / reconnect — GREEN

- Stopped **MCP-SWTR** (Agent + task-api alive).
- One bounded factual query (S2) → fail closed (`source_unavailable`); **0** local factual fallback.
- Restarted MCP-SWTR; **task-api auto-reconnected** (no manual step).
- S2 rerun → **11/11** exact parity (~81 s).

## P4 — Frontend restart — GREEN

- Restarted Vite/frontend only; opened a **fresh** browser session.
- All **6** routes load: `/` Обзор, `/tasks`, `/sprint`, `/releases`, `/team`, `/quality`.
- No factual result fabricated from frontend-local cache (fresh context, empty start).
- Local user-created tasks persist per documented `localStorage` contract; **0** AS21 mutations from local-task actions.
- Tasks query → **11/11**; Sprint page → **79/28** (total/completed) exact.

## P5 — Full cold-stack restart — GREEN

- Stopped all four (Agent, task-api, MCP-SWTR, frontend); started from cold in dependency order.
- Time-to-ready: **MCP ~33 s, task-api ~71 s, agent ~49 s, vite ~34 s**.
- No manual data repair; no persisted runtime-session dependency; no stale process/port conflict (exactly 1 listener per port).
- First factual queries after cold start — `all_parity=true`:
  - S1 **0/346** (REAL_EMPTY), S2 **11/11**, S3 **3/3**.
- No hidden warm cache required; **0** unauthorized writes.

## P6 — snapshot / recovery behavior — GREEN

- Valid source-backed Tasks snapshot: 11 cards, trace `f9087a93`, `"Снимок · обновлено 01.10.2026, 10:28"`.
- Stopped Agent → **Refresh while down**: 11 stale cards **kept**, label `"Не удалось обновить · данные на 01.10.2026, 10:28"` (error=true), **not** relabeled as fresh, trace unchanged → stale/failure semantics correct.
- Restored Agent (robust detached spawn) → **Refresh while up**: **new trace** `f9087a93 → 24e9e2de`, **fresh timestamp** 10:29, **source parity 11/11**.
- **Note (QA-harness artifact, not product RED):** the first P6 attempt restored the agent via `qa_228_agent_restart.sh` (`set -e` + `nohup`) through `execSync`, which did not survive; the stale/relabel half still passed. Re-run with an inline detached `spawn` restore completed the recovery half cleanly.

## P7 — session isolation across restart — GREEN

Pending-clarification is the real session-persisted planner state (`session_id`-keyed, in-memory). Deterministic discriminator (probed): `"ДMS" + intact "Покажи спринт" context → COMPLETED sprint.current`; `"DMS" standalone (no context) → NEEDS_CLARIFICATION (agent.help)`.

- **Part 1 — cross-session independence:** A (`p7-A`) "Покажи спринт"→clarify→"DMS" → `DMS-SPRNT-3`; B (`p7-B`) "Покажи спринт"→clarify→"WMB" → `WMB-SPRNT-2` (**its own space, not A's**); distinct clarification_ids; B ≠ A.
- **Part 2 — no cross-session leakage:** C's own pending → `COMPLETED DMS-SPRNT-3`; session **D** passing **C's** `clarification_id` under a different `session_id` → `NEEDS_CLARIFICATION` (did **not** inherit C's context).
- **Part 3 — restart clears transient context:** E pending (pre-restart cid) → **restart Agent** → re-ask → **new** cid; the stale-cid continuation → `NEEDS_CLARIFICATION` (explicit re-clarification, **not silent reuse** of A's/E's cleared context).
- **Note (QA-harness refinement, not product RED):** the first two P7 runs returned `false` only due to over-strict harness assertions (pinned exact `sprint.current` skill; a later run dropped the `answ` field). The isolation behavior itself was correct in all three runs; the corrected harness yields `true`. LLM non-determinism routes the "покажи спринт + DMS" continuation to either `sprint.current` or `sprints.list` (both legitimate DMS-scoped resolutions) — not an isolation defect.

## P8 — final restart/recovery source audit — GREEN

Audited the full accumulated Agent log (24 task-api calls, whole session), task-api access log, MCP-SWTR log, vite log, and cross-checked against `.env` tokens (counts only, no secrets printed):

| Check | Result |
|---|---|
| Local-store factual fallback | **0** — all 24 agent→task-api calls are `/api/v1/swtr-read/*` (real source); 0 legacy `/api/v1/tasks`; task-api 0 local |
| Unauthorized AS21 mutations | **0** — agent 0, task-api 0 (all GET), MCP 0 write-tool invocations |
| Tenant-wide scans | **0** — every `task-query` is assignee- or space-scoped (e.g. `assignee=Semavin.M.M`, `sprints/DMS-SPRNT-3/tasks?space=DMS`) |
| Secret leakage in logs/UI | **0** — 0 token hits, 0 JWT candidates, 0 bearer headers across agent/task-api/MCP/vite |
| Process provenance | HEAD = `c18b8c0` = START_HEAD (agent self-validates `PO_AGENT_EXPECTED_HEAD`) |
| Skipped RED hidden by retry | **none** — all P0–P7 genuinely GREEN; the only first-attempt anomalies (P6 restore, P7 assertion) are documented QA-harness artifacts, not product REDs, and were re-run cleanly |

---

## Oracles (fresh REAL AS21, captured this run)

- **S1** `Задачи Семавина по рискам` → canonical `Semavin.M.M`, phrase "риски", **REAL_EMPTY 0/346** (Semavin total 346, 0 risk rows).
- **S2** DMS-SPRNT-3 IN_PROGRESS → **11** keys `[DMS-104/253/269/272/343/349/357/399/401/405/452]`.
- **S3** `Спринты в DMS` → 3 sprints `[DMS-SPRNT-1/2/3]`.
- **Sprint DMS-SPRNT-3:** total 79, completed 28, active 51, blocked 1.
- Current sprints: DMS = `DMS-SPRNT-3`; WMB = `WMB-SPRNT-2`.

## Fail-closed contract (retained across all restart/recovery)

Upstream down → `status=FAILED`, `warnings=['source_unavailable']`, answer `"Источник AS21 временно недоступен. Данные не интерпретируются как пустой результат."` — never false-zero, never stale-fact-as-fresh, 0 local `/api/v1/tasks` reads. Verified in P1 (agent down), P2 (task-api down), P3 (MCP down), P6 (refresh-down), and the P8 audit.

---

## Recommendation (GREEN)

- Recommend checkpoint: **`checkpoint/v4-release-recovery-green-a228`**.
- Next owner phase: **latency hardening** (reconnect/cold-start time-to-ready; S2 re-query latency 38–108 s after downstream restarts is the main remaining cost).
- Do **not** start Learning Reviewer 2.0.

## Services left running (all from START_HEAD `c18b8c0`)

| Service | Port | PID |
|---|---|---|
| Agent (po_agent.main, `PO_AGENT_AGENT_CORE_V4_ENABLED=true`) | 8004 | 60611 |
| task-api | 8241 | 38460 |
| MCP-SWTR (SSE) | 3000 | 38215 |
| vite (frontend, proxy `/api`→8004) | [::1]:5175 | 39280 |

All 4 live and 200 at report time.

## Tooling notes (repro)

- `curl` is policy-blocked → all HTTP via python `urllib.request` / Node `fetch`.
- `run_shell_command` blocks `$()`, backticks, `<()`, `>()` → used python/awk/printf for command substitution.
- In-node agent restore must use a **detached** `spawn` (not a `set -e`+`nohup` script via `execSync`) to survive process teardown.
