# A229R2 — planner-turn reduction design gate

**Verdict: `AGENT_CORE_V4_PLANNER_TURN_DESIGN_GREEN_A229R2`**

- **Branch:** `feat/core8-real-query-hardening-v2`
- **START_HEAD / TESTED_HEAD:** `b20837a83469226711a4f4edb7e070b31a51a8e1`
- **Functional baseline frozen at:** `checkpoint/v4-complex-task-clarification-green-a229f3r@6fb335d6f67344245a5c65e5c1b5b145759e96da`
- **Role:** QA/performance/source-forensics only. **No production code modified.** (Only untracked QA scripts + this report.)
- **Date:** 2026-10-09
- **Deliverable:** measured model-call anatomy for 8 scenarios, one safest removable turn proven by counterfactual replay, quantified benefit/blast radius, and a single implementation target. No Core/planner change implemented.

---

## P0 — integrity / baseline: GREEN

- `git pull --ff-only` clean; START_HEAD `b20837a`; tracked worktree clean (only local `GIGACODE.md` memory addendum untracked).
- **Core 6/6 byte-identical** to frozen checkpoint `6fb335d` (`agent_core_v4.py`, `agent_core_v4_robust.py`, `agent_core_v4_reliable.py`, `agent_core_v4_completion.py`, `v4_plugin_registry.py`, `llm/real.py`) — `git diff 6fb335d..HEAD` over the six files is empty. (Also byte-identical to `afb6fa1`; `6fb335d` and `b20837a` are API/plugin/docs-only over it.)
- Focused suites: **39/39** (`task_created_period` + `task_semantics_hierarchy` + `task_catalog` + `v4_browser_api_contract`).
- Full V4 blast (`test_agent_core_v4*.py` + `test_v4*.py`): **258/258**. Task API SWTR (9 suites): **57/57**. 0 failed.
- Retained live gates (complex task + period/type/status, latest sprint + type, hierarchy, Overview KPI, task drawer) were certified GREEN on the identical code in A229F3R; re-exercised here via P1 scenarios C/F (hierarchy), A/B/D/E (complex task + period/type/status) — all COMPLETED, `runtime_contract`, source-grounded.
- **No 429/outage windows:** the whole P1 session (40 valid queries, 169 LLM POSTs) had **0 provider 429s, 0 provider reruns, 0 5xx** on both the LLM and source planes. Agent restarted fresh on `b20837a` (clean log) before measurement.

---

## P1 — decompose every LLM/model call

**Two and only two LLM call sites exist** in the production V4 path (exhaustive grep, confirmed by code + live log):

| # | call site | method | purpose | output | skippable? |
|---|-----------|--------|---------|--------|------------|
| A | `agent_core_v4_robust.py:178` | `RobustSkillNativePlannerV4.next_decision` | the single agentic decision: `LOAD` a skill / `CALL` a capability / `READY` | one JSON action (`{load_skill|call|ready}`), typed-DSL fallback on repair | **No** — the decision engine |
| B | `agent_core_v4.py:423` | `ResponseSynthesizerV4.synthesize` | final human-facing Russian prose from validated observations | free-text `answer` (max_tokens 900, temp 0.0) | **Yes** — deterministic fallback already exists (`agent_core_v4.py:657`) |

Each `client.complete()` = exactly one HTTP POST to `https://api.ai.sbt/openai/v1/chat/completions` (`llm/real.py`). One planner decision = one POST; the final synthesis = one POST. Bounded repair can add up to 3 extra POSTs *within a single decision* (primary + 3 recovery, `robust.py:176-196`); a recovered `READY` is rejected (fail-closed).

**Process loop** (`agent_core_v4.py:1186-1355`): `for turn in range(max_steps=8): decision = next_decision(...)`; branch `load_skill` → bookkeeping + `continue` (no extra LLM); `call` → validate literals → deterministic arg-fill → run capability (source HTTP, not LLM) → append observation → deterministic completion check; `ready` → completion gate → `_completed_response`. The terminal `READY` for certified skills is minted by the **deterministic `runtime_contract` path (`agent_core_v4.py:1346`, 0 LLM)**; both completion paths funnel into `_completed_response` (`:633`) which makes the **one synthesis POST (`:655`→`:423`)**.

