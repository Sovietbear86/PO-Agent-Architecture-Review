# A229M1 — Multi-Intent Goal Coverage: Architecture & Feasibility Gate (DESIGN ONLY)

**Verdict:** `AGENT_CORE_V4_MULTI_INTENT_DESIGN_GREEN_A229M1`
**Role:** QA / architecture investigator only. No production/test/config modifications. No implementation. No flag flip. No new production checkpoint.
**DESIGN GREEN ≠ multi-intent functionality GREEN.**

- **TESTED_HEAD / START_HEAD:** `9a0477279ae4ed72a70c9f00d092a5a4ff42c7e6` (branch `feat/core8-real-query-hardening-v2`, in sync with origin)
- **Frozen Core checkpoint compared:** `6fb335d6f67344245a5c65e5c1b5b145759e96da`
- **Date:** 2026-10-14
- **Services (read-only):** agent 8004 @ 9a04772 (flag `PO_AGENT_V4_SYNTHESIS_ELISION=false`, production default), task-api 8241, MCP-SWTR 3000.
- **Source:** REAL AS21, governed skill/capability/evidence plane, read-only.

---

## P0 — Safety, evidence and regression baseline (GREEN)

| Check | Result |
|---|---|
| Core 6/6 byte-identical to `6fb335d` | **PASS** — empty `git diff` on `agent_core_v4.py`, `agent_core_v4_robust.py`, `agent_core_v4_reliable.py`, `agent_core_v4_completion.py`, `v4_plugin_registry.py`, `llm/real.py` |
| Full V4 suite | **270/270 PASS** |
| Task API SWTR suite | **34/34 PASS** |
| Frontend `npm run build` | **exit 0** |
| Plugin registry | 13 plugins / 72 skills / 74 capabilities / 69 ui_contracts |
| Feature flag | `PO_AGENT_V4_SYNTHESIS_ELISION=false` — NOT flipped; entire P1 matrix ran flag-OFF (all `elided=False`) |

**Seam map (file:line, existing; preferred path touches none of Core):**
- Completion is per-skill, single-goal: `harness/agent_core_v4_completion.py` — `completion_frontier_skills` / `completion_frontier_satisfied` / `is_skill_satisfied` certify only structurally-active loaded skill(s). `CompletionRequirement{capability_id, data_keys, data_absent_keys, bound_argument, covers_resolved_constraints}`; `_CONSTRAINT_RESOLVERS` = member.resolve→assignee/member_login, space.resolve→space, sprint.resolve/search/current→sprint_id, release.resolve→release_id.
- Postcondition guard seam (Option B anchor): `api/v1/__init__.py:184` `_guard_completed_constraint_coverage(response, original_query)` (A229F3R pattern: COMPLETED + dropped user constraint → typed NEEDS_CLARIFICATION, results stripped, warning `v4_constraint_coverage_clarification`) + `_promote_planner_failure_to_clarification`.
- Continuation seam: `api/v1/__init__.py` `_prepare_query` (~:345) restores `original_query` + `resume_loaded_skills` + `resume_observations` + `required_completion_skills`; `_remember_clarification` stores `PendingClarification` in `_pending_clarifications[session_id]` (TTL `_CLARIFICATION_TTL_SECONDS`).
- Response shapes: `harness/contracts.py:10` `ResponseStatus{COMPLETED, NEEDS_CLARIFICATION, PARTIAL, FAILED}` — `PARTIAL` defined but **unused in V4**.
- Observation shape: `V4Observation{step, capability_id, arguments, answer, data}` (`agent_core_v4.py:166`); `_completed_response` (`:633`) builds `data._agent_core_v4{runtime, completion, trajectory, loaded_skills, observation_count, ...}` + `data.results[]`.
- Frontend already supports PARTIAL (zero UI change): `frontend/src/api/client.ts:15` includes `'PARTIAL'`; `recovery/WorkspaceApp.tsx:224` renders result panel for `['COMPLETED','PARTIAL']`; `recovery/resultState.ts:142` PARTIAL→`SOURCE_CONDITIONAL`, `stateAllowsBusinessData(PARTIAL)=false` (answer text shown, no business cards). NEEDS_CLARIFICATION renders option buttons + continuation (`WorkspaceApp.tsx:217`).

