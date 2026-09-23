# AGENT CORE V4 — Pre-S2 Manual Query Consistency (A208) — QA Report

**Assignment:** 208 — Pre-S2 manual query consistency re-gate
**Role:** QA / adversarial + service-operator only (no production edits, no Wave S2, no new skills)
**START_HEAD:** `6519b87885314076942dfb2eb09f35c67a5fecd8` (branch `feat/core8-real-query-hardening-v2`)
**Stable rollback checkpoint:** `checkpoint/v4-wave-s1-green@ce64264` (A207 GREEN)
**Date:** 2026-09-23

---

## VERDICT

### **BLOCKED_BY_PROVEN_SOURCE_OUTAGE**

The Qwen3.8-27B planner LLM endpoint (`https://api.ai.sbt/openai/v1`) is in a **proven, persistent degradation window**: every planner call now takes **63–144 s**, far exceeding the agent's fixed **60 s** per-call LLM timeout. Every V4 query that requires the planner therefore exhausts its bounded repair budget and fails closed (`planner failed robust bounded repair: [ReadTimeout ×4]` → `v4_runtime_failure`). This blocks the entire live manual/consistency gate (Phases 3–8), which is the purpose of A208.

**This is NOT a code defect and NOT a RED.** The owner's consistency fixes are verified correct at the architecture (P0) and contract/unit (P1) level, and the agent fails **closed** with zero fabrication throughout. The blocker is environmental (LLM endpoint), the same lineage as A179 / A186 (`P1_LLM_ENDPOINT_BLOCK`) / A199-F3 / A200-F1.

**Recommendation:** when the LLM endpoint recovers (sub-60 s planner calls), **re-run A208 live phases 3–8** before `PROCEED_TO_WAVE_S2_OWNER_IMPLEMENTATION`. Do **not** start Wave S2 on the basis of this report.

---

## Phase 0 — Pull / architecture diff (`ce64264..6519b87`) — **PASS**

Owner commits under test: `16bbae5` (source-status + blocked predicate in task search), `fc8d269` (declare semantics), `3aa47ce` (Wave S1 generic sprint resolution), `76c57d1` + `d11dbe0` (focused tests), `fa7c821`/`802e869`/`6519b87` (docs/spec).

| Invariant | Result |
|-----------|--------|
| No per-person/space/sprint/status-name hardcode | ✅ `blocked` maps to the canonical `task.is_blocked` predicate; source-status match is a generic field check |
| No new Agent Core routing branch by phrase/entity | ✅ only a generic `status == "blocked"` semantic branch + a generic `status_raw`/`status_type` substring check in the free-text status path |
| task.search change is generic predicate/source-field support only | ✅ `agent_core_v4.py`: `blocked`→`is_blocked`; free-text status now checks `status_raw` and `status_type` before the normalized enum/category |
| Wave S1 resolution changes are declarative plugin procedure/capability exposure | ✅ `wave_s1.py`: all 4 metric skills expose `space.resolve` + (`sprint.resolve` \| `sprint.search` \| `sprint.current`) — procedure text + capability allow-list only, **no formula change** |
| No local/fake/cache fallback | ✅ no such path introduced |

No architecture violation.

## Phase 1 — Automated tests — **PASS (140)**

| Suite | Result |
|-------|--------|
| `test_agent_core_v4_task_search_source_status.py` (new, 2) + `wave_s1` + `plugin_registry` (22 total) | 22 passed |
| `test_agent_core_v4*.py` + `test_v4*.py` (full V4) | **140 passed**, 0 failures |

The new focused test **proves the fix at contract level** (LLM-free, deterministic):
- `test_task_search_blocked_uses_canonical_blocked_predicate`: `status=blocked` → `task.is_blocked` → returns exactly the NEED_INFO task.
- `test_task_search_matches_authoritative_source_status_label`: `status="На исправлении"` (normalizes to `TaskStatus.UNKNOWN`) → matches on `status_raw` → returns exactly that task. This is the direct close of the A207 **F2** gap.

## Phase 2 — Fresh REAL AS21 oracle (DMS current sprint) — **BUILT**

Built at run time (not reused from A207; source drifted 65→66):

- **Sprint:** DMS-SPRNT-3, **n = 66**
- **Status-name distribution:** In progress 12, Open 19, Resolved 10, Закрыт 3, Closed 3, **На исправлении 1**, Тестирование 2, In review 6, Ready for QA 2, QA 4, Ready for review 1, **Need info 2**, Зарегистрирован 1
- **Canonical `is_blocked` (NEED_INFO):** **2** → `DMS-352`, `DMS-379`
- **UNKNOWN-canonical tasks:** 0 in the current DMS sprint (a custom-name probe is covered by `Закрыт`×3 and `На исправлении`×1, both of which the old enum-only matcher would have returned empty for)

