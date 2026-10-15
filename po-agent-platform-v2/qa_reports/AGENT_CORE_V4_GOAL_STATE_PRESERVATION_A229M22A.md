# A229M2.2A — Verified Observation State Preservation (strict independent QA)

**Verdict:** `AGENT_CORE_V4_GOAL_STATE_PRESERVATION_RED_A229M22A`
**First failing boundary:** P1/P3 — lookup-based multi-goal state preservation (M2/M4/C5) is **non-functional for real source data**: the real `DMS-267` `task.lookup` observation compacts to **8343 bytes**, which exceeds the owner's `_MAX_CARRIED_STATE_BYTES = 8192` cap, so `guard_completed_goal_coverage(preserve_state=True)` **fails closed and carries no state** for all three lookup-based scenarios. Live-confirmed 3/3.
**Date:** 2026-10-15
**Role:** independent QA / forensics only. **Zero** production, test, config, Core, or frontend edits. **Zero** flag flips on the default stack (flag-ON runs were isolated QA agent sessions only).
**Scope:** stage STATE PRESERVATION (not guaranteed missing-goal execution, not a security certification, not permission to enable the flag).

---

## 0. Baseline (P0) — GREEN

- **TESTED_HEAD / START_HEAD:** `f6d9fe5be47b4091c14a7278646893cb76a9b6b3` (branch `feat/core8-real-query-hardening-v2`, pulled `--ff-only` from `2fdde65`).
- **Owner delta `2fdde65..f6d9fe5`** — confined to the 4 files named in the spec (plus docs):
  - `src/po_agent/api/v1/goal_coverage.py` (+76): new `_build_internal_continuation` (`_MAX_CARRIED_OBSERVATIONS=6`, `_MAX_CARRIED_STATE_BYTES=8192`, `_PROVENANCE={"REAL_AS21"}`); `guard_completed_goal_coverage(..., preserve_state=False)` now supplies `continuation_observations` + `goal_continuation_pending` before `data.pop("results")`, and appends `v4_goal_continuation_state_unavailable` when it cannot.
  - `src/po_agent/api/v1/__init__.py` (+10): passes `preserve_state=settings.v4_goal_continuation_enabled` to the guard; **new expiry sweep + 100-entry global bound** in `_remember_clarification` (spec P3 item — implemented).
  - `src/po_agent/config/settings.py` (+5): `v4_goal_continuation_enabled` default `False`, env `V4_GOAL_CONTINUATION`/`PO_AGENT_V4_GOAL_CONTINUATION`.
  - `tests/test_v4_goal_coverage.py` (+53): 3 new tests.
  - Docs: `GIGACODE_NEXT_ACTION.md`, `PO_AGENT_HARNESS_EVOLUTION_PLAN.md`.