---

## P1 — Goal semantics, oracles, live matrix (42 runs + 11 detail probes)

Fresh sessions, flag OFF, 3 runs/case (plus detail probes with full terminal args/results). Independent REAL AS21 oracles per goal via task-api :8241 (read-only) + MCP-direct. `и/AND` used as coordination signal only — never as a splitter (P4, R1).

### Oracles (2026-10-14, REAL AS21)

| Oracle | Value |
|---|---|
| Kalachanov WMB | total **6** [WMB-29242, 29830, 29890, 29995, 30000, 30482]; open [WMB-30482] |
| Semavin DMS | total 173; open [DMS-455, DMS-431, DMS-458]; open-bug [DMS-431] |
| DMS-267 | "[mcp] Аутентификация по сертификатам", Resolved/done, Semavin.M.M, suit=task. **Links: total 1 — DMS-253→DMS-267 (type=decomposition, not deleted) → parent DMS-253 PROVEN** |
| DMS open | 67 → drifted to **66** mid-session (live source); space total 494 |
| OLP open | **314**; space total 3337 |
| C1 (Semavin DMS open-bug last 2 days, window 10-13T00:00→10-14T18:03 MSK) | **0** REAL_EMPTY (DMS-431 older than 2d) |
| C2 (Kalachanov WMB with attachments) | **3** [WMB-30000×5, WMB-29890×1, WMB-29995×10], all terminal |
| C3s (Semavin OPEN BUGS in OLP-SPRNT-9) | sprint total **88** (87 at 18:03, +1 drift), Semavin tasks **23**, Semavin bugs 17 (all Resolved/done) → **open bugs = 0 REAL_EMPTY** |
| C4 (Kalachanov WMB in-progress ∩ attachments) | **0** REAL_EMPTY (only open WMB task WMB-30482 has no attachments) |
| C6s (DMS vs OLP current sprints) | DMS-SPRNT-4 **40/19 done/21 open**; OLP-SPRNT-9 **88/47/41** (complete=true verified) |

**QA oracle correction (transparency):** my first C3 oracle filtered sprint rows by a top-level `assignee_login` field that does not exist — sprint rows carry the assignee under `source_data.swtr_attributes[].code=assigned_to → value.externalId`. Corrected: Semavin has **exactly 23** tasks in OLP-SPRNT-9; the agent's "23" in C3-plain runs is **exact** (no misattribution).

### Live matrix — requested goals vs proven terminal observations