### Per-scenario call graph (5 valid warm samples each; log-correlated LLM POST counts)

| Scenario (query) | Modal decision sequence | median LLM | LLM range | median wall | terminal result (source-truth) |
|---|---|---|---|---|---|
| **A** Задачи Калачанова в WMB | `LOAD → task.search_assignee → READY(rc) → SYNTH` | **3** | 3–3 | 10.52 s | 6 tasks (Kalachanov WMB = 6 ✓) |
| **B** Задачи в работе в сентябрьском спринте по DMS | `LOAD → space.resolve → sprint.search → task.search → READY(rc) → SYNTH` | **5–6** | 5–6 | 24.21 s | 0 (DMS-SPRNT-3 = 51, all terminal — sprint FINISHED ✓) |
| **C** Покажи задачу DMS-267 | `LOAD → task.lookup → READY(rc) → SYNTH` | **3** | 3–3 | 4.87 s | DMS-267 lookup ✓ |
| **D** Открытые задачи Калачанова в WMB за последние 2 дня | `LOAD → task.search_created → READY(rc) → SYNTH` | **4–5** | 4–7 | 14.20 s | 0 (REAL_EMPTY, drift 0) |
| **E** Открытые задачи Семавина с типом дефект в DMS с 30.09.2026 | `LOAD → space.resolve → task.type_analysis → READY(rc) → SYNTH` | **4** | 4–4 | 10.00 s | 0 (4 open in window, all «Задача», 0 defects ✓) |
| **F** Покажи иерархию DMS-267 | `LOAD → task.hierarchy → READY(rc) → SYNTH` | **3** | 3–3 | 7.44 s | CRPV-90180→DMS-253→DMS-267, epic DMS-349 ✓ |
| **G** …в DMS за период (incomplete) | `LOAD → [space.resolve] → CLARIFY` (no READY/SYNTH) | **3–7** | 3–7 | 13.99 s | NEEDS_CLARIFICATION (no synthesis) |
| **H** continuation of G | `[space.resolve] → task.type_analysis → READY(rc) → SYNTH` | **3** | 3–4 | 16.19 s | 0 (5 constraints, REAL_EMPTY) |

Classified per call: `LOAD`=skill-selection; `space/sprint/member/release.resolve|search|current`=entity-resolution planning; terminal `task.*`=terminal-capability planning; `READY(runtime_contract)`=completion (0 LLM, deterministic); `SYNTH`=final response synthesis (1 LLM, **only in COMPLETED trajectories**).

**Observations (measured):**
- **O1.** The final `SYNTH` call is present in **every COMPLETED trajectory** (A,B,C,D,E,F,H) and **absent in G** (clarification). It is always the **last** LLM call.
- **O2.** Completion is already deterministic (`runtime_contract`, 0 LLM) in all 7 COMPLETED scenarios — the "READY turn" is not an LLM call (see P2-C).
- **O3 (secondary, out of scope):** B (3/5) and D (2/5, up to 7 LLM) show a **redundant second `LOAD`** mid-trajectory (planner loads `task_catalog`, resolves, then re-LOADs the specific skill before the terminal CALL). This is a behavioral/planner inefficiency, not a clean structural one-turn removal — noted for a *future* gate, not proposed here (spec: exactly one round-trip first).
- **O4.** H (continuation) carries no `LOAD` (skills resumed from G via `resume_loaded_skills`), so it is already near-minimal; its only removable turn is also the synthesis.

---

## P2 — identify the single safest removable turn (no implementation)

