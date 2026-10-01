# A229 — Release Hardening: Latency Baseline & Bottleneck Analysis

**Verdict:** `AGENT_CORE_V4_LATENCY_BASELINE_GREEN_A229`
**Date:** 2026-10-01
**QA role:** measurement only, zero code changes
**Branch:** `feat/core8-real-query-hardening-v2`
**START_HEAD:** `1591eaefd0c3ea1c426b0ff3d1fab0657f22cc69` (docs-only over A228 `7f4bef7`: GIGACODE_NEXT_ACTION.md, PO_AGENT_HARNESS_EVOLUTION_PLAN.md, V4_DOD_LOCK.md)

---

## P0 — integrity / warm baseline

| Item | Result |
|---|---|
| Worktree | clean (untracked QA artifacts only) |
| Checkpoint `checkpoint/v4-release-recovery-green-a228` | **does not exist** (non-blocking, per A228; effective baseline = `7f4bef7`) |
| V4 regression | 233/233 passed |
| Frontend tsc + vite build | GREEN |
| Services (steady state) | agent 8004 (PID 74111 at start, later 96087 after P4 restart), task-api 8241 (PID 38460 → 96598 after P4), MCP-SWTR 3000 (PID 38215 → 97012 after P4), vite 5175 (PID 39280) |
| Source health | MCP 48 tools connected; all swtr-read routes 200 |
| Sample classes | P1 = warm steady-state (sequential, 1.5s spacing); P4 = explicit cold/reconnect; P5 = UI warm |

**Environment caveat (material to interpretation):** the LLM endpoint (`api.ai.sbt`, Qwen3.8-27B) had **two intermittent outage windows** during the session (3-15s typed fail-closed `v4_runtime_failure`, 0 source calls). All outage-affected runs (24) were re-run after endpoint recovery; the final 50-run matrix below is fully valid data. Outage frequency itself is reported as a bottleneck (rank 1b).

## P1 — representative query matrix (10 warm runs each, sequential)

Oracles (fresh, per gap batch): A = Semavin "риски" REAL_EMPTY (count 0); B = DMS-SPRNT-3 IN_PROGRESS = 11 keys (`complete_tasks`, `source_id`); C = [DMS-SPRNT-1/2/3]; D = WMB Kalachanov route returns 5 tasks but **all terminal** (Закрыт/Решен) → true open = 0 (route `status=not_completed` is not server-side filtered; client-side terminal classification applied to the oracle); E = DMS-380 (`unit.summary` provenance).

| Sc | Query | n | wall min | p50 | p90 | max | status | parity | LLM calls | src calls |
|---|---|---|---|---|---|---|---|---|---|---|
| A | Задачи Семавина по рискам | 10 | 19.2s | **38.0s** | 54.4s | 54.4s | 10 COMPLETED | 9/10* | 4-6 | 2-3 |
| B | Задачи в работе в сентябрьском спринте по DMS | 10 | 27.1s | **39.3s** | 59.8s | 59.8s | 10 COMPLETED | 10/10 | 5-6 | 3 |
| C | Спринты в DMS | 10 | 12.4s | **17.1s** | 30.5s | 30.5s | 10 COMPLETED** | 10/10** | 4-6 | 2 |
| D | Открытые задачи Калачанова с вложениями в WMB | 10 | 44.5s | **61.7s** | 165.3s | 165.3s | 10 COMPLETED | 10/10 | 5 | 3 |
| E | Покажи задачу DMS-380 | 10 | 10.0s | **12.0s** | 24.3s | 24.3s | 10 COMPLETED | 10/10 | 3 | 1 |

\* A-3: planner routed via `task.search_assignee` (all 346 Semavin tasks, no "риски" phrase) — LLM routing variant (A196-F2 lineage), documented, not a correctness defect; answer still source-accurate.
\*\* C-1 first attempt hit the LLM outage (5.4s typed `v4_runtime_failure`); re-run after recovery: COMPLETED 12.4s parity=true (superseded in all stats).

D note: all 10 runs = grounded REAL_EMPTY (COMPLETED, 0 open tasks, 5 terminal tasks fetched, attachments enumerated) — no false zero (P7 guard below).

## P2 — stage decomposition (from agent log segments, offline)