| Case (query) | Immutable goal set | Terminal(s) executed (all runs) | Coverage | Answer safety | Status |
|---|---|---|---|---|---|
| **M1** «Покажи задачи Калачанова в WMB и задачи Семавина в DMS» (4 runs) | g1: Kalachanov/WMB tasks; g2: Semavin/DMS tasks | `task.search_assignee{Калачанов, WMB}` (4/4) | g1 **PROVEN 6/6 exact**; g2 **UNPROVEN** (0 calls) | **honest flag 4/4** ("данные по этому запросу отсутствуют — результат не получен"); 0 false claims | `COMPLETED` — **silent goal drop** |
| **M2** «Покажи задачу DMS-267 и её иерархию» (4 runs) | g1: DMS-267 lookup; g2: DMS-267 hierarchy | `task.lookup{DMS-267}` (4/4) | g1 PROVEN; g2 **UNPROVEN** (no `task.hierarchy`) | **FALSE NEGATION 2/4** ("Задача не имеет иерархии: Родительская задача: — … самостоятельной задачей") vs source-truth parent DMS-253; honest 2/4 | `COMPLETED` |
| **M3** «Покажи задачи Калачанова в WMB и иерархию DMS-267» (4 runs) | g1: Kalachanov/WMB; g2: DMS-267 hierarchy | `task.search_assignee{Калачанов, WMB}` (4/4) | g1 PROVEN 6/6; g2 UNPROVEN | **honest 4/4** ("в предоставленных наблюдениях отсутствует") | `COMPLETED` — silent drop |
| **M4** «Покажи задачу DMS-267, её иерархию и задачи Калачанова в WMB» (4 runs) | g1: lookup; g2: hierarchy; g3: Kalachanov | `task.lookup{DMS-267}` (4/4) | g1 PROVEN; g2, g3 UNPROVEN | **FALSE NEGATION 3/4** on hierarchy ("не имеет родителя… автономная задача"); honest 3/4 on g3 ("необходим отдельный запрос") | `COMPLETED` — 2 silent drops |
| **M5s** «Сравни незавершённые задачи в DMS и OLP» (3 runs) | g1: compare open counts DMS vs OLP — ONE goal requiring **two** evidences | `task.search{space=DMS, status=not_completed}` (3/3) → 66 exact | g1 **PARTIAL** (1 of 2 required evidences) | **honest 3/3** ("данные по OLP не получены… сравнение провести невозможно"); 0 fabrication | `COMPLETED` |
| **M5p** «Покажи открытые задачи DMS и открытые задачи OLP» (4 runs) | g1: DMS open; g2: OLP open | non-deterministic: short `task.search_status{DMS}` (1/4) vs full `space.resolve×2 + task.search{DMS} + task.search{OLP}` (3/4 → **67/314 exact**) | short: g2 UNPROVEN; full: both PROVEN | short: honest "OLP — данные… не получены"; full: exact | `COMPLETED` both variants |
| **C1** «Открытые задачи Семавина с типом дефект в DMS за последние 2 дня» (3 runs) | ONE composed goal (5 filters) | none (0 terminals) | not executed | typed free-text clarification, 0 data | `NEEDS_CLARIFICATION` (safe; oracle could have answered 0 — conservative) |
| **C2** «Задачи Калачанова в WMB с вложениями» (4 runs) | ONE goal (person+space+attachments) | `member.resolve` + `task.search_attachments{Калачанов, WMB}` | **PROVEN 3/3 exact** (3 tasks) | exact | `COMPLETED` |
| **C3s** «Покажи открытые дефекты Семавина в последнем спринте OLP» (3 runs) | ONE goal (open+bug+person+sprint) | 1/3: `space.resolve + sprint.current + task.type_analysis{defect, Семавин, OLP, open, OLP-SPRNT-9}` → **0 = oracle REAL_EMPTY exact**; 2/3: planner misparsed «последнем» as an unrecognized period → typed clarification | proven / safe-clarify | 0 false data | `COMPLETED` / `NEEDS_CLARIFICATION` |
| **C3p** «Задачи Семавина в текущем спринте OLP» (4 runs, extra) | ONE goal | `space.resolve + member.resolve + sprint.current + task.search{Semavin.M.M, OLP-SPRNT-9, OLP}` → **23/23 exact** | PROVEN | exact | `COMPLETED` |
| **C4** «Задачи Калачанова в WMB в работе с вложениями» (4 runs) | ONE intersected goal | `member.resolve + task.search_attachments{status=in_progress}` → **0 = oracle REAL_EMPTY exact** | PROVEN | "нет задач" correct | `COMPLETED` |
| **C5** «Покажи задачу DMS-267 и связанные с ней задачи» (4 runs) | g1: lookup; g2: related tasks | `task.lookup{DMS-267}` (4/4) | g1 PROVEN; g2 **UNPROVEN** (no hierarchy/links call) | **FALSE NEGATION 3/4** ("Связанных задач не найдено: поле `related_keys` пусто") vs source-truth 1 decomposition link (DMS-253) | `COMPLETED` — silent drop |
| **C6s** «Сравни DMS и OLP» (3 runs) | ONE comparison goal (metric underspecified) | `portfolio.overview` (no args; natively spans all spaces) → DMS-SPRNT-4 40/19/21, OLP-SPRNT-9 88/47/41 — **core numbers exact vs source** | **PROVEN** (one terminal covers both entities by capability design) | sensible default metrics, no fabrication | `COMPLETED` |
| **C6p** «Покажи задачи ОЛЬГИ Ивановой в DMS» (3 runs, extra: invented person) | ONE goal (person unresolvable) | none | — | typed clarification "Не удалось однозначно определить пользователя" | `NEEDS_CLARIFICATION` (safe) |

**No false-positive splits:** C1–C4 composed-filter queries were treated as ONE goal in 100% of runs (no fragment executed as an independent deliverable).

---

