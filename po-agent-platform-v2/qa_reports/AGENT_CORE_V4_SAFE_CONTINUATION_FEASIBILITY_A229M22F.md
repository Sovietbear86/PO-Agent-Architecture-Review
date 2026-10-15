# A229M2.2F — Safe Continuation Feasibility (DESIGN / FORENSICS ONLY)

**Verdict:** `AGENT_CORE_V4_SAFE_CONTINUATION_FEASIBILITY_GREEN_A229M22F`
**Recommendation (exactly one):** `REUSE_CLARIFICATION_CONTINUATION`
**Date:** 2026-10-15
**Role:** independent QA / architecture investigator. Zero production, test, config, Core, plugin or frontend edits. Zero flag flips. No checkpoint.
**Scope:** decide whether multi-goal continuation can safely re-use validated observations through the existing V4 dialogue seam. This gate does NOT certify working multi-intent continuation.

---

## 0. Baseline (P0)

- **TESTED_HEAD / START_HEAD:** `a54a685356274834589e301c85e027e62ca169fe` (branch `feat/core8-real-query-hardening-v2`, pulled `--ff-only` from `025679a`).
- **Owner delta `a6f3fd4..a54a685`:** docs only — `GIGACODE_NEXT_ACTION.md`, `PO_AGENT_HARNESS_EVOLUTION_PLAN.md`, and the A229M2.1R report (`025679a`). **Zero** `src/`, `tests/`, `.env`, settings changes (git name-only verified). Code is therefore byte-identical to the A229M2.1R GREEN baseline `a6f3fd4`.
- **Tracked worktree:** clean (only pre-existing `M GIGACODE.md` at repo root, not part of this gate).
- **Core 6 hashes — byte-identical to frozen checkpoint `6fb335d`:**

| File | Blob (short) | Status |
|---|---|---|
| `src/po_agent/llm/real.py` | `1cc10e12` | ✓ |
| `src/po_agent/harness/agent_core_v4.py` | `52100ca1` | ✓ |
| `src/po_agent/harness/agent_core_v4_robust.py` | `3bdb4d09` | ✓ |
| `src/po_agent/harness/agent_core_v4_reliable.py` | `1f7562dc` | ✓ |
| `src/po_agent/harness/agent_core_v4_completion.py` | `cf75a6d6` | ✓ |
| `src/po_agent/harness/v4_plugin_registry.py` | `d82929d1` | ✓ |

- **Tests (P0.2):**
  - Focused (goal coverage, browser API contract, created-period, synthesis elision): **47/47 passed**.
  - Full V4 blast `test_agent_core_v4*.py + test_v4*.py`: **282/282 passed** (matches A229M2.1R exactly).
  - Config suites (`test_frontend_config.py`, `test_team_config.py`): **46/46 passed**.
  - Task API canonical SWTR suites (`test_swtr_assignee_canonical`, `test_swtr_assignee_timestamps`, `test_swtr_task_query_partial`): **16/16 passed**.
  - Frontend `npm run build`: **exit 0**.
  - Pre-existing, documented, NOT delta-caused (code byte-identical to GREEN baseline): `task-api/tests/integration/test_s21_agent_integration.py::test_swtr_adapter_initialization` fails with `AttributeError: 'SWTRAdapter' object has no attribute 'mcp_host'` — a stale structurally-broken integration test (A226R class), unrelated to the SWTR read path.
- **Feature flags:** `v4_goal_coverage_guard_enabled` (settings.py:69, env `V4_GOAL_COVERAGE_GUARD`/`PO_AGENT_V4_GOAL_COVERAGE_GUARD`) and `v4_synthesis_elision_enabled` (settings.py:64) — both **default `false`**, unchanged.

---

## 1. Architecture map (P0.3/P0.4) — request → guard → pending → response → follow-up → restored execution

All line numbers at TESTED_HEAD. Files: `api/v1/__init__.py` (A), `harness/agent_core_v4.py` (C), `harness/agent_core_v4_completion.py` (F), `harness/contracts.py` (H), `api/v1/goal_coverage.py` (G), `frontend/src/recovery/WorkspaceApp.tsx` (U).

