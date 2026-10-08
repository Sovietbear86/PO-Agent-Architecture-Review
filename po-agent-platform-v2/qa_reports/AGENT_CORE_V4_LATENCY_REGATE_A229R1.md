# A229R1 — Low-risk latency verification (R1 sprint single-read, R2 assignee+space pushdown, R3 bounded UI fan-out, R5 stage timing)

**Verdict:** `AGENT_CORE_V4_LATENCY_GREEN_A229R1`
**Date:** 2026-10-08
**QA role:** performance/tester only, zero code changes
**Branch:** `feat/core8-real-query-hardening-v2`
**START_HEAD:** `7ad8f3a` (docs-only over certified `afb6fa1`; owner `747d06f` froze the A229S1R4 checkpoint + advanced to latency re-gate)
**Certified baseline:** `checkpoint/v4-task-semantics-hierarchy-green-a229s1r4` (tag exists @ `afb6fa1`)
**A229 latency baseline:** `AGENT_CORE_V4_LATENCY_BASELINE_GREEN_A229` (report `AGENT_CORE_V4_LATENCY_BASELINE_A229.md`)

**Environment note (material to interpretation):** the LLM endpoint (`api.ai.sbt`, Qwen3.8-27B) was rate-limited and slow throughout the session (recurring `429 Too Many Requests`; ~19s/call observed vs ~7.5s/call implied by A229). All 429-affected samples fail closed, are documented separately, and were re-run after recovery; they are **not** counted as optimization measurements. Source-side (task-api/MCP) was fast and healthy (direct probes 1–2s).

---

## P0 — integrity / correctness guard

| Item | Result |
|---|---|
| Worktree | clean (untracked QA artifacts only) |
| Delta `afb6fa1..7ad8f3a` | docs-only: `GIGACODE_NEXT_ACTION.md`, `PO_AGENT_HARNESS_EVOLUTION_PLAN.md`, A229S1R4R report. **0 production code** |
| Core 6/6 byte-identical vs `afb6fa1` | **PASS** (sha256: agent_core_v4, agent_core_v4_robust, agent_core_v4_reliable, agent_core_v4_completion, v4_plugin_registry, llm/real.py) |
| Focused latency-remediation regressions | `test_agent_core_v4_plugin_sprint_single_read.py` 1 passed (R1); `test_swtr_task_query_partial.py` 2 passed (R2 scoped-strict/partial-isolation) |
| Full V4 blast-radius | `test_agent_core_v4*.py + test_v4*.py` = **248 passed, 0 failed** |
| Task API SWTR suites | 8 suites = **54 passed, 0 failed** |
| Retained A229S1R4R correctness (REAL AS21) | H: Semavin open bugs OLP-SPRNT-9 = **4/4 exact** [OLP-2974, 3241, 3357, 3392]; hierarchy DMS-267 = **exact** (CRPV-90180→DMS-253→DMS-267, depth 2); Overview KPI = **82/29/5/26.1% exact** vs `po.status_report` |

No correctness regression. **P0 GREEN.**

---

## P1 — R1 sprint single-read verification

Scenario: `Задачи в работе в сентябрьском спринте по DMS` (A229 scenario B).

**Fresh independent oracle:** DMS September sprint = `DMS-SPRNT-3` ("Спринт 2026.09 - 1", status FINISH). Complete corpus = 51 rows, **all 51 terminal** (Resolved 35, Closed 9, Подтверждение исправления 3, Закрыт 3, Выполнен 1) → canonical IN_PROGRESS = **0**. The correct answer is a legitimate `count=0` REAL_EMPTY **on the right sprint** (the planner must not pivot to the October sprint DMS-SPRNT-4, which has 13 in-progress).

**10 valid warm sequential samples** (run 9 of the first batch hit a 429 window → typed fail-closed, documented, re-run after cooldown — not counted):

| Metric | Value |
|---|---|
| Valid runs | 10/10 COMPLETED, `runtime_contract` |
| Exact source parity | 10/10 (`count=0`, no keys, terminal `task.search sprint_id=DMS-SPRNT-3 status=in_progress`) |
| **Complete sprint-corpus source read per request** | **exactly 1 in 10/10** (task-api log: one `GET /swtr-read/sprints/DMS-SPRNT-3/tasks` per request) |
| Duplicate `get_sprint_tasks`/full sprint collection read | **0** (A229 cost ~1.4s/request — removed) |
| Local fallback / tenant-wide scan | 0 / 0 |
| wall | min 53.7s, **p50 109.4s**, p90 142.6s, max 222.8s |
| LLM/planner calls | 5–7 per request |