## P2 — First-failing-boundary analysis

Per-goal loss map (where and why each goal is lost):

| Boundary | Location | Determinism | Evidence |
|---|---|---|---|
| **B1 — single-goal completion contract (STRUCTURAL)** | `harness/agent_core_v4_completion.py` (Core): `completion_frontier_*`/`is_skill_satisfied` see only the structurally-active loaded skill; planner (`agent_core_v4.py`/`_robust`) plans one goal per trajectory and converges to one terminal | **100% deterministic** | M1–M4, C5: always `nterm=1` + `COMPLETED runtime_contract` with 1–2 unproven goals; READY rationale "deterministic skill completion contract satisfied" with one terminal |
| **B2 — synthesis honesty on negatable goals (NON-DETERMINISTIC)** | `ResponseSynthesizerV4.synthesize` (Core, post-execution): converts null hierarchy/related fields in a lookup-only observation into confident source negations | non-deterministic, **8/12** hierarchy/related runs assert false absence (M2 2/4, M4 3/4, C5 3/4) | "Родительская задача: —", "Задача не имеет иерархии", "Связанных задач не найдено: поле `related_keys` пусто" — all contradict source-truth (DMS-253 decomposition link). Non-negatable goals (task collections) → honest gap flags (M1 4/4, M3 4/4, M5p-short, M5s 3/3) |
| **B3 — presentation: no per-goal status channel (STRUCTURAL)** | `api/v1/__init__.py` + `data._agent_core_v4`: single `status` + single `answer`; no per-goal proven/unproven surface; frontend cannot render partial coverage | deterministic | M1–M4 all `COMPLETED` with mixed coverage; `PARTIAL` enum exists but is never emitted by V4 |

**DMS-267 parent mismatch — explicitly reproduced (spec requirement):**
- `task.lookup{DMS-267}` observation contains **no** link/hierarchy fields → hierarchy data is null.
- Source oracle (get_unit_links, REAL AS21): exactly **1 link, DMS-253→DMS-267, type=decomposition, not deleted** → parent DMS-253 exists.
- 8/8 lookup-only runs (M2×4, M4×4) + 3/4 C5 runs rendered a user-visible **false claim** of absent parent/hierarchy/relations. `task.lookup` does NOT prove absent hierarchy; only `task.hierarchy` / link source does.
- **Verifier requirement derived:** before a response becomes user-visible, any negatable assertion about an attribute whose goal is unproven must be blocked/replaced. A coverage verifier keyed on (uncovered goal kind ∈ {hierarchy, relations}) + (answer contains negation markers for that attribute) catches all 8 observed false claims; the principled form is "uncovered negatable goal ⇒ response must not contain absence-claims for that attribute" (P4 rule R4).

**Where goals are lost:** discovery — all needed skills exist and are loadable (task.hierarchy, task.search, portfolio.overview in catalog); planner — plans only the first goal (Core); execution — single terminal (Core planner); completion — certifies the single terminal (Core contract); synthesis — may fabricate negations (Core, LLM); API presentation — no per-goal surface (B3). **No goal is lost to source, permissions, or the plugin plane** — the boundary is entirely in Core planning/completion + presentation absence.

---

## P3 — Three solution options (design only, no implementation)

### Option A — Plugin/capability-side composition (dedicated multi-goal procedural skill)
- **Idea:** add governed skills in the trusted `po_agent.harness.v4_plugins` namespace whose procedures instruct the planner to call several capabilities sequentially (e.g., `task.compare_spaces` → `task.search{DMS}` + `task.search{OLP}`; `task.lookup_with_hierarchy` → `task.lookup` + `task.hierarchy`).
- **What current Core CAN certify:** a fixed-N capability set with one `CompletionRequirement` per capability (tuple `completion`) — a skill with 2 fixed requirements completes only when BOTH are satisfied. Deterministic, no LLM completion.
- **What it CANNOT certify:** an *arbitrary* user goal set. A skill's requirement tuple is static; "Kalachanov WMB + Semavin DMS" vs "DMS-267 + hierarchy" vs "3 goals" would need a combinatorial explosion of skills, and the planner must route the right phrase to the right skill (LLM routing fragility, A217/F2 lineage). Completion cannot distinguish "user asked for 1 of the 2 fixed requirements" (over-requirement → forced extra calls on single-goal queries).
- **Core touch:** none (plugin-only). **Cost:** +1–2 LLM planner turns per extra capability. **Rollback:** remove plugin file. **54 canonical skills impact:** additive only. **Counterexample:** M1/M3/M4/C5 shapes are not coverable by a bounded fixed-N skill set without phrase routing.
- **Verdict:** sound for **fixed comparison patterns only** (and C6s proves `portfolio.overview` already covers cross-space comparison natively). **Not a general solution.**