### Candidate S — final synthesis turn  → **PREFERRED**
`_completed_response` (`agent_core_v4.py:655`) always calls `synthesizer.synthesize(query, observations)` (one POST, `:423`) and **already has a deterministic fallback** (`:657`: join of capability `answer`s) if it throws.
Proven eligible for a **deterministic renderer of the terminal observation's `data`** for the single-part task-collection / exact-lookup subset:
- **Capability answer already contains the exact result** — verified per terminal capability (file:line):
  - `task.search` → `data={count, task_keys, tasks, filters, source}` (`core.py:99-107`); `answer` is just `"Найдено задач: N."` → count/keys fully in `data`.
  - `task.lookup` → `data={task_key, task{20+ fields}, assignee_login, attachment_count, attachments, source}` (`_task_live_handlers.py:264-272`); `answer` self-contained (key+title+status+assignee+attachments).
  - `task.type_analysis` → `data={count, task_keys, type_breakdown, task_type, scope, source}` (`_task_live_handlers.py:700-712`); `answer` self-contained (count + distribution).
  - `task.hierarchy` → `data={parent_chain, root_key, depth, epic_key, related_keys, mode, source}` (`_task_live_handlers.py:838-844`); `answer` self-contained (depth/related/epic).
- **No multi-observation reasoning required** for single-part collection/lookup: the terminal `data` (incl. `filters` which echoes resolved space/assignee/sprint) is sufficient; the LLM adds only conversational polish, no new source facts.
- **No clarification/source/error semantics lost:** the synthesis is invoked only on `COMPLETED`; clarification (`NEEDS_CLARIFICATION`, `FAILED`) never reaches `_completed_response`, so their typed semantics are untouched.
- **Deterministic fallback output is source-grounded:** a renderer of the terminal `data` emits only REAL_AS21 fields (count, task_keys, type_breakdown, task fields, hierarchy) — it cannot invent ids/counts/people/statuses.
- **Eligible scenarios (measured):** A, B, C, D, E, F, H (all COMPLETED, single terminal). **Not eligible:** G (no synthesis) and any multi-part query (renderer must defer to LLM).
- **Savings:** exactly **1 LLM round-trip removed per eligible query**; measured ~1.6–3.5 s in this fast session, ~7.5 s in A229R1 normal conditions; ~12–34% of eligible-query wall (see P5).

### Candidate L — load_skill round-trip (not preferred)
`LOAD` is **structurally mandatory and separate** from the first `CALL`: `catalog.allowed_capabilities(()) == ∅` (`agent_core_v4.py:150`), so a turn-1 CALL is rejected `capability_not_loaded` (`robust.py:143`). Fusing `LOAD`+first-`CALL` requires the runtime to infer the owning skill from a CALL and auto-load it *before* the allowed-capability check — i.e. a **Core planner-protocol change at the governance boundary** (`_decision_allowed`). Progressive disclosure stays intact only if the auto-loaded skill detail is still injected as an observation. It removes 1 turn on *all* queries (not scoped to a safe subset) and touches anti-invention/allowed-capability checks. → MEDIUM-HIGH risk, not the clean first target. (Also note O3: the redundant *second* LOAD in B/D is a related but behavioral issue.)

### Candidate R — resolver-planning round-trip (not preferred)
`space.resolve` is elidable because deterministic arg-completion (`resolved_constraint_arguments`, `agent_core_v4.py:~1247`) + the literal guard already validate/inject `space`/`assignee`; `member.resolve` is fusible via the already-shipped `task.search_assignee`. But elision is a **behavioral** change (the LLM must choose to skip the resolver call) — it does not *structurally* remove a turn, does not guarantee "exactly one" removed, and risks under-resolving when the planner omits a literal the guard can't ground. No phrase routing / hardcoding involved (good), but the non-determinism is the blocker. → MEDIUM-HIGH risk.

### Candidate C — completion/READY turn (NON-CANDIDATE)
**Already eliminated.** For certified terminal skills the final READY is minted by the deterministic `runtime_contract` path (`agent_core_v4.py:1346`) with **0 LLM calls** — measured in all 7 COMPLETED scenarios (O2). The typed completion contracts (`agent_core_v4_completion.py`: `data_keys`/`covers_resolved_constraints`/`_nonempty`) make the READY model-free. No further optimization possible/needed here.