Method: per-run log window; events = LLM completion (`api.ai.sbt/openai/v1/chat/completions`), source GET (task-api 8241), response (`"Request completed"`). Inter-event gaps attributed to the following event type. Residual = wall − LLM − SRC − final-gap (includes request intake before first logged event, capability execution between log lines, response synthesis, client round-trip — not separable from current logs, reported as residual per spec).

| Sc | wall p50 | LLM p50 | SRC p50 | final p50 | residual p50 | LLM % | SRC % | residual % |
|---|---|---|---|---|---|---|---|---|
| A | 38.0s | 24.7s | 4.2s | 5ms | 9.4s | **64.9** | 11.1 | 24.6 |
| B | 39.3s | 25.6s | 3.4s | 3ms | 8.3s | **65.1** | 8.7 | 21.2 |
| C | 17.1s | 11.9s | 0.4s | 3ms | 4.0s | **69.9** | 2.5 | 23.5 |
| D | 61.7s | 29.8s | **31.7s** | 5ms | 4.3s | 48.3 | **51.4** | 7.0 |
| E | 12.0s | 9.8s | 0.2s | 5ms | 4.3s | **81.3** | 1.6 | 35.5 |

**Where the top 80% sits:** LLM planner round-trips (4-6 sequential calls, each 3-15s) are the dominant stage in 4 of 5 scenarios (48-81% of wall). In D, the WMB assignee+status task-query scan (P6a: 34.5s median) becomes the co-dominant source stage (51.4%). Final synthesis gap (last LLM → response) is negligible (≤7ms). Residual (request intake + unlogged capability work) is 7-36% — needs structured stage logging to decompose further (see R5).

## P3 — duplicate / redundant work audit

| # | Finding | Scenario | Class | Cost |
|---|---|---|---|---|
| 1 | `GET sprints/DMS-SPRNT-3/tasks?complete=true&limit=100&max_pages=500` fetched **2× per run** | B 10/10 runs | **avoidable technical duplication** (identical source-backed observation re-fetched within one request) | ~1.4s each (P6a median) |
| 2 | Same sprint full-collection fetched 1× | C 10/10 runs | required by correctness (current-sprint context) | ~1.4s |
| 3 | `assignees/resolve?reference=Kalachanov.V.V` 2× in one run | D-8, D-10 (2/10) | avoidable technical duplication | ~0.6s each |
| 4 | `assignees/resolve?reference=Semavin.M.M` 2× (member.resolve + task.search_assignee internal) | A-2 (1/10) | avoidable (resolver not memoized across capabilities) | ~0.6s |
| 5 | Repeated capability within one run | — | **none found** | — |
| 6 | UI duplicate query bodies (P5) | all routes | **none** (all burst bodies unique) | — |

No retry/recovery duplicates observed (0 failed HTTP in the 50-run matrix).

## P4 — cold vs warm / reconnect penalty (scenario B, 3 runs after each restart)

Boot readiness (not counted as request latency): agent 2.4s, task-api 1.1s, MCP 1.1s (task-api auto-reconnected).

| Phase | r1 (cold/reconnect) | r2 | r3 | parity |
|---|---|---|---|---|
| after agent restart | 32.26s | 32.24s | 23.25s | 3/3 exact |
| after task-api restart | 27.72s | 31.84s | 32.12s | 3/3 exact |
| after MCP restart | 30.59s | 47.05s | 27.78s | 3/3 exact |

**No measurable cold-start or reconnect penalty** — first factual request after any restart is within the warm distribution (warm B p50 39.3s, range 27-60s). No separate initialization/connection cost observed at the request layer.

## P5 — UI snapshot fan-out (Playwright, 1440×900, 6 routes)

| Route | auto POSTs on mount | concurrency | duplicate bodies | on revisit (full reload) |
|---|---|---|---|---|
| `/` | 4 | 4 (spread ≤1ms) | 0 | 4 (same set re-fired) |
| `/tasks` | 0 (explicit-submit only) | — | 0 | 0 |
| `/sprint` | 5 | 5 (spread ≤1ms) | 0 | 5 |
| `/releases` | 5 | 5 (spread ≤1ms) | 0 | 5 |
| `/team` | 5 | 5 (spread ≤1ms) | 0 | 5 |
| `/quality` | 4 | 4 (spread ≤1ms) | 0 | 4 |