### Option B — Typed API/dialogue goal-coverage guard (RECOMMENDED)
- **Anchor:** the existing postcondition chain in `api/v1/__init__.py` — `_guard_completed_constraint_coverage` (A229F3R) already proves the pattern: after Core returns COMPLETED, a deterministic checker inspects (original query, executed capabilities/arguments) and converts unsafe COMPLETED → typed NEEDS_CLARIFICATION with results stripped + warning code. Generalize it from "one dropped constraint" to "N requested goals vs N terminal observations".
- **Components (all outside Core, additive):**
  1. `api/v1/goal_coverage.py` — pure functions: `detect_goals(query, trajectory) -> tuple[RequestGoal]` (typed extractor, P4 R1), `check_goal_coverage(observations, goals) -> GoalCoverage` (bound-argument matching, reusing `_CONSTRAINT_RESOLVERS` semantics), `repair_answer(answer, coverage)` (blocks false negatable claims, R4).
  2. Wire in `api/v1/__init__.py` postcondition chain: COMPLETED + non-empty `coverage.unproven` → **NEEDS_CLARIFICATION** with typed question ("Выполнено: <covered>. Не выполнено: <uncovered> — отправить отдельный запрос?"), one **option per uncovered goal** (canonical rephrase), stored via `_remember_clarification` (existing `PendingClarification` + `resume_loaded_skills/resume_observations/required_completion_skills`) → continuation turn re-runs only the uncovered goal, reusing proven session state.
  3. Optional second response mode **PARTIAL** (enum exists; frontend renders it): covered data + uncovered list. v1 keeps NEEDS_CLARIFICATION as default (drives completion via one-click continuation; PARTIAL hides business cards — weaker when half the answer is real data).
- **Safety:** fail-closed (uncovered ⇒ never COMPLETED); the guard only *detects* incomplete coverage — it never infers or executes missing facts; no cross-goal evidence reuse (R2); stale/partial guards (R5/R6).
- **Core touch:** **NONE** (Core 6/6 byte-identical at re-gate). **Cost:** 0 extra LLM calls on turn 1 (guard is deterministic, post-response); continuation adds one normal V4 trajectory for the uncovered goal only. **Rollback:** one flag `PO_AGENT_V4_GOAL_COVERAGE_GUARD` (default OFF). **54 canonical skills impact:** none (presentation/API plane only; no skill/capability/registry change). **Counterexamples handled:** C1–C4 single-goal pass untouched; C6s single comparison goal PROVEN by `portfolio.overview` (both entities in one terminal) — the extractor must classify "сравни X и Y" as ONE comparison goal when a covering capability exists, not two goals.

### Option C — V5 deep-orchestration sidecar (GVS5H-inspired)
- **Idea:** a new orchestration plane that decomposes the request, runs each goal as an independent governed V4 trajectory (same skills/evidence/read-only source), and merges per-goal statuses (true multi-terminal, native PARTIAL, per-goal evidence isolation).
- **Cost:** N× planner turns, new plane + lifecycle, new failure modes; 429/latency multiplier.
- **Role:** correct home for **genuinely independent analytical workloads** (cross-space metric comparisons, portfolio analytics) — NOT required for the basic multi-intent fix.
- **Verdict:** V5 roadmap item; overkill as the minimal path.

**Selection: Option B.** It closes B1 (structural silent drop → typed incomplete), B2 (false negations → answer repair), and B3 (no per-goal surface → typed continuation options) with zero Core changes, zero extra LLM calls on turn 1, existing frontend support, and a one-flag rollback.

---

## P4 — Typed goal contract (PROPOSED SCHEMA — report only, not production code)