```
POST /api/v1/query {query, session_id?, clarification_id?, clarification_option?}
 └─ A::_run_query (:520)
    1. session_id = payload.session_id | header X-Session-Id | uuid4()          A:523
       ⚠ client-chosen opaque string; no server-side ownership binding
    2. A::_prepare_query(payload, session_id)                                    A:344
       ├─ no clarification_id            → pop pending; fresh query             A:355-357
       ├─ unknown/expired/mismatched cid → NEEDS_CLARIFICATION "context lost" + POP  A:359-366
       ├─ option ∉ pending.options       → "invalid_clarification_option" (state KEPT)  A:369-375
       └─ valid → ONE-SHOT POP pending                                     A:376
          combined query = "Исходный запрос: …\nВопрос: …\nОтвет: …\nПродолжи…"  A:377-382
          → ClarificationContinuation(loaded_skills, observations, required)  A:384-387
    3. bundle.v4_runtime.process(HarnessRequest(
          query, session_id, resume_loaded_skills, resume_observations,
          required_completion_skills, session_context=_session_context_for))   A:533-540
       C::process (:1140):
       ├─ restore resume skills via catalog.load                               C:1148-1155
       ├─ restore V4Observation(step, cap, args, answer, data) — TRUSTED AS-IS  C:1156-1172
       │   (no source re-validation, no freshness check; TTL applies only to the
       │    pending record: 15 min monotonic)
       ├─ pin required_completion_skills into completion frontier              C:1176-1179
       └─ planner loop ≤ max_steps=8: LOAD / CALL / READY                      C:1183+
          ├─ CALL: capability must be exposed by loaded skills                 C:1262-1265
          │   literal guards (assignee MUST be $obs reference)                 C:1028-1057
          │   $obs.N.path resolution                                           C:1011-1033
          │   deterministic arg completion from typed resolver obs             C:1278-1290
          │   handler execution → full_results (raw) + V4Observation (COMPACT) C:1301-1308
          │   deterministic runtime_contract completion after each CALL        C:1310-1345
          ├─ READY: planner-READY accepted only if frontier satisfied          C:1206-1260
          └─ typed V4NeedsClarification → v4_state carries                     C:1379-1402
               continuation_observations  = ALL compact obs (planner_view)
               continuation_required_skills = loaded skills WITH contracts
               loaded_skills, trajectory
    4. A::_decorate_v4_response (ui contract, plugin_ids)                      A:541
    5. A::_promote_planner_failure_to_clarification                             A:542
       (FAILED→NC only for planner/period contract markers; provider errors
        429/timeout/connect NEVER promoted → stay FAILED)
    6. A::_guard_completed_constraint_coverage                                  A:546
       (COMPLETED + user period + task.* executed without created_period → NC)
    7. G::guard_completed_goal_coverage  [only if flag ON]                      A:549-553
       (COMPLETED + ≥2 detected goals + unproven → NC; strips answer/evidence/
        results; v4_state.goal_coverage={requested,proven,unproven})
       ✗✗ does NOT set continuation_observations / continuation_required_skills
    8. A::_remember_completed_session_context (COMPLETED only)                  A:554
       single-valued resolver facts → _session_entity_context (TTL 15 min)
    9. A::_remember_clarification (NEEDS_CLARIFICATION only; else POP pending)  A:424-458
       reads v4_state: loaded_skills / continuation_observations /
       continuation_required_skills → PendingClarification (A:32-40, store A:43)
       pops continuation_* from the public payload (internal-only)             A:444-446
       clarification_id = existing or uuid4()                                  A:431-433
UI (U): session_id = sessionStorage per tab (U:25-37); only the LATEST
NEEDS_CLARIFICATION result supplies pending (U:139-143); option click or free text
sends {query, session_id, clarification_id, clarification_option} (U:147-152).
Client can inject ONLY those 4 fields (QueryRequest, A:63-67).
```

**Which variables actually survive, per terminal status** (measured, P1):