- `/tasks` explicit submit: exactly 1 POST, 25.5s, HTTP 200.
- **All bursts are fully concurrent** (all t0 within 1ms) — each burst fires 4-5 complete query trajectories simultaneously.
- Contention: concurrent POSTs share the same LLM endpoint and the same source routes (e.g. sprint full-collection fetched by multiple snapshots; `/team`-class pages include the 34.5s WMB scan). A single page load therefore triggers **4-5× LLM amplification** (12-40 LLM calls) and up to 4-5 concurrent source scans.
- Revisit semantics: revisit was measured via full document reload (`page.goto`), which re-fires the persisted snapshot set — consistent with the A226R3 policy ("page refresh re-runs persisted, not defaults"). SPA-nav returns were verified 0-POST in A227R2 and not re-measured here.
- No obviously redundant calls returning overlapping source facts were found at the *body* level (all bodies distinct); the redundancy is at the *source-fetch* level (finding P3-1/2: the same sprint collection is fetched by multiple concurrent snapshots and duplicated within a single request).

## P6 — source-plane timing (direct, 5 iters each; no tenant-wide scans)

Task-API routes (P6a):

| Route | median | max |
|---|---|---|
| `current-sprint` (DMS) | 185ms | 1243ms |
| `spaces/DMS/sprints` | 441ms | 700ms |
| `sprints/DMS-SPRNT-3/tasks?complete=true` | **1382ms** | 1675ms |
| `assignees/resolve` (Semavin) | 616ms | 627ms |
| `task-query?phrase=риски&assignee=Semavin.M.M` | **4315ms** | 5613ms |
| `task-query?space=WMB&assignee=Kalachanov.V.V&status=not_completed` | **34464ms** | **46917ms** |
| `tasks/DMS-380` (point) | 282ms | 1417ms |
| `tasks/DMS-380/files` | 189ms | 426ms |

MCP-SWTR direct (P6b, JSON-RPC over SSE): `get_current_sprint` 113ms, `read_unit` 212ms, `find_units_by_filter` 247ms (medians).

**Task-API overhead over MCP:** ~50-200ms on cheap routes; on the WMB assignee+status query the 34.5s is source-bound (the route does a full WMB space scan and filters status client-side — `status=not_completed` is not applied at TQL level; confirmed by A229 oracle work: route returns all 5 tasks incl. terminal).

## P7 — correctness guard (across all 50 warm runs + P4 + P5)