**Preferred candidate: S (final synthesis turn).** It is the only candidate that (a) removes *exactly one* model round-trip, (b) is isolated from planning/governance/completion/clarification, (c) already has a grounded deterministic path, and (d) has a clean external seam.

---

## P3 — safety matrix (LOW / MEDIUM / HIGH, with evidence)

| dimension | **S synthesis** | L load-fusion | R resolver-elision | C ready |
|---|---|---|---|---|
| LLM calls removed (eligible) | **1 / query** (A–F,H) | 1 / query (all) | 0–1, non-deterministic | 0 (already 0) |
| median wall saving | **~1.6–3.5 s** (measured); ~7.5 s normal | ~1 LLM turn | variable | n/a |
| Core files touched if implemented | **none** (swap public `self.synthesizer` in factory + new class) | `agent_core_v4.py` + `robust.py` (`_decision_allowed`, loop) | `agent_core_v4.py` (arg-completion) + catalog | none |
| plugin/API-only alternative? | **yes** — synthesizer is an injectable seam | no (planner protocol) | partial (task.search_assignee exists) | n/a |
| constraint-propagation risk | **LOW** (no args touched) | MEDIUM (auto-load must not widen allowed caps) | MEDIUM (risk of under-resolving) | n/a |
| clarification risk | **LOW** (clarify/FAILED never reach `_completed_response`) | LOW | MEDIUM (resolver skip could drop a constraint → wrong/clarify) | n/a |
| source-grounding risk | **LOW** (renderer uses only terminal `data`, `source=REAL_AS21`) | LOW | MEDIUM | n/a |
| progressive-disclosure risk | **LOW** (skills still loaded normally) | MEDIUM (must still inject skill detail) | LOW | n/a |
| regression blast radius | **LOW** (only the `answer` string; facts/count/keys/evidence unchanged) | MEDIUM (governance path) | MEDIUM (planner behavior) | n/a |
| rollback simplicity | **HIGH** (feature flag off → LLM synthesis) | MEDIUM | MEDIUM | n/a |

**Selected preferred candidate: S.** It is the only row that is LOW across constraint-propagation / clarification / source-grounding / blast-radius while removing exactly one round-trip.

---

## P4 — counterfactual replay (no-code) for Candidate S

Method: replay each recorded A–H trajectory with the single `SYNTH` call elided and replaced by a deterministic render of the terminal observation's `data`. Because `synthesize` is invoked **only** inside `_completed_response` (the terminal return of `process()`), its output (the `answer` string) is used **only** as the final response text and **never** feeds back into `next_decision`, the completion contract, `_validate_call_literals`, or any capability argument. Therefore the executed capabilities and their arguments are **byte-identical** to the recorded run.

| Scenario | current LLM (median) | after S (median) | call that disappears | executed caps/args after S | eligible? |
|---|---|---|---|---|---|
| A | 3 | **2** | `SYNTH` (`agent_core_v4.py:423`) | `task.search_assignee{Калачанов, WMB}` — identical | yes |
| B | 5–6 | **4–5** | `SYNTH` | `space.resolve{DMS}`, `sprint.search{DMS,сентябрь}`, `task.search{DMS-SPRNT-3, В работе}` — identical | yes |
| C | 3 | **2** | `SYNTH` | `task.lookup{DMS-267}` — identical | yes |
| D | 4–5 | **3–4** | `SYNTH` | `task.search_created{последние 2 дня, Калачанов, WMB, not_completed}` — identical | yes |
| E | 4 | **3** | `SYNTH` | `space.resolve{DMS}`, `task.type_analysis{дефект, Семавин, DMS, open, с 30.09.2026}` — identical | yes |
| F | 3 | **2** | `SYNTH` | `task.hierarchy{DMS-267, inspect}` — identical | yes |
| G | 3–7 | **3–7 (unchanged)** | (none — no synthesis call) | clarification trajectory unchanged | **no** (not eligible) |
| H | 3 | **2** | `SYNTH` | `task.type_analysis{дефект, Семавин, DMS, not_completed, с 30.09.2026 по сегодняшний день}` — identical | yes |