| State | Typed NC from runtime (V4NeedsClarification) | Goal-guard NC (from COMPLETED) | COMPLETED | FAILED |
|---|---|---|---|---|
| original_query | ✓ pending store | ✓ pending store | ✗ | ✗ |
| loaded_skills | ✓ → `resume_loaded_skills` | ✓ → `resume_loaded_skills` (from COMPLETED v4_state) | → session entity context only (single-valued facts) | ✗ |
| observations (compact) | ✓ → `resume_observations` | ✗ **STRIPPED** (results popped; no continuation_observations supplied) | ✗ (public `data.results` only) | ✗ |
| required completion skills | ✓ → `required_completion_skills` | ✗ | ✗ | ✗ |
| full rows (`data.results`) | — (never set on NC) | ✗ STRIPPED | ✓ public | ✗ |
| session entity context | ✗ | ✗ (set only on COMPLETED) | ✓ TTL 15 min | ✗ |
| public payload `continuation_*` | ✓ present at emit, popped before send | n/a | n/a | n/a |

---

## 2. P1 — data-survival and security proof (offline, real production functions, zero LLM/source)

Probe scripts: `/private/tmp/qa229m22f/p1_replay.py`, `/private/tmp/qa229m22f/p1_part2.py` (untracked, outside repo). All replay rows use A229M1-real capability ids and argument/data shapes (`member.resolve` → `{reference, member_login, external_id, source: REAL_AS21, resolution_scope}`; `task.search` compact → `{count, filters, task_keys_sample[:20], task_key_count, source}`; `task.lookup` → `{task_key, task{…}, assignee_login, source: REAL_AS21}`).

### 2.1 Goal-guard data survival — M1/M2/M4/C5 (guard ON)

| Case | Query | Goals detected | Proven / Unproven | Guard result | `resume_observations` | `required_completion_skills` | `resume_loaded_skills` |
|---|---|---|---|---|---|---|---|
| M1 | «Задачи Калачанова в WMB и задачи Семавина в DMS» | 2× person_tasks | g1(K@WMB) / g2(S@DMS) | NC, results stripped, meta {2,[g1],[g2]} | **0** | **[]** | ✓ 1 skill |
| M2 | «Покажи задачу DMS-267 и её иерархию» | lookup + hierarchy | lookup / hierarchy | NC, meta {2,[g2],[g1]} | **0** | **[]** | ✓ |
| M4 | «Покажи задачу DMS-267, её иерархию и задачи Калачанова в WMB» | hierarchy + lookup + person_tasks | lookup / hierarchy, person | NC, meta {3,[g2],[g1,g3]} | **0** | **[]** | ✓ |
| C5 | «Покажи задачу DMS-267 и связанные с ней задачи» | lookup + relations | lookup / relations | NC, meta {2,[g1],[g2]} | **0** | **[]** | ✓ |

**Finding F-1 (the decisive one):** the goal guard converts COMPLETED→NEEDS_CLARIFICATION and strips `data.results`/`answer`/`evidence`, but supplies **no** `continuation_observations` and **no** `continuation_required_skills`. Therefore `_remember_clarification` (A:435-439) stores an **empty** observation set. The executed, source-proven goal's observations are **destroyed** — the follow-up turn re-plans from scratch (skill metadata only). This confirms the spec's warning: the stripped public payload is not being replaced by retained internal state. **No resume guarantee exists today for goal-guard continuations.** Proven-goal data (Kalachanov WMB 6 keys, DMS-267 lookup row) does not survive.

### 2.2 Control — the EXISTING typed-clarification path DOES carry state

Same `_remember_clarification` on a runtime `V4NeedsClarification` response: `resume_observations` = 1 (member.resolve, compact), `required_completion_skills` = [skill], loaded skills = [skill], and `continuation_observations` is **popped from the public payload** (leak flag = false). The mechanism works; it is simply not fed by the goal guard.

### 2.3 Runtime restoration seam (real `AgentCoreV4Runtime.process()`, stub planner/synthesizer/handlers)

| Probe | Setup (resume state) | Planner stub | Result | LLM turns | Source reads |
|---|---|---|---|---|---|
| B1 typed continuation | member.resolve carried + required=[skill] | CALL task.search{space=WMB} | **COMPLETED** runtime_contract; assignee auto-injected `Kalachanov.V.V` from carried obs | 1 | **1** (only the missing goal; member re-resolve = 0) |
| B2 goal-guard continuation AS-IS | observations dropped (current behavior) | CALL member.resolve → CALL task.search | COMPLETED runtime_contract | 2 | **2** (proven goal RE-EXECUTED: identity + collection re-read) |
| B3 counterfactual Option A | member.resolve + task.search carried + required=[skill] | READY | **COMPLETED** planner_ready | 1 | **0** — proven goal NOT re-read; frontier satisfied from carried obs |
| B4 carry, no pin | same carried obs, required=[] | READY | COMPLETED planner_ready | 1 | **0** — demonstrates stale-data exposure (contract satisfiable from 15-min-old carried facts) |
| B5 corrupted carried obs (count missing) | carried obs with contract key removed | READY ×8 | **FAILED** `v4_runtime_failure` (step budget) | 8 | 0 — fail-closed, no fabrication |

