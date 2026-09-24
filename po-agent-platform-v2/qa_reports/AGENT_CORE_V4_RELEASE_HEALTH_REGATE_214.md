# A214 — Agent Core V4: release.health trusted-observation re-gate

- **Date:** 2026-09-24
- **Branch:** `feat/core8-real-query-hardening-v2`
- **START_HEAD:** `b5ac56797b62e0a84f3ae921a208ab9744220296`
- **A213 baseline (report):** `0251fa8` — verdict `RELEASE_HEALTH_RED`, sole blocker D-A213-1 (generic literal-grounding guard rejected the authoritative `release_id` UUID returned by a validated `release.search` observation; no trusted-observation exemption).
- **Owner fix under review:**
  - `31f122a` fix(v4): trust release ids from validated search observations
  - `18e8d4c` test(v4): cover trusted release id literal grounding
  - `356c5a2` test(v4): align release health contract with bounded search flow
- **Source:** REAL AS21 via task-api 8241 → MCP-SWTR 3000 (SSE, 48 tools). Agent 8212 restarted at START_HEAD (PID 43636, `/live` 200). LLM Qwen3.8-27B healthy (6–24 s/call, no 500s this session).

## Verdict

**`RELEASE_HEALTH_SAFE_SOURCE_CONDITIONAL_GREEN`**

D-A213-1 is CLOSED: the planner can now pass the release UUID emitted by a validated `release.search` observation into `release.health`, the bounded space-scoped handler executes, and the current source limitation (empty authoritative release→task membership) surfaces as a **typed fail-closed** result — no generic runtime failure, no 0/0 fabricated health, no tenant-wide scan, no local factual reads.

---

## Phase 0 — architecture invariant

Diff `0251fa8..b5ac567` (production + tests + task-api):

```
po-agent-platform-v2/src/po_agent/harness/agent_core_v4_reliable.py | 35 +++++++++-
po-agent-platform-v2/tests/test_agent_core_v4_reliable.py           | 58 ++++++++++++++++
po-agent-platform-v2/tests/test_agent_core_v4_wave_s1.py            |  4 +-
```

Invariants — all PASS:

1. **No planner/router changes.** Only `agent_core_v4_reliable.py` (the literal-grounding guard layer), 2 test files. No `v4_plugins/`, no `runtime_factory.py`, no adapters, no `task-api/` changes.
2. **Guard change is generic trusted-observation grounding, not release-specific routing.** New `_trusted_release_values(observations)` scans only observations with `capability_id == "release.search"` and collects `data["release_id"]` and `releases[].id` (casefolded). In `_validate_call_literals`, the `release_id` branch first keeps the pre-existing product-space rejection (`raw.upper() in APPROVED_PRODUCT_SPACES` → V4ContractError), then `continue`s only if the literal is in `trusted_releases`. No new skill id, no routing branch, no memorized source facts (values come from the governed observation only).
3. **Arbitrary release ids remain rejected.** An id not emitted by a `release.search` observation falls through to the standard query-derived/session-context checks and is rejected (unit test `test_release_id_literal_is_accepted_only_from_trusted_release_search_observation` asserts `invented-release-id` → V4ContractError).
4. **release.health remains plugin/registry-owned.** Untouched this assignment (A213 plugin-only change at `v4_plugins/core.py`); binding `CapabilityBindingV4("release.health", build_release_health)` intact.
5. **No hardcoded release ids/spaces/tasks in the diff** — test fixtures use the WMB/24Q1 sample; production code references capability ids only.
6. **dummy-55 invariant:** plugin suite GREEN (included in the 154, see Phase 1).

## Phase 1 — tests

`po-agent-platform-v2` venv:

- Focused: `test_agent_core_v4_reliable.py` + `test_agent_core_v4_release_health.py` + `test_agent_core_v4_wave_s1.py` → **19 passed** (incl. the 2 new trusted-release-id tests: trusted search UUID accepted (single + list-row forms), invented id rejected).
- All V4 suites (`tests/test_agent_core_v4*.py tests/test_v4*.py`) → **154 passed, 0 failed** (A213 was 151/152; the stale `wave_s1` assertion is now aligned to the current plugin-owned tuple `{space.resolve, release.search, release.health}` — F1 CLOSED).

Requirements met: trusted UUID literal passes; invented UUID fails; product-space-as-release_id still fails (code path preserved, pre-existing guard line unchanged); release-health focused tests pass; no stale assertions remain.

## Phase 2 — live NL release.health (API)

All three forms reach the new chain and fail closed on the source limitation:

| # | Query | Status | warning | Trajectory | Result |
|---|-------|--------|---------|------------|--------|
| 1 | `здоровье релиза 24Q1 в WMB` | FAILED | `v4_capability_unavailable` | space.resolve → release.search(WMB, 24Q1, require_single) → **release.health(release_id=7a84006f-…, space=WMB)** | typed; answer: «Необходимая возможность не подтверждена источником данных и не выполняется» |
| 2 | `здоровье релиза 1.6.0 в OLP` | FAILED | `v4_capability_unavailable` | same chain, OLP / `20ba588e-…` | typed, 21.8 s |
| 3 | `здоровье релиза в OLP` | FAILED | `v4_capability_unavailable` | same chain (OLP has exactly 1 release → require_single resolves) | typed, 24.0 s |