| Guard | Result |
|---|---|
| Exact source parity | 49/50 (sole exception: A-3 documented planner routing variant, answer still source-accurate) |
| False zero | **0** — D REAL_EMPTY grounded: 10/10 COMPLETED with search executed + source calls (5 terminal tasks enumerated) |
| Local factual fallback (non-`/swtr-read` reads) | **0** (95 source GETs, all `/api/v1/swtr-read/`) |
| Unauthorized mutations | **0** (all source calls GET) |
| Tenant-wide scans | **0** (all task-query calls carry `space=` or `assignee=`; the assignee-only phrase scan is bounded to one person's 346 tasks) |
| Hidden truncation | **0** (every sprint full-collection call uses `complete=true`; DMS-SPRNT-3 count 79 stable across P4) |

All performance measurements remain correctness-valid.

---

## P8 — Ranked bottleneck list (by measured time contribution)

### 1. LLM planner round-trips — Qwen3.8-27B @ `api.ai.sbt` *(environment/provider + agent turn count)*
- **Scenarios:** all (A-E)
- **Impact:** 48-81% of wall per scenario; 3-6 **sequential** calls per query; single-call duration 3-15s (p50 ~4-5s). A: 24.7s p50; B: 25.6s; C: 11.9s; D: 29.8s; E: 9.8s.
- **Evidence:** P2 stage decomposition (LLM inter-event gaps from agent log); P1 LLM-call counts.
- **Sub-item 1b — endpoint instability:** 2 outage windows in one session → 24 typed fail-closed runs (`v4_runtime_failure`, 0 source calls, 2-14s). Fail-closed behavior correct; user-visible cost = full query failure.
- **Attribution:** environment/provider (call duration) + agent (call count is locally controllable).
- **Safest optimization candidate:** reduce sequential planner turns (single-call plan for simple intents; consolidate `space.resolve`+terminal call when space is already in-query) and/or constrained-output decoding (A179/A227-F3 owner item — same reliability frontier).
- **Risk to correctness:** medium — planner changes touch the reliability frontier already documented in A179/A217C/A227; must re-gate the full A205R suite.
- **Owner code change warranted:** yes (call-count reduction is agent-side; provider duration is not).

### 2. WMB assignee+status task-query full-space scan *(Task API / source-bound)*
- **Scenarios:** D (and any `space + assignee + status=not_completed` query)
- **Impact:** **34.5s median / 46.9s max** (P6a); 51.4% of D wall (31.7s p50 stage); D wall p50 61.7s, p90 165.3s.
- **Evidence:** P6a direct route timing (5 iters, 200s, count=5); P2 D stage split; oracle: route `status=not_completed` not server-filtered (returns all 5 incl. terminal).
- **Attribution:** Task API (missing server-side status filter) → source scan cost.
- **Safest optimization candidate:** apply statusType filter at TQL level in the task-query route (or cache the assignee's task set with short TTL).
- **Risk to correctness:** low-medium — must preserve fail-closed on partial pages and the client-side terminal classification contract (A229 oracle D relies on it).
- **Owner code change warranted:** yes.

### 3. UI snapshot fan-out: 4-5 concurrent full query trajectories per page load *(frontend concurrency)*
- **Scenarios:** all UI routes except `/tasks`
- **Impact:** 4-5 simultaneous POSTs (spread ≤1ms) per mount and per reload → 12-40 concurrent LLM calls + 4-5 concurrent source scans per page load (incl. the 34.5s WMB scan on `/team`-class pages); bursts share the same LLM endpoint and the same sprint full-collection.
- **Evidence:** P5 (6/6 routes; 0 duplicate bodies; all bursts fully concurrent).
- **Attribution:** frontend (design) × backend amplification.
- **Safest optimization candidate:** bound snapshot concurrency (e.g. max 2 in flight) and/or deduplicate identical source fetches across concurrent snapshots (the sprint collection is fetched 4-5× per page load).
- **Risk to correctness:** low (presentation layer; snapshot TTL policy already exists per A226R3).
- **Owner code change warranted:** yes (bounded, frontend-local).

### 4. Duplicate sprint full-collection fetch within a single request *(plugin/runtime)*
- **Scenarios:** B 10/10 runs (2× per run), C 10/10 (1×, required)
- **Impact:** ~1.4s per duplicate (P6a median); ~3.5% of B wall; also multiplies ×4-5 under P5 bursts.
- **Evidence:** P3 finding #1 (identical `complete=true&max_pages=500` URL twice in the same run log window, 10/10).
- **Attribution:** agent runtime (no in-request memoization of source-backed observations).
- **Safest optimization candidate:** in-request observation cache keyed by (capability, args) — the second call should reuse the existing observation.
- **Risk to correctness:** very low (read-only, same-request, byte-identical request).
- **Owner code change warranted:** yes (cheap, safe win).

### 5. Agent-side residual (intake + unlogged capability work + synthesis) *(plugin/runtime, partially UNKNOWN)*
- **Scenarios:** all; E 35.5%, A 24.6%, C 23.5%, B 21.2%, D 7.0% of wall (p50 4.0-9.4s)
- **Evidence:** P2 residual column; current logs cannot separate request intake, inter-capability processing, and synthesis.
- **Attribution:** agent runtime (measurement gap).
- **Safest optimization candidate:** **instrument first** — structured stage logging (intake→plan→each capability→synthesis) before any optimization attempt.
- **Risk to correctness:** none (observability only).
- **Owner code change warranted:** yes (logging only, no behavior change).

### 6. Duplicate person-resolve within a request *(agent runtime, minor)*
- **Scenarios:** D-8/D-10 (2× `assignees/resolve`), A-2 (member.resolve + internal resolve)
- **Impact:** ~0.6s per affected run (2-3/50 runs)
- **Evidence:** P3 findings #3-4.
- **Safest optimization candidate:** memoize resolved identities per request (same mechanism as #4).
- **Risk to correctness:** very low. **Warranted:** yes, fold into #4.

### 7. Phrase task-query scan (A) *(source-bound)*
- **Impact:** 4.3s median / 5.6s max (11.1% of A wall)
- **Attribution:** source (bounded assignee-scope phrase search).
- **Warranted:** **no** — bounded and 4.3s; watch item only.

### Do NOT optimize (source/provider-bound; local change risks architecture quality)
- **MCP direct call latency** (113-247ms) — already thin; Task-API overhead above it is 50-200ms, acceptable.
- **LLM single-call duration (3-15s)** — provider-bound; only call *count* is locally controllable (rank 1).
- **Sprint full-collection fetch (1.4s for 79 tasks)** — healthy per-fetch cost; only the *duplication* (rank 4) is the defect.
- **Point reads / files (189-282ms)** — no action.
- **Boot readiness (1.1-2.4s)** — no request-level penalty observed (P4); no prewarming needed.

## Recommended owner remediation list for A229R (prioritized, with before → target)

| # | Fix | Before (measured) | Target | Risk |
|---|---|---|---|---|
| R1 | In-request observation memoization (sprint collection + person resolve) | B wall p50 39.3s; 10/10 duplicate fetches; 2-3/50 double-resolve | B p50 ≤ 37.9s (−1.4s); 0 duplicates | very low |
| R2 | Server-side statusType filter for `task-query?status=not_completed` (or TTL cache of assignee sets) | D wall p50 61.7s / p90 165.3s; route scan 34.5s median | D p50 ≤ 35s, p90 ≤ 60s; route scan ≤ 5s | low-medium (keep fail-closed + client terminal classification) |
| R3 | Bound UI snapshot fan-out concurrency (max 2 in flight) + dedupe identical source fetches across concurrent snapshots | 4-5 concurrent POSTs/page load; 12-40 concurrent LLM calls; sprint collection fetched 4-5×/load | ≤ 2 concurrent trajectories; 1 sprint-collection fetch per load | low |
| R4 | Reduce sequential planner turns for simple intents (single-call plan; consolidate space.resolve) | E 3 turns/12.0s; C 4-6 turns/17.1s p50 | E ≤ 2 turns / ≤ 8s p50; C p50 ≤ 12s | medium (re-gate A205R + A227 matrix) |
| R5 | Structured stage logging (intake/plan/capability/synthesis) | residual UNKNOWN 4.0-9.4s p50 (7-36% of wall) | residual decomposed; ≤ 15% unaccounted in re-gate | none (observability) |
| R6 | (tracked, not this wave) LLM endpoint reliability / constrained output — A179/A227-F3 owner item | 2 outage windows → 24 fail-closed runs in one session | 0 fail-closed from endpoint blips < 30s | medium |

## Non-blocking findings
1. Checkpoint tag `checkpoint/v4-release-recovery-green-a228` still absent (A228 carry-over).
2. `task-query?status=` parameter is accepted but not applied server-side (oracle D) — users/agents must classify terminal client-side; document or fix in R2.
3. P5 revisit was measured as full reload (re-fire of persisted set = A226R3-compliant); SPA-nav revisit re-verification recommended in A229R alongside R3.
4. D wall p90 165.3s — single run with an LLM slow-window (86s LLM stage); source stage itself stable (34.5s median, 46.9s max).

## Services left running
agent 8004 (PID 96087 @1591eae), task-api 8241 (PID 96598), MCP-SWTR 3000 (PID 97012), vite 5175 [::1] (PID 39280).

## Evidence files
`/private/tmp/qa229/`: p0_steady.json, p1.log, p1_gap.log, p1_all_runs.json, p1_gap_runs.json, p1_run_*.json (per-run log segments), p1_oracles_gap.json, p2_stages.json, p3_duplicates.json, p4_reconnect.json, p4.log, p5_fanout.json, p5.log, p6_source_timing.json, p6_mcp_direct.json, p7_guard.json.

**Recommendation:** freeze A229 as the latency checkpoint; execute R1+R2+R3 first (low-risk, ~60% of removable latency), then R4 with full A205R/A227 re-gate; R5 logging should ship with any of them.