Key mechanics proven:
- Restored observations are trusted as-is (C:1156-1172) — **no source re-validation on resume**; freshness bounded only by the 15-min pending TTL.
- `covers_resolved_constraints` (F:163-177) accepts the **union** of all matching terminal observations' arguments — multiple collections in one resumed trajectory can each cover their own resolved identity (relevant to the M1 follow-up).
- Pinned `required_completion_skills` (F:304-337) keep the frontier fail-closed: a resumed trajectory cannot auto-complete unless carried or newly executed observations satisfy the contracts (B5 proves the negative).
- Compact observation data (C:1088-1108: `count` + 20-key sample) is sufficient for contract satisfaction, but **cannot re-render a large collection** beyond the 20-key sample without a fresh read.

### 2.4 Security probes

| # | Probe | Result | Assessment |
|---|---|---|---|
| S1 | Another client presents the victim's `session_id` + matching `clarification_id` | **Consumes the victim's pending state** (state keyed by client-chosen `session_id`, A:523/359) | CONTROL GAP. Bounded in practice: the API has no authentication at all (internal tool), the exposed data is AS21 facts already reachable by direct query under the same token, and the state is one-shot (destroyed on first consumption). No NEW data plane exposed; recorded as missing control, not a regression. |
| S2 | Wrong `clarification_id` | typed `clarification_context_lost` + pending **destroyed** (fail-safe) | ✓ |
| S3 | Invalid option (options non-empty) | typed `invalid_clarification_option`, state KEPT for retry | ✓ |
| S4 | TTL (15 min, monotonic) | typed `clarification_context_lost` | ✓ |
| S5 | 500 unique sessions, simulated +1 h | **500/500 entries still resident** — no background sweep; lazy reclaim only on access to the same key (all touch-points: A:43,130,356,361,376,426,447; `set_runtime` clear A:130 is a test hook) | Minor unbounded-growth risk; each entry bounded (S7) |
| S6 | Client-injectable request fields | exactly `query, session_id, clarification_id, clarification_option` | ✓ observations/loaded-skill state CANNOT be injected by the browser; server-side store is the only source (S1 is the sole bypass) |
| S7 | Pending entry size with 1 carried observation | **583 bytes** (compact obs ≈ 300-700 B each; observation count bounded by max_steps=8) | ✓ bounded per session |
| S8 | Process restart | in-memory dicts → typed `clarification_context_lost` on next follow-up (A:319-331) | ✓ no stale persistence |
| S9 | Concurrency, same session | dict ops serialized under GIL; worst case = one of two concurrent follow-ups gets `clarification_context_lost` (fail-safe) | ✓ no corruption |

### 2.5 Provenance / completeness / identity / REAL_EMPTY vs SOURCE_UNAVAILABLE

- Carried observations carry their original `source: REAL_AS21` markers and immutable resolved arguments; nothing in the resume path re-stamps or re-validates them (documented trade-off, B4).
- `source_unavailable` / `source_complete=False` observations are excluded from goal proof (G:169-171) and from contract satisfaction (F:92-101) — REAL_EMPTY (count=0 with complete source) is a legitimate completion; SOURCE_UNAVAILABLE never proves a goal. No blending observed.
- Canonical identity: `assignee` literals must be `$obs.` references (C:1040-1044) or deterministically injected from typed resolver observations (C:1278-1290) — a carried `member.resolve` observation binds the canonical login for the follow-up exactly as in-turn (B1/B3 `task_search_args` proven).

---

## 3. P2 — supported continuation options (no implementation)