**Before → after (R1):**
- p50 wall: 39.3s (A229) → 109.4s. **Not a regression of the remediation** — the wall is now ~96% LLM/planner (P4 stage decomposition); the duplicate sprint read (~1.4s) is provably gone (1 read/request × 10/10).
- source calls/request: A229 B = 3 (incl. duplicate sprint read) → **1 sprint-corpus read** + bounded sprint discovery.
- planner calls/request: 5–6 (A229) → 5–7 (same class).

**P1 GREEN** (R1 verified: duplicate sprint reads removed; exact parity retained).

---

## P2 — R2 assignee + space source pushdown

Same live person+space class as A229 D (WMB/Kalachanov).

**Source predicate proof (in-process capture of the exact TQL sent to MCP for a space-scoped request):**
```
find_units_by_filter.query = assigned_to = "Kalachanov.V.V" AND space = "WMB"
```
Both `assigned_to` **and** `space` are pushed to REAL AS21 (`swtr_assignee.py:_assignee_tql`); client-side space validation retained as postcondition (`row_space != normalized_space → skip`).

**Direct bounded source route** (`GET /swtr-read/assignee-tasks?assignee=Kalachanov.V.V&space=WMB`), 10x:
- **p50 1.0s, max 2.0s** (A229: p50 ~34.5s, max ~46.9s) → **~35× faster**. Target ≤10s / preferred ≤5s: **met**.
- All rows `space=WMB` (client validation holds).

**Cross-space narrowness control:** unscoped `assignee-tasks?assignee=Kalachanov.V.V` = 29.2s / 2991 rows across CRPV+STS+WMB, WMB share **0.2%** — vs 0.9s / 6 rows scoped. Pushdown materially narrows the source query.