- The removed call is always the **last** LLM POST (the synthesis). Bounded-repair extras (seen transiently in H run1/run5) are planner-decision retries — **unaffected** by S (S removes only the synthesis, not decision retries).
- **Factual trajectory identical for all 7 eligible runs** (A–F, H): same capabilities, same arguments, same `runtime_contract` completion, same `data`/`evidence`. Only the `answer` prose changes (LLM wording → deterministic render of the same terminal `data`). Count/keys/type_breakdown are preserved because they are read straight from the terminal `data`.
- **G unchanged** (no synthesis to remove). Any **multi-part** query (not in A–H) is also unchanged — the renderer defers to the LLM synthesizer when more than the single terminal observation is needed.
- **Conclusion:** the counterfactual is provably safe — the design keeps the exact factual trajectory identical for all eligible factual runs. (No RED condition triggered.)

---

## P5 — target selection / implementation boundary

**Recommended implementation target: `SYNTHESIS_TURN_ELISION`.**

1. **Minimal files that would change:**
   - **New** `harness/v4_synthesis_elision.py` — a `TerminalSynthesisElider` implementing the same `synthesize(user_query, observations) -> str` interface as `ResponseSynthesizerV4`. It (a) detects an eligible trajectory (single terminal capability in `{task.search, task.search_assignee, task.search_created, task.search_created_in_progress, task.search_status, task.search_sprint, task.search_text, task.search_attachments, task.search_excel/pdf/msg, task.type_analysis, task.lookup, task.hierarchy, task.summary, task.quality, task.acceptance, task.blockers, task.missing_requirements, task.time_in_status, task.history, task.aging, task.similar, task.dependencies}`), (b) renders a deterministic Russian answer **only from the terminal observation's `data`/`answer`/`evidence`** (count, task_keys, type_breakdown, task fields, hierarchy) — source-grounded, no invented facts, count preserved; (c) for non-eligible trajectories **delegates to the wrapped LLM synthesizer** (no behavior change).
   - **`harness/runtime_factory.py`** — when the feature flag is on, wrap the synthesizer after the V4 runtime is built: `v4_runtime.synthesizer = TerminalSynthesisElider(underlying=v4_runtime.synthesizer)`.
   - **`config/settings.py`** — add the flag (default `False`).
2. **Does Agent Core change?** **No.** `_completed_response` already calls `self.synthesizer.synthesize(...)` with a deterministic fallback; `synthesizer` is a public, swappable object. The elider is an external decorator injected at the factory seam — the spec's preferred "external/plugin/synthesizer seam over Core."
3. **Feature flag / rollback seam:** `PO_AGENT_V4_SYNTHESIS_ELISION` (env, default `false`). `false` → current LLM synthesis (byte-identical behavior). `true` → deterministic for eligible single-part collection/lookup, LLM for everything else. Rollback = unset the flag.
4. **Exact tests to add (before implementation):**
   - Unit: elider renders the correct deterministic answer for `task.search` / `task.lookup` / `task.hierarchy` / `task.type_analysis` fixture observations (assert count + task_keys preserved; assert output uses only `data` fields — no invented ids/counts/people/statuses).
   - Unit: elider **delegates to the LLM synthesizer** (mock) for a multi-observation / non-eligible trajectory (no deterministic short-circuit).
   - Unit: elider is a no-op passthrough for `NEEDS_CLARIFICATION`/`FAILED` (it is only ever invoked on COMPLETED).
   - Integration (flag on): `Задачи Калачанова в WMB` makes **2** LLM calls (not 3) with **identical** count/task_keys; `Покажи иерархию DMS-267` makes 2 (not 3) with identical facts.
   - Regression: the A/B/C re-gate set below.