### Option A — reuse existing `resume_observations` + pending clarification (recommended)
- **Exact seams (all measured):**
  1. `G::guard_completed_goal_coverage` (goal_coverage.py:187-222): on the unproven branch, BEFORE stripping `data.results`, compute compact `planner_view()` of the PROVEN terminal rows (+ their `member.resolve`/`space.resolve` support rows) and set `state["continuation_observations"]`; set `state["continuation_required_skills"]` = skill ids covering the UNPROVEN goals (small goal-kind→skill-id table: person_tasks→person-collection skill, task_hierarchy→hierarchy skill, task_relations→relations skill, task_lookup→lookup skill; ids must exist in the production registry).
  2. `A::_remember_clarification` (A:424-458) — **no change**: already captures both fields and pops them from the public payload (verified in the typed control).
  3. `A::_prepare_query` (A:344-391) — **no change**: already forwards them into `HarnessRequest`.
  4. `C::process` restoration (C:1148-1179) + frontier (F) — **no change**: B3 proves carried observations deterministically satisfy contracts with 0 source reads.
- **Executes missing goals:** yes — the follow-up planner sees carried observations in context and executes only the missing goal(s) through the normal governed CALL path (literal guards, $obs binding, arg completion all intact).
- **Avoid re-running proven goals / stale evidence:** PARTIAL. Contracts can be satisfied from carried observations (B3: 0 re-reads), but the planner is stochastic (A179 class) and MAY re-execute a proven goal — a re-read is safe (fresh data) but wasteful. A prompt-level mitigation is possible OUTSIDE Core: `_prepare_query`'s combined query (A:377-382) can carry a deterministic line «Уже подтверждено источником: <kind> (<args>) — не повторяй; выполни только недостающее» (API-layer text, no Core change; soft guarantee only). A hard anti-stale policy (carried obs never satisfy a terminal contract) WOULD require a Core change (mark restored observations as non-terminal) — out of scope.
- **Clarification for genuinely ambiguous missing goals:** existing typed `V4NeedsClarification` mechanism (options, continuation) — unchanged.
- **Budgets:** per-turn planner max_steps=8 (C:317); sequential; 429/timeout/connect stay FAILED (never promoted to clarification, A:254-261) — bounded, same as today.
- **Leakage/permissions:** none new — same governed read-only adapters, same token, no public exposure of carried state (popped before send).
- **Rollback flag:** new `PO_AGENT_V4_GOAL_CONTINUATION` (default false) gating only the state-supplying branch; the existing `PO_AGENT_V4_GOAL_COVERAGE_GUARD` stays as the NC gate.
- **Core files changed:** **ZERO** (1 API-layer file + settings + tests).
- **Detector FP risk:** a lexical false-positive goal would only ever ADD an unproven requirement → NC instead of COMPLETED (safe direction; cost = one follow-up). A false "proven" requires a real terminal row with matching capability+arguments (G:148-171), so it cannot be minted from prose. Mitigation: keep the detector conservative; `goal_coverage` meta already logged.

### Option B — bounded API-side orchestrator
- **Seams:** new `api/v1/multi_goal_orchestrator.py`; on COMPLETED+unproven, retain proven observations server-side (same store) and drive **per-goal sub-trajectories** through the SAME `bundle.v4_runtime.process(HarnessRequest(query=<goal-scoped query>, …))` — full planner governance per goal; merge terminal rows; re-run the goal guard over the merged response; COMPLETED only if all goals proven.
- **Executes missing goals:** yes, deterministically (each goal gets its own bounded trajectory).
- **Legality:** driving `process()` per goal = 100% within governance (contracts, literal guards, auth). Directly invoking `_handlers` for the missing goal is also legal (handlers are governed read-only adapters) but BYPASSES planner literal-validation and $obs binding — not recommended.
- **Avoid re-running proven goals:** structurally (sub-trajectories launched only for unproven goals).
- **Clarification:** a sub-trajectory's typed NC surfaces as the overall NC (forward options + continuation).
- **Budgets:** N sub-trajectories (cap ≤3), sequential, per-turn max_steps=8, 429 → typed FAILED; worst case ≈ N× current wall time.
- **Rollback flag:** new flag, default false. **Core changes:** zero.
- **Risks:** merged `data.results` shape must stay UI-contract-compatible (V4 panel expects one trajectory — merging needs care); 429 amplification; more moving parts than A. Strictly more capable (guarantees each missing goal is ATTEMPTED) — the right stage-2 vehicle if a completion guarantee is required.