```python
# proposed: po_agent/api/v1/goal_coverage.py  (NOT implemented in A229M1)

GoalKind = Literal[
    "person_tasks", "status_collection", "task_lookup", "task_hierarchy",
    "task_relations", "task_attachments", "sprint_collection",
    "type_analysis", "comparison", "other",
]

@dataclass(frozen=True)
class RequestGoal:
    goal_id: str                    # "g1", "g2"… assigned in order of appearance
    span: tuple[int, int]           # char offsets in original_query (source text span)
    kind: GoalKind
    constraints: dict               # typed: person / space / task_key / status /
                                    # created_period / sprint / release / type / attachments
    dependencies: tuple[str, ...]   # goal_ids that must be proven first (e.g. hierarchy after lookup)
    required_evidence: int = 1      # comparison goals require 2+ (one per entity side)
    negatable: bool                 # True for hierarchy/relations kinds (B2 class)

@dataclass(frozen=True)
class GoalEvidence:
    goal_id: str
    capability_id: str              # terminal capability that proved it
    terminal_args: dict
    result_ref: str                 # "results[<step>]" reference into data.results
    source_status: str              # REAL_AS21 / REAL_EMPTY / SOURCE_UNAVAILABLE / ...

@dataclass(frozen=True)
class GoalCoverage:
    goals: tuple[RequestGoal, ...]
    proven: tuple[str, ...]
    unproven: tuple[str, ...]
    ambiguous: tuple[str, ...]      # extractor could not type the fragment → safe clarify
    status: Literal["ALL_PROVEN", "INCOMPLETE_SAFE_CLARIFY", "UNSUPPORTED",
                     "SOURCE_OUTAGE", "PROVIDER_OUTAGE"]
    evidence: dict                  # goal_id -> GoalEvidence
    answer_repairs: tuple[str, ...] # warning codes applied by repair_answer

@dataclass(frozen=True)
class ContinuationState:
    session_id: str
    original_query: str
    pending_goal_ids: tuple[str, ...]
    prior_evidence: tuple[GoalEvidence, ...]   # proven facts carried, NOT re-fetched
    retry_budget: int = 1                     # bounded: one continuation per goal set
```

**Binding & safety rules (deterministic, no LLM):**
- **R1 — goal typing, not conjunction splitting:** a fragment is a separate goal only if it carries an *independent entity/constraint anchor* (a second person, a second space, an explicit task_key, or a distinct deliverable verb/object: «и её иерархию», «и задачи <person>»). Filters attaching to the nearest anchor (status/type/period/attachments/sprint) belong to THAT goal. «Задачи Калачанова в WMB в работе с вложениями» = 1 goal; «Сравни X и Y» = 1 `comparison` goal when a spanning capability exists (C6s), else 1 goal with `required_evidence=2` (M5s). Conjunction alone never splits.
- **R2 — no cross-goal evidence reuse:** goal g is PROVEN only by a terminal observation whose `terminal_args` contain ALL of g's constraints (bound-argument match, `_CONSTRAINT_RESOLVERS` semantics). `task.search{assignee=Semavin, space=OLP}` cannot prove goal «Kalachanov WMB»; a resolver observation (space.resolve) proves no user goal by itself.
- **R3 — provenance:** every GoalEvidence cites `result_ref` + `source_status`; a goal is never proven by model text.
- **R4 — claim repair (anti-false-negation):** if g ∈ unproven and `g.negatable`, the response must not contain absence-claims for g's attribute (observed markers: «не имеет иерархии/родителя», «связанных задач не найдено», «поле … пусто», «автономная задача», «Родительская задача: —» in the section about g's entity). `repair_answer` replaces such sections with the typed «данные не получены — отправить отдельный запрос?» note + warning code `v4_goal_claim_repaired`. This is the verifier that prevents the DMS-267 false-parent claim before the user sees it.
- **R5 — stale guard:** continuation reuses `prior_evidence` as-of its observation timestamp; covered goals are NOT silently re-fetched; if the follow-up changes a constraint, stale evidence for the changed constraint is dropped.
- **R6 — partial source failure:** if the uncovered goal's re-run hits source 5xx → `SOURCE_OUTAGE` (typed FAILED, prior proven data kept labeled as-of ts); LLM 429/timeout → `PROVIDER_OUTAGE` (existing taxonomy). Never fabricate to fill.
- **Statuses:** `ALL_PROVEN` (stay COMPLETED); `INCOMPLETE_SAFE_CLARIFY` (→ NEEDS_CLARIFICATION + options; PARTIAL in v2); `UNSUPPORTED` (no covering capability → typed clarification, e.g. invented person C6p); `SOURCE_OUTAGE`; `PROVIDER_OUTAGE`. All map onto CURRENT API enums (COMPLETED / NEEDS_CLARIFICATION / FAILED); PARTIAL reserved for v2 — no new wire enum in v1.