5. **Exact A/B/C re-gate set:** A (3→2, result identical), B (5-6→4-5, identical), C (3→2, identical), D (4-5→3-4, identical), E (4→3, identical), F (3→2, identical), H (3→2, identical), G (unchanged, still typed clarification) — plus the A229F3R retained gates (type+current-sprint, hierarchy, Overview KPI, task drawer) and the A229F3 complex-composition invariants (no silent period drop; clarification continuity).
6. **Expected improvement:** −1 LLM round-trip per eligible query (3→2, 4→3, 5→4, 6→5). Measured median wall: A 10.52→~7 s, C 4.87→~3.3 s, F 7.44→~5.1 s, E 10.0→~7.5 s, B 24.21→~21 s, D 14.2→~11 s, H 16.19→~13 s (i.e. **~12–34% wall reduction**; ~7.5 s/query in A229R1 normal conditions). Zero change to source reads, planning, governance, or completion.
7. **Explicit non-goals:** no planner/Core/orchestration change; no LOAD+CALL fusion (Candidate L); no resolver elision (Candidate R); no multi-part-query prose change; no source/data-plane change; no multi-agent behavior; no change to clarification/error taxonomy.

**Non-preferred candidates (deferred, documented not implemented):** Candidate L (LOAD fusion) and the O3 redundant-second-LOAD in B/D are the next-highest-leverage targets but require Core planner-protocol changes at the governance boundary — to be scoped in a *separate* future gate, after S is shipped, never simultaneously (spec: one round-trip first).

---

## P6 — GVS5H / multi-agent interaction note

The selected optimization is **compatible** with the future V5 manager/worker/verifier sidecar and does **not** make V4 more monolithic or phrase-routed:
- `SYNTHESIS_TURN_ELISION` is a **pure presentation-layer** change at the synthesizer seam. It keeps the governed **capability/evidence plane** (typed capabilities, validated observations, `source=REAL_AS21` evidence, deterministic completion contracts) fully intact and versioned — exactly the plane a V5 verifier would consume to re-check a worker's factual claims.
- Because the elider renders **only** from validated observations (never inventing facts), a V5 verifier can independently re-derive the same count/keys from the recorded evidence — the deterministic answer is *more* auditable than the LLM prose, not less.
- No phrase routing is introduced (the eligibility test is on the **executed terminal capability id + observation shape**, not on query text), so the V4 runtime stays capability-driven and can be lifted into a V5 worker unchanged. The elider is a swappable sidecar component, not a rewire of the planner.
- A229R2 changes **no** planning/orchestration code, so it cannot couple V4 planner turns to any future manager/worker loop.

---

## Verdict

`AGENT_CORE_V4_PLANNER_TURN_DESIGN_GREEN_A229R2`

GREEN criteria met:
- **Model-call anatomy measured** — every LLM POST reconstructed per scenario (P1): exactly two call sites; 7/8 scenarios COMPLETED with a removable final synthesis; completion already deterministic (0 LLM) in all of them.
- **One preferred removable turn proven by counterfactual replay** — Candidate S (final synthesis, `agent_core_v4.py:423`) removes exactly one round-trip on A–F,H with byte-identical factual trajectory; G unchanged.
- **Benefit and blast radius quantified** — −1 LLM call / eligible query, ~12–34% wall (measured), ~7.5 s normal; blast radius limited to the `answer` string; LOW risk across constraint-propagation/clarification/source-grounding; trivial flag rollback.
- **No code changed** — Core 6/6 byte-identical; only untracked QA scripts + this report.

**Recommendation:** proceed to implement `SYNTHESIS_TURN_ELISION` at the synthesizer seam (P5 boundary) behind `PO_AGENT_V4_SYNTHESIS_ELISION`, then run the A/B/C re-gate set. Do **not** bundle Candidate L / the O3 redundant-LOAD fix in the same change.

**QA artifacts (untracked):** `qa_229r2_p1_runner.py`, `qa_229r2_p1_parse.py` (repo root); evidence in `/private/tmp/qa229r2/` (`p1_runs.json`, `p1_callgraph.json`, `p1.log`); agent log `/private/tmp/qa229r2_agent.log`.
**Services left running:** agent 8004 (fresh, `b20837a`), task-api 8241, MCP 3000, vite [::1]:5175.