Key evidence (form 1, full re-run):

- Trajectory turns 1–4: `load_skill` → `space.resolve {reference: WMB}` → `release.search {space: WMB, query: 24Q1, require_single: True}` → `release.health {release_id: '7a84006f-7823-4052-ae46-b94f5165518e', space: 'WMB'}` — the exact authoritative UUID from the observation passes the guard (D-A213-1 gone; no `V4ContractError`).
- `error`: `release.health requires authoritative release-to-task membership; the current REAL AS21 task source does not expose populated release linkage` — the A213 bounded handler firing by design.
- task-api log: `GET /api/v1/swtr-read/task-query?limit=100&max_pages=100&space=WMB&release=7a84006f-…` 200 (bounded, space-scoped, single page) and the OLP analogue — **space-scoped bounded membership call proven live**.
- No `total`/`completed`/percent anywhere in payloads; no product-as-release confusion; no generic `v4_runtime_failure`.

## Phase 3 — Browser C (UI 5175, Playwright)

| # | Case | UI status | Checks |
|---|------|-----------|--------|
| C1 | `здоровье релиза 24Q1 в WMB` | COMPLETED (28.0 s) | errVisible=false, no 0/0, no stack/session/contract leak. Renders release identity (name/ID) and explicitly states health metrics «в текущих наблюдениях не представлены» — honest source-limitation, no fake health card |
| C2 | `здоровье релиза 1.6.0 в OLP` | COMPLETED (15.8 s) | same: release identity table + explicit "no health data in observations"; no fabricated percentages |
| C3 | `какие релизы в WMB` (control) | COMPLETED (10.1 s) | 3-release list renders correctly (24Q1/24Q2/25Q1 with UUIDs) |

Note: the UI path completed with the honest identity-plus-limitation answer (release.search observation only, health handler did not run in these runs); the API path (Phase 2) proves the guard→handler→typed-unavailable chain. Both surfaces present the source limitation clearly and fabricate nothing.

## Phase 4 — retained release.search (A212 parity)

| Space | Result |
|-------|--------|
| WMB | COMPLETED — 3 releases (24Q1, 24Q2, 25Q1, UUIDs exact) |
| OLP | COMPLETED — 1 release (1.6.0, `20ba588e-…`) |
| DMS | NEEDS_CLARIFICATION «В REAL AS21 не найден подходящий релиз. Уточните название или идентификатор.» (authoritative 0 — A212 cosmetic carry, unchanged) |

**A212 parity GREEN** (6 `GET /versions` calls, all 200).

## Phase 5 — retained regression and audit

- Wave S2 metric (sprint.health, `DMS-SPRNT-3`): 68 total / 17 completed (25%) / 13 in work / 2 blocked — consistent with A210/A208B lineage (drift-verified).
- task.lookup `DMS-380`: COMPLETED, source-accurate (Закрыт/Closed, mTLS/Lineager title).
- person+status `открытые задачи Жданова в DMS`: COMPLETED via `space.resolve → member.resolve → task.search` → `[DMS-371, DMS-1]` 2/2 (drift-exact per A210/A208B).
- dummy-55 / plugin registry: GREEN (within the 154).
- Fresh audit window (this assignment's task-api traffic): **local factual `GET /api/v1/tasks` reads = 0**; **unscoped (no `space=`) `task-query` scans = 0**; all 19 task fetches via `swtr-read/tasks/`, 6 `versions`, 4 `sprints/`, 2 space-scoped release task-queries.

## Defect status

| ID | A213 status | A214 status |
|----|-------------|-------------|
| D-A213-1 (release_id literal-grounding guard, no trusted-observation exemption) | BLOCKING RED | **CLOSED** — generic `_trusted_release_values` exemption proven at unit (2 tests) and live (3/3 forms reach handler) level; arbitrary/product-space ids still rejected |
| F1 (stale wave_s1 contract assertion) | non-blocking | **CLOSED** — assertion aligned; V4 suites 154/154 |

## Recommendation

Release remediation for V4 can be closed as:

- `release.search` = **GREEN** (end-to-end, A212);
- `release.health` = **terminal SOURCE_CONDITIONAL** — correctly bounded and fail-closed until authoritative release→task membership exists in the REAL AS21 task source (source-data limitation, proven empty in A211/A212; not a code defect).

**Recommend resuming V4-CATALOG with the next five-skill batch.**

## Services left running

- UI 5175 (PID 55236) / 5176; agent 8212 (PID 43636 @ `b5ac567`); task-api 8241 (PID 29761, system python3, SSE 48 tools); MCP-SWTR 3000 (PID 29268).
