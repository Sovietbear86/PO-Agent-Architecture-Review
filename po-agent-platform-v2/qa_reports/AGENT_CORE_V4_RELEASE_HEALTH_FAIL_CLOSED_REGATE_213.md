# A213 — Release Health Fail-Closed Re-Gate (QA)

**Date:** 2026-09-24
**START_HEAD:** `e194ae75dc37ed86ef6c8737b1cffe8a9e8431ce` (`e194ae7`)
**Branch:** `feat/core8-real-query-hardening-v2`
**Baseline:** A212 `a8ff162` (RELEASE_SEARCH_GREEN_HEALTH_LINKAGE_BLOCKED)
**Owner hardening under test:** `4c81342` (release health bounded + fail closed) + `9f973f7` (focused tests)

## Verdict

**`RELEASE_HEALTH_RED`**

Sole blocking defect: **D-A213-1** — the live NL `release.health` path is deterministically blocked (7/7 observed runs) by the pre-existing generic literal-grounding guard in `agent_core_v4_reliable.py` before the new fail-closed handler ever executes. The spec-required typed `SOURCE_CONDITIONAL`/`SOURCE_UNAVAILABLE` outcome is therefore unreachable through the natural-language path. The owner's handler itself is correct and unit-proven; the blocking layer is the guard's `release_id` treatment, which — unlike `assignee` — has no trusted-observation exemption.

---

## Phase 0 — architecture invariant: PASS

- Diff `a8ff162..e194ae7` (production + tests) touches **exactly two files**:
  - `po-agent-platform-v2/src/po_agent/harness/v4_plugins/core.py` (+85/−8)
  - `po-agent-platform-v2/tests/test_agent_core_v4_release_health.py` (new, +62)
- **No Agent Core / planner / runtime / adapter / task-api changes** (diff over `agent_core_v4*.py`, `runtime_factory.py`, `runtime.py`, `dialogue_runtime.py`, `adapters/*.py` = empty).
- `release.health` remains registry/plugin-discovered: live responses show `loaded_skills: ["release.health"]` and plugin ids `builtin.core.a188`, `builtin.wave_s1.sprint_flow_release_search`, etc.
- Binding is now **plugin-owned**: `CapabilityBindingV4("release.health", handler_builder=build_release_health)` — the legacy `legacy_capability_id="release.health"` runtime bridge is removed.
- **dummy-55 / plugin invariants: 25 passed** (registry discovery suite green).
- No hardcoded release ids/spaces/tasks in the production diff (only generic guards: empty `release_id` / empty `space` → typed clarification).
- Skill procedure updated to: space.resolve → `release.search` (require_single) → `release.health(release_id, space)`; legacy `release.resolve` step removed from the skill tuple. `release.resolve` capability + binding remain intact globally (core.py:84, :182).
- **Boundedness of the handler path proven by code chain:** `build_release_health` → `runtime.adapter.get_release_tasks(release_id, space)` → `task_api.py:506` builds `project = {space} AND release = {id}` → production `search_tasks` (production_task_api.py:154) → `GET /api/v1/swtr-read/task-query?space=<S>&release=<id>` — space-scoped, `limit=100`, `max_pages=100`, live-only, 502/503 → `AS21SourceUnavailable` (fail closed). **No legacy tenant-wide scan path remains** for this capability.
- Empty membership → `V4CapabilityUnavailable` (typed), never 0/0.

## Phase 1 — focused tests: PASS (1 non-blocking stale assertion)

- New focused tests **2/2 passed**:
  - `test_release_health_uses_bounded_space_scoped_membership` — bounded space-scoped membership call; metrics only from source-backed tasks.
  - `test_release_health_fails_closed_when_membership_is_not_exposed` — empty membership → typed fail-closed, never 0/0.
- V4 suites (`test_agent_core_v4*.py` + `test_v4*.py`): **151 passed, 1 failed**.
  - The single failure is **stale test-logic, not production**: `tests/test_agent_core_v4_wave_s1.py::test_release_health_contract_can_use_release_search_helper` asserts `"release.resolve" in release_health.capabilities`, but the owner intentionally removed `release.resolve` from the release.health **skill** capability tuple (the capability and its binding still exist globally). The test was not updated with the contract change.
- No legacy runtime release-health scan path (binding removed; unit-confirmed).

## Phase 2 — live NL release.health: **RED (D-A213-1)**