**Counterfactual verification on captured traces (no production logic executed):**

| Case | detect_goals | coverage | guard action (counterfactual) |
|---|---|---|---|
| M1 | g1 person_tasks{Kalachanov,WMB}, g2 person_tasks{Semavin,DMS} | g1 PROVEN (terminal args match); g2 UNPROVEN | **FLAG** → clarify «отправить: «Задачи Семавина в DMS»?» |
| M2 | g1 task_lookup{DMS-267}, g2 task_hierarchy{DMS-267} (negatable) | g1 PROVEN; g2 UNPROVEN | **FLAG** + R4 repair of «не имеет иерархии» section |
| M3 | g1 person_tasks{Kalachanov,WMB}, g2 task_hierarchy{DMS-267} | g1 PROVEN; g2 UNPROVEN | **FLAG** (answer already honest — repair is a no-op) |
| M4 | g1 lookup, g2 hierarchy, g3 person_tasks | g1 PROVEN; g2, g3 UNPROVEN | **FLAG** + R4 repair + 2 options |
| M5s | g1 comparison{DMS,OLP,status=open}, required_evidence=2 | 1 of 2 evidences | **FLAG** (goal PARTIAL — not "one of two goals") |
| M5p | g1 status_collection{DMS,open}, g2 status_collection{OLP,open} | short variant: g2 UNPROVEN; full variant: both PROVEN (67/314 exact) | short **FLAG**; full **stay COMPLETED** |
| C1 | 1 composed goal | already NEEDS_CLARIFICATION | pass-through (guard no-ops on non-COMPLETED) |
| C2 / C3p / C3s(1/3) / C4 | 1 goal each | PROVEN, args match, exact/REAL_EMPTY oracles | **stay COMPLETED** — no false positive |
| C5 | g1 lookup, g2 task_relations (negatable) | g2 UNPROVEN | **FLAG** + R4 repair of «связанных задач не найдено» |
| C6s | 1 comparison goal (spanning capability portfolio.overview) | PROVEN (one terminal covers both entities) | **stay COMPLETED** — no false-positive split |

---

## P5 — Recommendation & minimal owner path

**Recommendation: Option B** — typed goal-coverage guard in the API/dialogue plane. Core planning/completion stays frozen; the guard makes the *presentation* honest (no silent drop, no false negation) and gives a one-click typed continuation for uncovered goals. If full multi-terminal execution is later required (independent analytics), that is Option C's V5 scope — not this path. Under the existing interfaces, multi-terminal *execution* is not reachable without Core (planner plans one goal; completion certifies one skill) — the precise boundary is B1; Option B is the safe outside-Core completion of "honest partial/clarification", exactly the spec's fallback clause.

**Stages (owner implementation, all outside Core):**
1. **Typed goal extraction + evidence mapping** — new `api/v1/goal_coverage.py`: `detect_goals` (R1) + `check_goal_coverage` (R2/R3). Unit corpus: the 11 A229M1 cases — expected goal counts M1=2, M2=2, M3=2, M4=3, M5s=1 (req. 2 evidences), M5p=2, C1=1, C2=1, C3s=1, C3p=1, C4=1, C5=2, C6s=1, C6p=1; zero splits on C1–C4.
2. **Postcondition coverage fail-closed** — wire `check_goal_coverage` + `repair_answer` (R4) into the existing `_guard_completed_constraint_coverage` chain behind flag `PO_AGENT_V4_GOAL_COVERAGE_GUARD` (default OFF). Replay the exact captured M1–M5/C5 payloads (matrix.json) through the guard offline: all flagged, C1–C4/C6s unflagged; 8/8 false-negation answers repaired.
3. **Safe continuation** — uncovered-goal options via `_remember_clarification` (existing `PendingClarification` + resume state); continuation re-runs ONLY the uncovered goal (bounded `retry_budget=1`), R5 stale guard, R6 outage typing.
4. **Non-regression / UI / REAL AS21 A/B oracle gate** — live re-gate M1–M5, C5 (3/3 each: turn 1 covered data + typed clarification; turn 2 option-click → uncovered goal executed, combined coverage exact vs fresh oracle); C1–C4 + C6s unchanged; Browser C check that clarification options render and continue in-session; audit 0 local reads / 0 mutations / 0 unscoped scans / 0 extra turn-1 LLM calls.