### Option C — isolated sidecar execution orchestrator
- Separate process/service with its own planner loop, importing the governed capability registry and sharing task-api/MCP-SWTR. New deployment/auth/observability/test surface; governance can drift from Core (two planner stacks). Disproportionate for 2-3-goal queries at this stage. **Rejected for now.**

### Status semantics (explicit, per spec)
- `NEEDS_CLARIFICATION` — genuine ambiguity (typed runtime NC) AND stage-1 guard output for unproven multi-goal (conservative; the guard claims "not proven", not "ambiguous" — wording: «не удалось подтвердить… уточните, какую часть выполнить»).
- `PARTIAL` — exists in the enum (H:13) and is consumed by legacy runtimes (correction_runtime.py:89, semantic_correction_runtime_v2.py:58), but **V4 never emits it** (no code path sets `ResponseStatus.PARTIAL`). Synthesizing PARTIAL at the API layer is possible without Core changes, BUT `_remember_clarification` stores only NEEDS_CLARIFICATION (A:425-427 — any other status POPs pending) so PARTIAL would carry NO continuation, and the UI has no PARTIAL renderer. For unambiguous-but-unexecuted goals PARTIAL is semantically better than NC — deferred to stage 2 (API-synthesized + UI contract + staleness policy).
- `FAILED` — infrastructure/source/provider failure (kept distinct; provider markers never promoted, A:254-261).
- **No user clarification is requested for information that was already unambiguous merely because the planner skipped an action** — the goal guard fires only when a recognized, independently anchored goal lacks terminal evidence, and the follow-up re-plans the same original query (no new user data required beyond choosing what to do next).

---

## 4. P3 — counterfactual end-to-end replays (A229M1 traces)

Budgets from A229R1/A229R2R2 measurements: 1 LLM per planner turn; identity read ~0.3-4 s; scoped task-query ~1-35 s; hierarchy/relations (get_unit_links) ~0.2-1 s.

**Case 1 — M1 (Kalachanov WMB proven, Semavin DMS missing).**
T1 (as executed, single-terminal convergence): LOAD(1 LLM) → member.resolve K(1 LLM + 1 identity read) → task.search K@WMB(1 LLM + 1 scoped read) → READY(1 LLM) → COMPLETED → guard → NC. ≈4 LLM, 2 source reads. Retained (Option A): `[member.resolve(K), task.search(K,WMB)]` compact ≈1.0-1.3 KB + required=[person-collection skill] + original query.
T2: combined query + carried state → member.resolve S(1 LLM + 1 identity read) → task.search S@DMS(1 LLM + 1 scoped read) → frontier: both collections match the `task.search` requirement; `covers_resolved_constraints` union covers K and S identities (F:163-177) → COMPLETED. ≈2-3 LLM, 2 source reads. **Total: 6-7 LLM, 4 source reads** (vs B2-style re-run: 8-9 LLM, 6 reads). Fallback: planner derail → bounded repair → step budget → FAILED `v4_runtime_failure` → promoted to NC (planner markers, A:262-269) — never a false COMPLETED.

**Case 2 — M2 (lookup DMS-267 proven, hierarchy missing).**
T2: carried `[task.lookup DMS-267]` (compact keeps the full task row; description ≤384 chars via C:1079-1084) + required=[lookup skill, hierarchy skill] → task.hierarchy{task_key: DMS-267}(1 LLM + 1 get_unit_links read) → frontier satisfied → COMPLETED. ≈2-3 LLM, 1 source read. **Negative-claim safety:** the guard's NC text only lists the unproven kind; DMS-267's parent (source oracle: DMS-253 via decomposition, A229S1R2) can be asserted ONLY after the hierarchy rows exist — the carried lookup data contains no parent field, so a «без родителя» claim cannot leak.

**Case 3 — M4 (lookup proven; hierarchy + person missing).**
T2: carried `[task.lookup]` + required=[2 skills] → task.hierarchy(1 read) + member.resolve S(1 read) + task.search S@DMS(1 read) → union coverage → COMPLETED. ≈4-5 LLM, 3 source reads. Multi-skill pinning is supported by the frontier (pinned set, F:304-337) but deferred to the implementation gate (only single-skill carry proven in B3).

