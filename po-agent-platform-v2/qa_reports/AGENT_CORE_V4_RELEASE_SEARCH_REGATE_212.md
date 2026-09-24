# AGENT_CORE_V4_RELEASE_SEARCH_REGATE_212

**Assignment:** 212 — release.search re-gate + release.health linkage oracle
**Date:** 2026-09-24
**Role:** QA/adversarial + source/oracle analysis only (no production/test/config edits)
**Branch:** `feat/core8-real-query-hardening-v2`

| Field | Value |
|---|---|
| START_HEAD | `51bc4d49ced9911033211170785c7ed7310d2af7` |
| A211 baseline (diagnostic) | `218eb01` |
| Owner fix commit | `2c630b1` (task-api only) |
| Agent under test | port 8212, PID 29798, HEAD `51bc4d4` |
| task-api | 8241, PID 29761 (system python3, SSE, 48 tools) — **restarted** at `51bc4d4` |
| MCP-SWTR | 3000, PID 29268 |
| UI | 5175 (55236) / 5176 (12824) |

## VERDICT

**RELEASE_SEARCH_GREEN_HEALTH_LINKAGE_BLOCKED**

`release.search` is fully re-gated GREEN end-to-end (source parity, adapter parity, natural-language gate, Browser C) — the owner fix `2c630b1` (D1: emit schema-required `calculatedAttributes:null`; D2: unwrap the MCP envelope into a `versions` list + pagination metadata) is certified. The A211 defect is closed: `/versions` now returns 200 with a coherent list wherever the live source has data.

The release.health **linkage is BLOCKED at the source-data level** (Phase 5, independent evidence, not a code defect): the only task-side version field, `fix_version_s`, is **uniformly empty** across WMB (all 2374 tasks), STS (sampled 50), and DMS-399. Neither the release UUID `code` nor the release `name` resolves to any task. So `release.health` has no authoritative release→task membership to compute a completed/total denominator from in the current source. This requires an owner/product decision (find the real membership mechanism or confirm it is not recorded in SWTR), not a code change.

---

## P0 — Architecture invariant: CLEAN

`git diff --stat 218eb01..51bc4d4 -- po-agent-platform-v2/src task-api` = **1 file**:
- `task-api/app/routers/swtr_read.py` (+35/−1).

Zero changes to Agent Core / planner / runtime / plugins / adapters (verified empty diff across `agent_core_v4*.py`, `runtime_factory.py`, `v4_plugins/*.py`, `adapters/*.py`). `release.search` remains plugin/registry-discovered (`v4_plugins/wave_s1.py` untouched). The fix is exactly A211's recommended bounded task-api plumbing:
- `_schema_aware_search_versions_arguments` now emits `calculatedAttributes: None` (guarded on the live schema declaring it) in both the nested-`request` and flat branches;
- the `GET /versions` handler unwraps the tool envelope into `versions: list` and preserves `total_elements` / `has_next` / `source_page` / `source_page_size`; type-validates the list.

**dummy-55 / plugin invariant: 25 passed** (GREEN). No architecture drift.

## P1 — Direct source vs Task API `/versions` parity: GREEN (4/4)

Same live MCP schema/oracle method as A211. For each space, direct MCP (`search_versions` with `calculatedAttributes:null`) vs `GET /api/v1/swtr-read/versions`:

| Space | direct total | route HTTP | `versions` is list | route n | total_elements | has_next | set parity |
|---|---|---|---|---|---|---|---|
| WMB | 3 | 200 | yes | 3 | 3 | false | **exact** |
| OLP | 1 | 200 | yes | 1 | 1 | false | **exact** |
| STS | 11004 | 200 | yes | 100 (page) | 11004 | true | **exact (first page)** |
| DMS | 0 | 200 | yes | 0 | 0 | false | **exact (empty)** |