Agent restarted at `e194ae7` (PID 37584, `/live` 200). Five API runs + two Browser C runs (Section P3), all forms per spec:

| # | Query | Status | Trajectory | Error |
|---|-------|--------|------------|-------|
| 1 | `здоровье релиза 24Q1 в WMB` | FAILED (`v4_runtime_failure`) | load release.health → space.resolve(WMB) → release.search(WMB,"24Q1",require_single=True) → **release.health(release_id=7a84006f-7823-4052-ae46-b94f5165518e, space=WMB)** | `V4ContractError: planner literal is not grounded in user query or validated session context: release_id=7a84006f-...` |
| 2 | `здоровье релиза 1.6.0 в OLP` | FAILED | same shape → release_id=20ba588e-9b7e-43b2-b78a-465bdec0669a | same guard error |
| 3 | `здоровье релиза в OLP` | FAILED | same shape (planner searched OLP, got the single 1.6.0 id) | same guard error |
| 4–5 | re-probes of #1/#2 | FAILED | identical | identical |
| 6–7 | Browser C (C1/C2) | FAILED | identical | identical |

**7/7 deterministic, identical signature.**

### Root cause (localized)

`po-agent-platform-v2/src/po_agent/harness/agent_core_v4_reliable.py`, `_validate_call_literals` (line ~427–442):

- `key == "release_id"` falls into the `{"reference","space","sprint_id","release_id","task_key","product"}` branch, which accepts a literal **only** if it is query-derived (`_literal_is_query_derived`) or present in validated session context.
- The release id the planner passes is the **authoritative UUID returned by the prior `release.search` observation** (the new skill procedure mandates exactly this chain). A UUID is never query-derived (the user said "24Q1"/"1.6.0") and there is no session-context channel for it → deterministic rejection.
- Contrast: `key == "assignee"` has an explicit trusted-observation exemption (`raw.casefold() in trusted_identities`), and `$obs.N.*` references bypass the guard — but `_trusted_identity_values` (line 340) scans only person-identity keys `{member_login, external_id, assignee_login, assignee_id}`; **`release_id` is not in the trusted key set at all**.
- The planner (Qwen3.8) reliably re-emits observation literals instead of `$obs` references (documented A195B lineage) — so the `$obs.N.release_id` escape route is not dependable in practice.
- **Consequence:** the owner's own new procedure (space.resolve → release.search → release.health) is structurally unreachable for any model that echoes resolved ids as literals. The guard failure occurs **before capability execution**, so the handler's fail-closed behavior is never exercised live, no membership read occurs, and no tenant scan is possible.

**Classification:** pre-existing generic-guard gap (the `release_id` clause predates A213; it was latent because the A212 legacy path failed earlier at the 502 source boundary) — now exposed and made mandatory by the A213 procedure change. Safety is preserved (fail closed, zero fabrication, zero source reads on the failed turns), so this is a **functionality RED, not a safety RED**.

### Owner fix (smallest, guard-boundary)

In `_validate_call_literals`: for `key == "release_id"`, additionally accept `raw` when it is byte-equivalent (casefolded) to a `release_id` value (or a row `id` within `releases`) in a prior trusted `release.search` observation — mirroring the existing `assignee` exemption. Concretely: extend the trusted-value scan (or add a dedicated release-id set) with the observation key `release_id` (plus `releases[].id`), and accept membership in that set for the `release_id` argument. Keep the product-space-as-release-id rejection and the query-derived path. Add a non-mocked regression test: release.search → release.health literal-UUID passes the guard (mock adapter returning populated membership for the success branch and empty for the fail-closed branch).

**Expected post-fix behavior under current source state** (per A212 membership oracle — `fix_version_s` uniformly empty, UUID & name both → 0 tasks): release.search resolves the exact release → release.health executes bounded `task-query?space=<S>&release=<UUID>` → empty → typed `V4CapabilityUnavailable` (SOURCE_CONDITIONAL), no 0/0, no scan.

## Phase 3 — Browser C (real UI, `[::1]:5175` → agent 8212)