**Case 4 — C5 (lookup proven, link traversal missing).**
T2: carried `[task.lookup]` → task.relations{task_key}(1 LLM + 1 get_unit_links read) → COMPLETED. ≈3 LLM, 1 source read.

**Case 5 — M5 comparison («Сравни DMS и OLP»).**
`detect_goals` returns `()` on any `сравн…` (goal_coverage.py:103-104) → guard INERT → no continuation state. One analytical goal needing two source corpora; untyped in stage 1 → **OPEN** (comparison extractor). Design-only execution: 2 scoped corpus reads + 1 synthesis; requires its own typed goal kind before it can be guarded.

**Case 6 — C1/C3 composed-filter single-goal controls.**
«Открытые задачи Семавина с типом дефект в DMS за период» and «latest OLP sprint + Semavin + open + defect»: the collection regex requires person immediately before `в <SPACE>`; interposed filters break the match → 0-1 goals → guard INERT → normal single-trajectory completion (A229F3R: 42/42, 26/26 exact). **Never split.**

**Case 7 — ambiguous underspecified («покажи задачи и иерархию», no key).**
0 anchored goals → guard INERT → runtime typed NC («Какую задачу нужно открыть?») with the existing typed-continuation machinery. Clarification genuinely required — correct.

**Zero fabrication** across all cases: every merged/retained fact originates from a source-backed terminal row; the guard strips rather than rewrites; FAILED/NC taxonomy preserved.

---

## 5. P4 — feasibility answers and owner implementation plan

**Q1. Can the existing continuation carry validated observations across turns without Core changes and without duplicating source reads?**
**YES — proven.** The typed-clarification path already does (B1: 1 source read for the missing goal only); the SAME seam accepts goal observations when they are supplied (B3: 0 source reads). The only missing piece is state supply at the goal guard (1 API-layer function).

**Q2. Can it guarantee all missing goals are attempted/completed?**
**NO.** Completion remains per-skill, planner-driven, single-terminal-convergence-prone. The guard guarantees **no false COMPLETED** (fail-closed, B5); it cannot force execution. A per-goal attempt guarantee requires Option B (stage 2) or a Core multi-terminal completion change (out of scope).

**Q3. Can a plugin/API sidecar call the same governed capability registry safely?**
**YES**, by driving `v4_runtime.process()` per goal (Option B) — identical contracts/source/auth. Direct handler invocation is legal but bypasses planner literal-governance — avoid.

**Q4. Exact missing checks blocking implementation today:**
1. Goal guard does not supply `continuation_observations`/`continuation_required_skills` (the 3-line gap, F-1).
2. No per-goal identity in pending state (one pending record per session, one-shot; multi-goal needs a goal list + per-goal proven flag — extend `PendingClarification` or a sibling store).
3. Freshness policy for carried observations (15-min TTL only; no source re-validation; B4 shows contracts can complete from carried facts — acceptable for read-only analytics, must be a documented product decision).
4. Session ownership binding (client-chosen `session_id`; S1 impersonation possible; no auth service-wide).
5. No background sweep of expired pending entries (S5 unbounded lazy growth).
6. No typed goal extractor beyond the lexical pilot (comparisons, English, nested multi-goal, elided collections — OPEN).
7. No `PARTIAL` semantics for unambiguous-unexecuted (enum exists; V4 never emits; UI has no renderer; `_remember_clarification` would drop the state).
8. No anti-rerun hint for proven goals (soft prompt-line in the combined query is the out-of-Core mitigation).