- Route returns 200 wherever direct MCP returns 200 (A211's 502 is gone).
- Exact version/release set parity for source-backed rows (UUID `code` sets identical).
- **DMS zero is authoritative REAL_EMPTY** (200, `totalElements:0`, not source-unavailable) — confirmed even with `withArchived`/`withDeleted` in A211.
- `versions` is a JSON list; pagination metadata coherent (`total_elements`/`has_next` present and consistent; STS correctly `has_next=true` at 11004).
- No local/cache fallback (route calls live MCP `search_versions`).

## P2 — Adapter `search_versions_bounded` parity: GREEN (4/4)

Ran the production `EvidenceValidatedProductionTaskApiAS21Adapter.search_versions_bounded(query=None, space=X)`:

| Space | adapter n | codes == route | error |
|---|---|---|---|
| WMB | 3 | **yes** | none |
| OLP | 1 | **yes** | none |
| STS | 100 | **yes** | none |
| DMS | 0 | **yes** | none |

- Exact set parity with Task API / direct MCP.
- **No malformed-payload error** (D2 fix certified — the envelope is unwrapped to a list before the adapter sees it).
- No tenant task scan; no local factual reads (task-api log: 8 `/versions` calls, 0 tenant scans, 0 local `/api/v1/tasks`).
- Sample rows are real version objects: WMB `{"code":"7a84006f-…","name":"24Q1"}`, OLP `{"code":"20ba588e-…","name":"1.6.0","description":"релиз 1.6.0"}`.

## P3 — release.search natural-language gate: GREEN (5 forms)

| Query | status | count | result |
|---|---|---|---|
| `релизы WMB` | COMPLETED | 3 | `[24Q1, 24Q2, 25Q1]` exact, multi-list |
| `релизы OLP` | COMPLETED | 1 | `[1.6.0]`, `release_id=20ba588e-…` (correct single) |
| `релизы DMS` | **NEEDS_CLARIFICATION** | 0 | "В REAL AS21 не найден подходящий релиз. Уточните название или идентификатор." (typed, no options) |
| `какие релизы есть в WMB` | COMPLETED | 3 | `[24Q1, 24Q2, 25Q1]` exact |
| `релиз 24Q2 в WMB` | COMPLETED | 1 | `[24Q2]`, `release_id=460d173f-…` (exact match) |

Verified:
- Correct skill load + space resolution: every COMPLETED form routed `space.resolve → release.search`.
- Exact source parity (WMB 3/3, OLP 1/1, 24Q2 1/1).
- **No product-space-as-release-id confusion**: `release_id` is always the version UUID, never "WMB"/"DMS".
- Multiple results stay a list (`release_id=null` for 3-result WMB); single result sets `release_id`.
- **DMS source-backed zero is not fabricated** into a release.

**Separately classified contract behavior (not hidden):** the current `build_release_search` renders a source-backed **empty** directory as `V4NeedsClarification` ("не найден подходящий релиз…") rather than a clean `REAL_EMPTY`. This is code-deterministic (`raise V4NeedsClarification` when `rows` is empty), not fabrication, and it is the correct fail-safe for "no release found" — but it means a genuinely-empty space (DMS) is shown as a clarification prompt instead of an explicit zero-result. **Owner decision:** if a real empty release directory should render as `REAL_EMPTY` (0 releases) rather than "clarify the name", the empty branch in `build_release_search` should be split (space-known-and-empty → REAL_EMPTY; unknown/ambiguous → clarification). Non-blocking for release.search correctness.

## P4 — Browser C: GREEN (3/3)

Real UI (`http://[::1]:5175/` → agent 8212):

| Case | status | panel | source-unavailable? | error? | leak? |
|---|---|---|---|---|---|
| C1 `релизы WMB` | COMPLETED | rendered | no | no | no |
| C2 `релизы OLP` | COMPLETED | rendered | no | no | no |
| C3 `релизы DMS` | NEEDS_CLARIFICATION | rendered | no | no | no |

- WMB/OLP render the real release list (3-row / 1-row tables with UUIDs) in the V4 `release_list` widget; `source=REAL_AS21`, `bounded=true`.
- DMS renders the typed clarification ("не найден подходящий релиз") in the same widget — **no source-unavailable** for a healthy source, no fabricated list.
- No generic "не смог безопасно завершить" error, no stack trace, no backend `session_id`/`correlation_id`/`trace_id` in the user-facing answer.
- Screenshots: `qa_212_browser_c/`. (The V4 evidence/trace panel shows the structured capability data — intended UIContract presentation, not a leak.)

## P5 — release-health linkage oracle: BLOCKED (source-data)

For the real WMB release **24Q1** (`code=7a84006f-7823-4052-ae46-b94f5165518e`):

| Item | Finding |
|---|---|
| Release catalog identifier(s) | UUID `code` (`7a84006f-…`) + `name` (`24Q1`); fields `code`, `name`, `description`; **no `status`** populated. |
| Task-side attribute code(s) | `fix_version_s` is the **only** version-like attribute on tasks (raw WMB units have 54 attrs; DMS-399 also exposes a separate `fix_version`). |
| `fix_version_s` population | **Uniformly empty** — WMB all 2374 tasks `[]`; STS sampled 50/50 `[]`; DMS-399 `fix_version` `[]`. |
| Candidate: UUID `fix_version_s` | `space="WMB" AND fix_version_s="7a84006f-…"` → **0 rows** (direct MCP + route, complete single page). |
| Candidate: name `fix_version_s` | `space="WMB" AND fix_version_s="24Q1"` → **0 rows**. |
| Candidate: `fix_version` (UUID / name) | **0 rows** both. |
| Exact bounded query | `GET /api/v1/swtr-read/task-query?space=WMB&release=7a84006f-…` → 200, `count=0`. |
| Membership task-key set | **∅** (empty) for every WMB release. |
| Membership completeness | **Proven** — `fix_version_s` is a declared attribute present on all raw units and uniformly empty; the bounded space-scoped query returns a complete single page with 0 matches. |

**Conclusion:** the task-query release predicate/field (`fix_version_s`) is the correct schema field, but **WMB/STS/DMS tasks do not populate it**, so no release→task membership is resolvable in the current source. The version catalog (24Q1/24Q2/25Q1) has no task linkage. This is a **source-data fact** (owner/product decision), not a code defect.

**Smallest owner path to unblock release.health (strictly from this evidence):**
1. Confirm the real release-membership mechanism with the SWTR/product owner — either the correct field/identifier (the UUID `code` is the catalog identity, but tasks don't carry it), or a release→task relationship exposed by a different read tool. The current `fix_version_s` predicate returns nothing because the field is empty, so release.health cannot compute a denominator until membership is resolvable.
2. If membership is genuinely not recorded in SWTR for these spaces, release.health should be implemented to **fail closed / report source-unavailable for the membership** (not fabricate 0), mirroring the sprint.predictability baseline pattern.
3. Do **not** route release.health through a tenant-wide task scan (A204 timeout lineage); the bounded `task-query?space=&release=` facade is the correct building block once a working identifier is known.

## P6 — Retained regression + audit: GREEN

| Check | Result |
|---|---|
| One Wave S2 metric — `cycle time спринта DMS-SPRNT-3` | COMPLETED (`sprint.resolve → sprint.cycle_time`), 23.4 s |
| `sprint.health` (DMS-SPRNT-3) | COMPLETED, 68 tasks |
| `task.lookup` DMS-380 | COMPLETED |
| person+status `Открытые задачи Жданова в DMS` | COMPLETED, `[DMS-371, DMS-1]` |
| dummy-55 plugin invariant | 1 passed |
| Local factual `GET /api/v1/tasks` reads (agent + task-api) | **0** |
| Local `POST /api/v1/query` reads | **0** |
| Tenant-wide `swtr-read/tasks?` scans | **0** |
| Agent `/versions` calls (A212) | 9, **all 200** (0 502 — D1/D2 fix works end-to-end) |
| Task-api task-query calls (Phase 5) | 5, all space-scoped (bounded); the one STS broad scan bounded-fail-closed on `max_pages` |

No regression from A210 GREEN.

---

## Non-observations / notes
- A transient sub-second `v4_runtime_failure` batch hit only on the first 5 requests immediately after the agent restart (warm-up); all queries succeeded on the next pass and the re-run (control `Покажи DMS-380` + `релизы WMB` both COMPLETED). Not a code defect; recorded for transparency.
- `search_versions` tool present; SSE transport healthy (48 tools).
- DMS has no releases in the version catalog (0 even archived/deleted) — source data fact.

## Services left running
UI 5175 (55236) / 5176 (12824), agent 8212 (PID 29798 @ `51bc4d4`), task-api 8241 (PID 29761, system python3, SSE 48 tools), MCP-SWTR 3000 (PID 29268).