**Regression acceptance (explicit):**
- 100% coverage OR honest partial/clarification — **never a silent goal drop** (M1–M5, C5: 3/3 flagged or fully covered);
- **no false-positive goal splits** for composed-filter single-goal queries (C1–C4, C6s stay COMPLETED/clarify as today);
- **DMS-267 can never claim parent/relations absent** without hierarchy evidence (R4; re-verify against the 1-link DMS-253 source-truth);
- no local fallback reads, no tenant scans, no writes, no invented data;
- ≤ 0 extra LLM calls on turn 1; feature default OFF; single-flag rollback; **Core 6/6 byte-identical** at re-gate.

**Minimal next owner task (single, bounded):** implement Stage 1+2 only (detector + guard + offline replay of the A229M1 matrix) behind the OFF flag, with the unit corpus above; then request A229M2 for Stages 3+4 (continuation + live re-gate).

---

## Audit & environment notes

- **Audit (session-wide, agent 8004 log + task-api):** 0 local `/api/v1/tasks` reads; 0 mutations (all task-api traffic GET read-only); 0 tenant-wide unscoped scans (every read space-scoped, sprint-scoped, or point); 0 console/TypeError; LLM endpoint `api.ai.sbt` healthy (self-healed 429 retries, documented class, not a gate failure).
- **Drift observed (live source, expected):** DMS open 67→66 mid-session; OLP-SPRNT-9 87→88 rows (active sprint); Semavin DMS 173 total.
- **Planner quirks (safe, non-blocking):** C3s 2/3 — «последнем спринте» misparsed as unrecognized period → typed clarification (safe); M5p non-deterministic routing (short vs full variant), both honest.
- **QA gotchas (recurring):** agent must run with explicit `PO_AGENT_TASK_API_BASE_URL`/`TASK_API_BASE_URL` override (`.env` pins stale 8003); kill the actual python uvicorn child, not the bash wrapper; sprint route complete set is in `complete_tasks`, assignee nested in `source_data.swtr_attributes`.

## Final return

- **Verdict:** `AGENT_CORE_V4_MULTI_INTENT_DESIGN_GREEN_A229M1`
- **TESTED_HEAD:** `9a0477279ae4ed72a70c9f00d092a5a4ff42c7e6`
- **REPORT_COMMIT:** (see git log after push)
- **Traces:** 42 matrix runs + 11 detail probes + 9 spec-exact runs + 2 extra probes; artifacts `/private/tmp/qa229m1/` (`matrix.json`, `probes.json`, `m5s.json`, `c3s.json`, `c6s.json`, `c3s_oracle.json`, `oracle.json`, `m5_raw.json`); agent log `/private/tmp/qa229m1_agent_off.log`.
- **Coverage matrix:** P1 table above (requested goals × proven terminal observations × answer safety × status).
- **Selected option:** **B** — typed API/dialogue goal-coverage guard (postcondition, fail-closed, existing clarification continuation, one-flag rollback, Core untouched).
- **Minimal next owner task:** Stages 1+2 of Option B (detector + guard + offline matrix replay) behind `PO_AGENT_V4_GOAL_COVERAGE_GUARD=false`; then A229M2 for continuation + live re-gate.
- **Core invariant:** Core 6/6 byte-identical to `6fb335d` at START and throughout; no production code/test/config modified in A229M1; flag `PO_AGENT_V4_SYNTHESIS_ELISION` remains `false`; no new production checkpoint created.