**Q5. Smallest reversible out-of-Core change for M1+M2 first (PROPOSAL ONLY — not implemented):**
- `src/po_agent/api/v1/goal_coverage.py` — in `guard_completed_goal_coverage`'s unproven branch (before `data.pop("results")`): build compact `planner_view()` dicts from the PROVEN terminal rows + their resolver support rows; set `state["continuation_observations"]` and `state["continuation_required_skills"]` via a goal-kind→skill-id table (registry-validated ids). Public stripping unchanged.
- `src/po_agent/config/settings.py` — `v4_goal_continuation_enabled: bool = Field(default=False, …)` (env `PO_AGENT_V4_GOAL_CONTINUATION`).
- `src/po_agent/api/v1/__init__.py` — NO change (seams verified as-is); optional combined-query anti-rerun line (soft) behind the same flag.
- `tests/test_v4_goal_coverage.py` — non-mocked: (a) goal-guard NC now supplies `continuation_observations` with proven rows (M1/M2 shapes); (b) full chain guard → `_remember_clarification` → `_prepare_query` → `AgentCoreV4Runtime.process` (stub LLM/handlers) → COMPLETED with 0 re-reads of the proven goal (B3 shape); (c) corrupted/absent carried observation fails closed (B5 shape); (d) flag OFF → byte-identical to A229M2.1R behavior; (e) no public leakage of `continuation_observations`.
- **Live re-gate spec (owner implementation gate):** A/B oracle (pre-fix HEAD vs fix on the same queries), browser (goal-guard NC → free-text continuation → merged result), restart (context lost → typed), recovery (source 502 mid-continuation → FAILED; carried observations not reused as success), privacy (0 new public fields), concurrency (2 sessions), regression (A229F3R gates + A229M2.1R matrix + 282 V4 blast), **0 false completed, 0 unauthorized mutations**.
- **Deferred (not in stage 1):** M4 multi-skill pinning, C5 relations, M5 comparison, PARTIAL status, per-goal ids, session ownership, background sweep, typed extractor.

### Recommendation
`REUSE_CLARIFICATION_CONTINUATION` — the state-carrying seam is measured end-to-end at the state-machine level (guard → remember → prepare → process restoration → completion frontier → COMPLETED / fail-closed, zero Core changes, zero fabrication), risks are explicit, and one valid, reversible, out-of-Core implementation boundary is specified (goal_coverage.py state supply + default-false flag). The owner implementation gate must re-prove it LIVE (A/B oracle + browser + recovery) before the flag is ever enabled.

---

## 6. P5 — verdict and residual risks

**Verdict: `AGENT_CORE_V4_SAFE_CONTINUATION_FEASIBILITY_GREEN_A229M22F`** — architecture seams measured (all line-located), alternatives compared (A/B/C), risks explicit, one valid implementation boundary specified. This does NOT certify working multi-intent continuation.

**Residual OPEN risks / gaps (non-blocking for this design gate):**
1. Planner stochasticity on follow-up turns (A179/A227R2 class) — bounded repair fails closed; continuation can still end in FAILED/NC instead of COMPLETED.
2. Stale carried observations (15-min TTL, no re-validation; B4) — product decision required for analytics freshness.
3. Session impersonation (S1) + no background sweep (S5) — pre-existing control gaps, bounded.
4. Lexical goal detector is a conservative pilot: comparisons/English/nested/elided-collection intents are OPEN; unrecognized multi-goal is never reinterpreted as certified success (guard inert → single-trajectory semantics).
5. Compact carried data (20-key sample) cannot re-render large collections; re-rendering requires a fresh read.
6. Multi-skill (M4) and relations (C5) continuation paths are designed but not yet proven live — deferred to the implementation gate.
7. `PARTIAL` semantics for unambiguous-unexecuted goals deferred (UI + state-decay policy needed).

**TESTED_HEAD:** `a54a685356274834589e301c85e027e62ca169fe`
**Core hashes:** 52100ca1 / 3bdb4d09 / 1f7562dc / cf75a6d6 / d82929d1 / 1cc10e12 (all = frozen `6fb335d`)
**Exact suite counts:** focused 47/47; V4 blast 282/282; config 46/46; Task API canonical SWTR 16/16; frontend build exit 0; 1 pre-existing stale integration failure (documented, not delta-caused).
**Evidence state-survival table:** §1 (per-status) + §2.1 (per-case M1/M2/M4/C5).
**Recommended option:** `REUSE_CLARIFICATION_CONTINUATION` (§5).
**Owner next action (exact):** implement the §5 Q5 spec (goal_coverage.py state supply + `PO_AGENT_V4_GOAL_CONTINUATION` default-false flag + 5 named tests), then run the live re-gate spec. Do NOT enable either V4 flag on the real stack until the re-gate is GREEN.
**No production code edits, no flag flips, no new checkpoint.**