| Case | UI outcome | Checks |
|------|-----------|--------|
| C1 `здоровье релиза 24Q1 в WMB` | FAILED, generic "Agent Core v4 не смог безопасно завершить траекторию." (20.2s) | no 0/0 health card, no source-unavailable text, no session/contract leak, specific cause only in `data._agent_core_v4.error` (same A195B UI-surface pattern) |
| C2 `здоровье релиза 1.6.0 в OLP` | FAILED, same (28.6s) | same checks pass |
| C3 `релизы WMB` | COMPLETED — 3-release table renders correctly (17.4s) | release list unaffected by the defect |

Screenshots: `qa_213_browser_c/`. Note: the spec's "clear source-limitation message" requirement is **unreachable** while D-A213-1 blocks the trajectory before the handler runs; the UI shows the generic failure surface instead.

## Phase 4 — retained release.search: GREEN (A212 parity retained)

| Query | Status | Result |
|-------|--------|--------|
| `релизы WMB` | COMPLETED | 3 releases, exact A212 catalog: 24Q1 `7a84006f-...`, 24Q2 `460d173f-...`, 25Q1 `4a1199c2-...` |
| `релизы OLP` | COMPLETED | 1 release, exact: 1.6.0 `20ba588e-...` |
| `релизы DMS` | NEEDS_CLARIFICATION | source-backed 0 → typed "не найден подходящий релиз" — the A212-documented empty-directory-as-clarification cosmetic (pre-existing, owner decision item), **not hidden** |

No product-as-release confusion, no source-unavailable, no fabrication.

## Phase 5 — retained regression and audit: GREEN

| Probe | Result |
|-------|--------|
| Wave S2 metric — `cycle time спринта DMS-SPRNT-3` | COMPLETED, exact A210 parity: median 77.7 / mean 206.06 / min 0 / max 1230.43 h over 17 completed |
| `здоровье спринта DMS-SPRNT-3` | COMPLETED: 68 total / 17 completed (25%) / 13 active / 2 blocked (A210/A208B parity) |
| `открой задачу DMS-380` | COMPLETED: correct title, status Закрыт, Minor |
| `открытые задачи Жданова в DMS` | COMPLETED: member.resolve → Zhdanov.A.Ni → task.search → **2 open: DMS-371, DMS-1** (A212 parity) |
| dummy-55 / plugin registry | 25 passed (unit) |
| Local factual `GET /api/v1/tasks` reads (fresh window) | **0** |
| Unscoped (tenant-wide) `task-query` calls (fresh window) | **0** |
| Release-health failed turns → task-query calls | **0** (guard blocks before execution — no membership scan attempted, let alone tenant-wide) |

Fresh task-api window (marker at line 68): 19 bounded `swtr-read/tasks/{key}` evidence reads (known A204-F2 N+1 class on 68-task sprint, pre-existing), 4 `sprints/`, 3 bounded `versions` (P4), 1 **space-scoped** `task-query` (person+status), 1 `assignees/resolve`.

## Non-blocking findings

- **F1 (test-logic, stale contract):** `test_release_health_contract_can_use_release_search_helper` asserts `release.resolve` in the release.health skill capabilities; the owner removed it from the skill tuple (capability + binding remain globally). Update the assertion to the new tuple `{"space.resolve","release.search","release.health"}`.
- **F2 (cosmetic, pre-existing A212):** DMS empty release directory renders as `NEEDS_CLARIFICATION` rather than a typed REAL_EMPTY answer (owner decision item carried from A212).
- **F3 (known, pre-existing A204-F2):** sprint health/cycle_time performs one `swtr-read/tasks/{key}` evidence-validation GET per task (19 calls for 68-task sprint, 10–17s). Not an A213 concern.

## Services left running

- UI 5175 `[::1]` (55236), UI 5176 (12824)
- Agent 8212 — **PID 37584** @ `e194ae7` (`/live` 200)
- task-api 8241 (PID 29761, system python3, SSE, 48 tools) — unchanged from A212 (task-api code identical at `e194ae7`)
- MCP-SWTR 3000 (PID 29268)

LLM endpoint (Qwen3.8-27B) healthy this session (6–40s/call, no 500 clusters, no timeouts).

## Recommendation

Do **not** close release remediation. One owner fix at the guard boundary (Section P2) + one stale test update (F1), then re-gate: P2 forms (expect typed SOURCE_CONDITIONAL under the current empty-membership source), P3 Browser C (expect clear limitation message), P4/P5 retained. After GREEN, the A212 terminal-source-conditional closure for release.health remains the correct long-term state until authoritative release→task membership exists in the source.