**End-to-end Agent** (`Открытые задачи Калачанова с вложениями в WMB`), 10 valid:
- 10/10 COMPLETED via `task.search_attachments(space=WMB, status=not_completed)`, grounded answer `count=0, results=[]` — correct: the only open WMB Kalachanov task (WMB-30482, In progress) has **0 attachments** (verified via `/files`). No false zero (drift vs A229's all-terminal corpus documented).
- wall: min 31.5s, **p50 86.8s**, p90 127.4s, max 136.7s (A229: p50 61.7s, p90 165.3s).

**Before → after (R2):** direct route p50 34.5s → **1.0s**. End-to-end p50 61.7s → 86.8s — the e2e target (≤45s) is **not** met, but the residual is **LLM/planner-bound, not source-bound** (source is now ~1s; P4 shows LLM ≈ 96% of wall). Per spec, remaining time is classified as provider-bound; no factual caching recommended.

**P2 GREEN** (R2 verified: predicate pushed down, direct route ~35× faster, e2e correct/source-backed).

---

## P3 — R3 UI bounded snapshot fan-out

Fresh context per page; `/api/v1/query` POST start/end traced in-browser:

| Page | snapshots fired | completed | **max simultaneous in-flight** | skipped |
|---|---|---|---|---|
| Overview | 3 | 3 | **2** | 0 |
| Sprint | 6 | 6 | **2** | 0 |
| Releases | 6 | 6 | **2** | 0 |
| Team | 6 | 6 | **2** | 0 |
| Quality | 4 (default criteria WMB-102/WMB/7d, by design) + 3 on submit DMS-380 | 7 | **2** | 0 |
| Tasks | explicit submit = **1 POST**; navigation away+back = **0** additional | — | — | — |

Mechanism: `pageSnapshot.tsx` `withSnapshotSlot` semaphore, `SNAPSHOT_MAX_CONCURRENCY = 2` (waiter queue). A229 baseline was 4–5 simultaneous full Agent trajectories per page; now capped at 2 on **every** page with zero lost snapshots.

**P3 GREEN** (R3 verified: max 2 concurrent Agent POSTs, all snapshots complete or typed-fail, none silently skipped; Tasks submit stays one request; no unintended auto-POSTs on return).

---

## P4 — R5 stage timing observability

**Emission (proven):** in-process probe driving the production `_instrument_handler` wrapper (the exact wrapper `bind_handlers` applies to every governed capability) confirms structured timing is emitted as log-record extras:
```
{capability_id: "probe.ok",  duration_ms: 0, outcome: "ok"}
{capability_id: "probe.err", duration_ms: 0, outcome: "error"}
```
So `capability_id` / `duration_ms` / `outcome` are emitted for both success and error outcomes.

**Rendering gap (finding D-A229R1-1, non-blocking):** the production log formatter (`main.py:18` `logging.basicConfig(format='{"timestamp": ..., "level": ..., "message": ...}')`) renders only timestamp/level/message and **drops the `extra=` fields** — 0 rendered lines in the live agent log contain `duration_ms`. The instrumentation is implemented and emitting, but per-capability durations are not observable in production logs as shipped. Fix boundary (owner, one-line class): a JSON formatter that includes record extras.

**Stage decomposition (reconstructed from timestamped httpx request lines + capability/`Request completed` markers, 47 representative completed windows):**

| Stage | share of wall (p50) |
|---|---|
| LLM/planner | **96.3%** (p90 100%) |
| Task API/MCP/source | 2.0% (p90 73.4% — the p90 outliers are the few multi-source capabilities) |
| Unexplained residual | **p50 0.0%**; 6/47 windows >15% (all 429-retry backoff windows, documented) |
| LLM calls/request | **5** (p50), range 3–8 |

The representative **median** runs meet the ≤15% residual target; the residual is explained and the dominant stage is unambiguously the LLM/planner.

**P4: R5 emission verified; rendering gap flagged (D-A229R1-1).**

---

## P5 — before/after latency matrix (5 valid warm samples each; B & D from P1/P2 at n=10)

| Sc | Scenario | A229 p50 | A229R1 p50 | A229R1 p90 | n | source parity | planner calls |
|---|---|---|---|---|---|---|---|
| A | person+text (Semavin риски) | 38.0s | 73.4s | 218.5s | 5 | 4/5 exact REAL_EMPTY + 1/5 routing variant (`task.search_assignee`, A229 A-3 class) | 3–4 |
| B | sprint+status (DMS септ в работе) | 39.3s | 109.4s | 142.6s | 10 | 10/10 exact REAL_EMPTY, sprint_reads=1 | 5–7 |
| C | sprint list (DMS) | 17.1s | 10.5s | 47.5s | 5 | 5/5 exact (4 sprints, incl new DMS-SPRNT-4) | 4 |
| D | open+attachments+person+space (WMB Kalachanov) | 61.7s | 86.8s | 127.4s | 10 | 10/10 correct grounded (0 open WMB w/ attachments) | 5–6 |
| E | exact task lookup (DMS-380) | 12.0s | 17.1s | 21.2s | 5 | 5/5 exact DMS-380 | 3 |
| F | created-period+open (Kalachanov STS 5d) | — | 61.4s | 96.3s | 5 | 5/5 `count=11` = oracle open-in-window (drift 0) | 4–6 |
| G | created-period+in-progress (Kalachanov STS 5d) | — | 32.5s | 36.3s | 5 | 5/5 REAL_EMPTY 0 = oracle inprog-in-window [] | 3 |
| H | person+latest sprint+status+type (Semavin OLP bug) | — | 38.7s | 38.9s | 5 | 5/5 exact 4 OLP keys | 6 |

Interpretation: source-side latency improved where the remediation targets it (R1 dedup; R2 direct route 34.5s→1.0s). End-to-end walls for the multi-call scenarios (A/B/D) are **higher** than A229 because the session's LLM provider was rate-limited/slow (~19s/call vs ~7.5s) — an environmental condition, not a code regression (every run is source-exact and fail-closed). C/E and the new F/G/H are fast (10–60s) because they use fewer planner turns.

**P5 GREEN** (every factual completed run is source-backed; 0 false zero; provider failures documented separately).

---

## P6 — source/correctness audit

| Guard | Result |
|---|---|
| Exact source parity for every factual completed run | **PASS** (P1 10/10, P2 10/10, P5 30/30 valid) |
| 0 false zero | **PASS** (REAL_EMPTY answers all grounded: DMS-SPRNT-3 all-terminal; WMB-30482 open-but-0-files; G inprog-window empty; A phrase no-match) |
| 0 local factual fallback | **PASS** (0 `GET /api/v1/tasks` in task-api + agent logs) |
| 0 unauthorized mutations | **PASS** (0 swtr-write POST/PUT/DELETE/PATCH) |
| 0 tenant-wide scans | **PASS** (112/112 `task-query`/`assignee-tasks` rows carry `space=` or `assignee=`; the only "unbounded" GETs are 44 `assignees/resolve` identity lookups by explicit reference) |
| 0 hidden truncation | **PASS** (complete corpora: `complete=true`, `membership_proven=true`; F/G full 2789-row STS corpus, 0 missing `created_at`) |
| 0 cross-request factual cache | **PASS** (each of the 10 P1 runs re-issued its sprint read; no server-side short-circuit) |
| 0 Agent Core changes | **PASS** (Core 6/6 byte-identical; delta docs-only) |

5 server 5xx observed in the session — all from **QA oracle probes** (`assignee-tasks?space=STS&max_pages=1/6`) during a transient STS source window; every agent query succeeded (retries after cooldown). 0 client 4xx.

**P6 GREEN.**

---

## P7 — decision gate

1. **Did R1 remove duplicate sprint reads?** **YES** — 10/10 P1 runs issued exactly one complete sprint-corpus read; 0 duplicates.
2. **Did R2 narrow the source query and materially improve direct-route latency?** **YES** — TQL carries `assigned_to AND space`; direct route p50 34.5s → **1.0s** (~35×); cross-space control proves the narrowing (2991 rows/0.2% WMB → 6 rows).
3. **Did R3 reduce simultaneous Agent trajectories to ≤2 without losing snapshots?** **YES** — max in-flight = 2 on every page (was 4–5); all snapshots completed, none skipped; Tasks submit stays 1 request.
4. **Does R5 explain enough wall time to identify the remaining bottleneck?** **YES (with caveat)** — stage decomposition attributes **96.3% (p50) of wall to LLM/planner** and ~2% to source, median residual ~0%. Caveat: the R5 per-capability fields are emitted but **not rendered** by the production log formatter (D-A229R1-1); stages were reconstructed from httpx + capability timestamps.
5. **Is ordinary interactive latency acceptable enough to avoid planner changes?** **NO.** Median end-to-end wall for multi-call scenarios is 10–100s+, dominated by **5 sequential LLM/planner calls** (plus the session's provider slowdown). Not acceptable for interactive use without planner-turn reduction.

**Quantification (latency remains unacceptable):**
- current planner calls/request: **5** (p50), 3–8 range;
- planner/LLM share of wall: **~96%** (p50);
- expected removable time from exactly **one fewer** planner call: ≈ 1/5 of the LLM share ≈ **~19% of wall** (~20s on a 100s query), before any provider-speedup;
- certified trajectories requiring re-gating after any planner change: the multi-hop person→search (A, D), sprint+status (B), created-period (F, G), and person+sprint+status+type (H) — i.e., every 5–7-turn trajectory.

**Recommendation:** `CONSIDER_A229R2_PLANNER_TURN_REDUCTION`

---

## Findings

- **D-A229R1-1 (non-blocking, owner fix):** R5 structured timing (`capability_id`/`duration_ms`/`outcome`) is emitted by `_instrument_handler` (proven) but the production formatter (`po_agent/main.py:18`, fixed `basicConfig` format) drops `extra=` fields → not observable in rendered logs. Fix: formatter that serializes record extras (or structlog JSON renderer). No behavior change; observability only.
- **Environmental:** LLM endpoint 429 rate-limiting + ~2.5× per-call slowdown across the session (documented per-run; affected samples fail closed and were re-run). STS source 502 window (transient, QA probes only). Neither is a code defect.
- **Non-blocking routing variant:** A-4 routed via `task.search_assignee` (378 tasks, no phrase) — pre-existing A229 A-3 / A196-F2 planner-routing class; answer still source-accurate.

## Services

agent 8004 (PID 69794 @ `7ad8f3a`, `EXPECTED_HEAD=7ad8f3a`, process-env `TASK_API_BASE_URL=http://127.0.0.1:8241` override — `.env` file guard), task-api 8241 (PID 69692, system py3), MCP-SWTR 3000 (SSE, 48 tools), vite [::1]:5175 (PID 56871).

## QA artifacts

`/private/tmp/qa229r1/` (oracles, p1/p2/p3/p5 run JSON, p4 windows, p6 audit, before_after matrix); QA scripts at repo root: `qa_229r1_p1_runner.py`, `qa_229r1_p1_rerun.py`, `qa_229r1_p2_predicate.py`, `qa_229r1_p2_direct.py`, `qa_229r1_p2_e2e.py`, `qa_229r1_p3_browser.mjs`, `qa_229r1_p3b.mjs`, `qa_229r1_p4_analyzer.py`, `qa_229r1_p5_matrix.py`, `qa_229r1_p6_audit.py`, `qa_229r1_r5_probe.py`, `qa_229r1_mcp_oracle.mjs`, `qa_229r1_sprints.mjs` (all untracked).

**No production code was modified.**