- **Core 6/6 byte-identical** to frozen `6fb335d`: `agent_core_v4.py=52100ca1`, `agent_core_v4_robust.py=3bdb4d09`, `agent_core_v4_reliable.py=1f7562dc`, `agent_core_v4_completion.py=cf75a6d6`, `v4_plugin_registry.py=d82929d1`, `llm/real.py=1cc10e12`. No planner/registry/task-source diff.
- **Tracked worktree:** clean (only pre-existing `M GIGACODE.md`, not part of this gate).
- **Tests (P0.2) — zero failures:**
  - Focused (`test_v4_goal_coverage`, `test_v4_browser_api_contract`, `test_v4_synthesis_elision`, `test_runtime_env_aliases`): **42/42 passed**.
  - Full V4 blast `test_agent_core_v4*.py + test_v4*.py`: **285/285 passed** (282 baseline + owner's 3 new).
  - Task API canonical SWTR (`test_swtr_assignee_canonical`, `test_swtr_assignee_timestamps`, `test_swtr_task_query_partial`): **16/16 passed**.
  - Frontend `npm run build`: **exit 0**.
- **Feature flags:** `v4_goal_coverage_guard_enabled` and `v4_goal_continuation_enabled` both **default `False`**; `v4_synthesis_elision_enabled` default `False`. Unchanged defaults.

---

## 1. P1 — real observation shape / offline replay

Captured **exact production REAL AS21 result-row shapes** from the live `f6d9fe5` agent (single-goal queries, guard inert) — `task.search_assignee` (person collection), `task.lookup` (DMS-267), `task.hierarchy` (DMS-267), `task.dependencies` (the "связанные" route). No invented fixtures. Then drove the **real** `guard_completed_goal_coverage(..., preserve_state=True)` + real `AgentCoreV4Runtime._compact_data` + real `V4Observation`.

### 1.1 GREEN items (safety + person-collection)

| Check | Result |
|---|---|
| **M1** (K WMB proven, S DMS missing) | Carries the **proven** `task.search_assignee` row only; compact **536 B**; `planner_view` shape `{step, capability_id, arguments, answer, data}`; `source=REAL_AS21`, `member_login`, `space`, `count`, `task_key_count`, `task_keys_sample[:20]` preserved; full `tasks` list + raw `source_data` dropped. `goal_continuation_pending=True`. |
| 173-task collection | Compact carries `count=173` + **only first 20 keys** (`task_keys_sample`); full 173-key set NOT persisted — re-fetch required for final rendering (noted, correct). |
| `>6` observations | 7 candidate rows → **fail closed**, `v4_goal_continuation_state_unavailable`, no continuation. |
| `>8192 B` (artificial 120-attr) | **fail closed**, no continuation. |
| `source=LOCAL` / `source_unavailable` / `source_complete=False` | **NOT carried** (fail closed each). |
| No cross-goal binding | Unproven goal's `source_unavailable` row excluded; only proven `Калачанов` row carried. |
| No huge raw cards (M1) | Raw `source_data` / full `tasks` dropped from the carried compact; `description` fields truncated to ≤384 by `_compact_data`. |
| `planner_view` shape | Carried obs rebuilds into `V4Observation` with the exact 5 keys. |

### 1.2 🔴 FIRST FAILING BOUNDARY — lookup-based preservation (M2/M4/C5) non-functional on real data

| Case | Real proven row | Real compact size | Carried | Warning |
|---|---|---|---|---|
| **M2** «Покажи задачу DMS-267 и её иерархию» (lookup proven / hierarchy missing) | `task.lookup` DMS-267 | **8343 B** | **0** | `v4_goal_continuation_state_unavailable` |
| **M4** «Покажи задачу DMS-267, её иерархию и задачи Калачанова в WMB» | `task.lookup` DMS-267 | **8343 B** | **0** | same |
| **C5** «Покажи задачу DMS-267 и связанные с ней задачи» | `task.lookup` DMS-267 | **8343 B** | **0** | same |

**Measured:** `AgentCoreV4Runtime._compact_data("task.lookup", <real DMS-267 data>)` = **8343 bytes** (`> _MAX_CARRIED_STATE_BYTES=8192`). The owner's `_build_internal_continuation` serializes the full carried list (even larger) and returns `[]` when over the cap.

**Root cause:** `_compact_data` **does not strip `source_data`** (the raw `swtr_attributes` card, ~35 attributes ≈ 8 KB). That raw card is exactly the "raw card" the spec says must never be persisted ("Never pass huge descriptions/raw cards to persistent state"), and its presence pushes the real lookup over the 8 KB cap. Net effect: for every real `task.lookup`-anchored multi-goal query, state preservation **degrades to stage 1** (nothing carried).

**Live end-to-end confirmation (BOTH_ON agent, `f6d9fe5`), M2 run ×3 — 3/3:**
```
status=NEEDS_CLARIFICATION  goal_coverage={requested:2, proven:['g2'], unproven:['g1']}
warnings include v4_goal_continuation_state_unavailable
visible JSON: no data.results, no continuation_observations
```
So the canonical "DMS-267 lookup + hierarchy" scenario — the one P3 explicitly requires ("Verify successful **carried DMS-267 lookup** does NOT prove absence of parent; hierarchy is missing until governed `task.hierarchy` executes (oracle parent DMS-253)") — **cannot preserve the lookup at all**, so that P3 test is unperformable as specified.

### 1.3 Test masking (owner suite passes 285/285 but does not exercise the real shape)

The 3 new owner tests all use **small synthetic `task.lookup` fixtures that omit `source_data`**:
- `test_preservation_carries_only_source_backed_proven_goal` — person-collection with tiny `task.search` (`tasks:[{key:WMB-6}]`).
- `test_preservation_disabled_and_unproven_source_fail_closed` — `task.lookup {task_key:DMS-267}` (no source / `LOCAL`).
- `test_preservation_fails_closed_for_large_or_partial_source_data` — "large" = an artificial `"payload":"x"*100000` **string**, not the real ~8 KB `source_data.swtr_attributes` card.

None carries the real DMS-267 `task.lookup` shape, so the suite is green while production lookup-based preservation fails closed. (Same masking class as A222R / A229U2.)

---

## 2. Safety posture (intact — this is a FUNCTIONAL RED, not a security RED)

- Guard is **fail-closed**: over-cap / over-count / non-REAL_AS21 / `source_unavailable` / `source_complete=False` all → **no** continuation, only a typed warning. No unsafe state supplied.
- Public payload: `continuation_observations`/`continuation_required_skills` are popped before send (verified in the offline `_remember_clarification` path); `data.results` stripped. No new public field.
- Owner's **100-entry bound + expiry sweep** in `_remember_clarification` is implemented (addresses the A229M2.2F S5 unbounded-growth gap).
- Session ownership / no-auth remains **OPEN / deployment blocker** (per spec) — not re-tested here (STOP), still recorded.

---

## 3. Owner fix proposal (not implemented by QA)

1. **Strip the raw provenance card before persisting.** In `_build_internal_continuation`, after `AgentCoreV4Runtime._compact_data(...)`, drop raw-card keys (at minimum `data["task"]["source_data"]`, and any `source_data`/`swtr_attributes`), keeping only the canonical fields the completion frontier + follow-up need (`task_key`, `count`, `task_keys_sample`, `task_key_count`, `member_login`, `space`, `assignee_login`, `assignee_id`, `parent_chain`, `depth`, `root_key`, `epic_key`, `related_keys`, `source`). This directly satisfies "never pass raw cards to persistent state" and brings the real DMS-267 lookup well under 8 KB so M2/M4/C5 carry.
   - Alternative (weaker): keep `source_data` and raise the cap — rejected: persists a raw card, and 8 KB is the wrong knob for unbounded attribute counts.
2. **Non-mocked regression with the REAL DMS-267 `task.lookup` shape** (including `source_data.swtr_attributes`): assert it IS carried (not fail-closed) and that `continuation_observations` contains the canonical lookup fields with the raw card stripped. Add a companion case proving a genuinely >8 KB state still fails closed.
3. Re-run the full A229M2.2A gate (P0–P3) after the fix.

**Re-gate acceptance (lookup-based):** real M2/M4/C5 must carry the proven lookup (compact < 8 KB, raw card stripped), `goal_continuation_pending=True`, and the P3 "carried DMS-267 lookup does not prove absence of parent (oracle DMS-253 via `task.hierarchy`)" test must be performable.

---

## 4. Not run (STOP at first RED boundary)

P2 (live flag ON/OFF HTTP matrix beyond the M2 confirmation), full P3 (continuation no-re-read replay, TTL/100-bound/sweep live, adversarial session, browser), P4 (facts/latency/acceptance) — **not executed** per the STOP rule. The first failing boundary (P1/P3 lookup preservation) blocks the gate.

---

## 5. Verdict

`AGENT_CORE_V4_GOAL_STATE_PRESERVATION_RED_A229M22A`

- **TESTED_HEAD:** `f6d9fe5be47b4091c14a7278646893cb76a9b6b3`
- **Core hashes:** `52100ca1 / 3bdb4d09 / 1f7562dc / cf75a6d6 / d82929d1 / 1cc10e12` (6/6 = frozen `6fb335d`).
- **Pass counts (P0):** focused 42/42; V4 blast 285/285; Task API canonical SWTR 16/16; frontend build exit 0.
- **First failing boundary:** real `DMS-267` `task.lookup` compact = **8343 B > 8192 B** `_MAX_CARRIED_STATE_BYTES` → `guard_completed_goal_coverage(preserve_state=True)` fails closed → **M2/M4/C5 carry no state** (live 3/3 `v4_goal_continuation_state_unavailable`). Owner tests mask it with synthetic small fixtures.
- **Continuation evidence retained:** M1 person-collection carried (536 B, real `task.search_assignee`, REAL_AS21); M2/M4/C5 carried 0 (real `task.lookup` over cap).
- **Safety:** intact (fail-closed, no public leak, 100-bound + sweep implemented); session ownership remains OPEN deployment blocker.
- **OPEN risks (carried forward):** external auth / session ownership (deployment blocker), stale compact results (15-min TTL, no re-validation), lexical detector false negatives (comparisons/English/nested/elided), no `PARTIAL` renderer, repeat-read risk on follow-up, and (new) raw `source_data` card not stripped by `_compact_data`.
- **No checkpoint, no default flag flip, no production edits.**

**Owner next action:** implement the §3 fix (strip raw `source_data` card in the continuation + real-shape non-mocked regression), then re-run the full A229M2.2A gate. Do NOT enable either goal flag on the real stack until GREEN.