## Phase 3–8 — Live manual consistency E2E — **BLOCKED (LLM endpoint)**

Every planner-dependent query fails closed. Evidence captured on `6519b87`:

**Agent-level (through the real V4 runtime):**
| Query | Result |
|-------|--------|
| "Заблокированные задачи спринта DMS-SPRNT-3" ×2 | FAILED `planner failed robust bounded repair: [ReadTimeout×4]`, `v4_runtime_failure`, 240 s, 0 skills, 0 evidence |
| "Заблокированные задачи спринта DMS-SPRNT-3" (110 s client) | CLIENT_TIMEOUT 110 s |
| "задачи в статусе На исправлении в DMS-SPRNT-3" (110 s) | CLIENT_TIMEOUT 110 s |
| "wip спринта по DMS" (110 s) | CLIENT_TIMEOUT 110 s |

**Direct LLM endpoint probes (independent of agent code, CA-disabled urllib):**
| Probe | Latency |
|-------|---------|
| trivial "OK" (max_tokens=10) ×3 | 63.5 / 74.3 / 77.1 s (model stuck in `reasoning`, `content=null`) |
| trivial "OK" (max_tokens=10) | 84.5 s, `finish_reason=length`, 10/10 tokens = reasoning |
| realistic planner prompt (max_tokens=400) ×2 | **127.8 / 144.5 s** |

The agent's LLM client timeout is **60 s** (`po_agent/llm/openai.py`), so **every** planner turn ReadTimes out under current endpoint latency. No live P3 (blocked↔health parity), P4 (raw-status parity), P5 (short/period metric matrix), P6 (health/WIP sanity), P7 (retained), or P8 (Browser C) run can complete. Zero fabrication in every blocked run.

### What IS proven without the LLM (code + contract level)

- **Blocked ↔ health parity is structurally guaranteed:** `sprint.health` counts blocked via `task.is_blocked` (`harness/team_intelligence.py:75-76`, also the team `blocked` capability at :121-124) and the new `task.search status=blocked` uses the **identical** `task.is_blocked` predicate (`harness/agent_core_v4.py:965`). Same predicate over the same fresh `get_sprint_tasks` set ⇒ equal counts by construction. (Live key-parity confirmation deferred to the re-run.)
- **Raw source-status matching:** proven by the focused unit test (`На исправлении`→`status_raw` hit, enum-UNKNOWN task no longer dropped to empty).
- **Wave S1 generic resolution:** declarative procedure/capability exposure present for all 4 metric skills (id→`sprint.resolve`, period→`sprint.search`, product-only/current→`sprint.current`); metric formulas unchanged from A207 GREEN.

## Phase 9 — Architecture / source audit — **PASS (as far as observable)**

- Local factual `GET /api/v1/tasks` reads: **0** (agent log).
- No tenant-wide scan introduced; release.search still routes to bounded `/api/v1/swtr-read/versions` only.
- `/versions` still **HTTP 502** → `release.search` remains **SOURCE_CONDITIONAL** (unchanged from A207).
- No hardcoded people/spaces/sprint ids/status names in the diff.
- Fail-closed preserved: every blocked/failed run is a typed `v4_runtime_failure`, no fabricated facts.

## Service health (left running)

| Service | Port | State |
|---------|------|-------|
| PO Agent (HEAD `6519b87`) | 8212 | `/live` 200 (PID 64407) |
| Task API (system python3) | 8241 | `/health` 200 |
| UI (IPv6 `[::1]`) | 5175 | 200 |
| MCP-SWTR | 3000 | connected (task-api source reads healthy) |
| `/versions` (release dir) | — | HTTP 502 (independent, pre-existing) |
| **LLM endpoint (Qwen3.8-27B)** | — | **DEGRADED: 63–144 s/call > 60 s agent timeout** |

---

## Owner action (to unblock)

1. Restore planner-LLM latency below the 60 s per-call budget (or raise the LLM client timeout / add bounded retry with backoff). Once sub-60 s planner calls are sustained, re-run A208 live Phases 3–8.
2. On re-run, the live must-proofs are: P3 blocked key-parity vs `task.is_blocked` oracle (DMS-352/DMS-379) **and** exact equality with `sprint.health.blocked`; P4 raw-label exact key parity (`На исправлении`, `In review`, `Закрыт`, `Need info`) + `not_completed`/`completed` retained; P5 short-form (5×) + period (2×) exact parity with explicit-id; P8 Browser C no V4 ERROR for healthy-source cases.

**STOP.** No code fixed, no Wave S2 started, no new skills. Only this QA report committed.
