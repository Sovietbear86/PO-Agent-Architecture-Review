# AGENT_CORE_V4_MISSING_GOAL_EXECUTION_DESIGN_A229M22BD

**Verdict:** `AGENT_CORE_V4_MISSING_GOAL_EXECUTION_DESIGN_GREEN_A229M22BD`
—a safe, detailed, zero-Core implementation path is PROVEN (design-level, no code change).
**Not** a functional implementation GREEN.
**TESTED_HEAD:** `2a50ce7d310ee9dd88c545b6e88330978e9e760d`
**Core 6 hashes (byte-identical to `checkpoint/v4-complex-task-clarification-green-a229f3r` @ `6fb335d`):**
`agent_core_v4.py 52100ca1`, `agent_core_v4_robust.py 3bdb4d09`,
`agent_core_v4_reliable.py 1f7562dc`, `agent_core_v4_completion.py cf75a6d6`,
`v4_plugin_registry.py d82929d1`, `llm/real.py 1cc10e12`.
**Chosen alternative:** `BOUNDED_V4_PER_GOAL_EXECUTOR`.

## P0 — baselines: GREEN

- TESTED_HEAD `2a50ce7` (owner docs `bc43dfa` assign + `2a50ce7` plan certification); tracked
  state clean apart from documented `M GIGACODE.md`. Prior certified report
  `AGENT_CORE_V4_GOAL_STATE_PRESERVATION_GREEN_A229M22AR2` present at commit `8697e68`.
- Baseline suites: focused goal coverage + full V4 blast `test_agent_core_v4*.py`+`test_v4*.py`
  = **290 passed / 0 failed**; Task API SWTR smoke (canonical + task-query partial) =
  **15 passed**. No new baseline defects. No STOP.

## P0.3/P0.4 — wiring map (exact seams, file:line)

| Seam | Location | Shape |
|---|---|---|
| Goal detector (deterministic, no phrase router) | `api/v1/goal_coverage.py:43-91` `detect_goals` | kinds: `person_tasks` (person+space), `task_lookup` / `task_hierarchy` / `task_relations` (task key), `()` on `_COMPARE` (line 82-83); `RequestGoal{goal_id, kind, span, task_key, person, space, required_evidence}` (:26-33) |
| Goal → governed capability (credit matcher = execution target, same table) | `goal_coverage.py:158-186` `check_goal_coverage` | `task_lookup`→`task.lookup{task_key}`; `task_hierarchy`→`task.hierarchy{task_key,mode=inspect}`; `task_relations`→`task.hierarchy|task.relations{task_key}`; `person_tasks`→`task.search*` + `member.resolve` identity binding (:123-149) |
| Governed per-capability execution | `harness/agent_core_v4.py:1140` `process()` → :1267 allow-list check → :1279-1302 arg resolution + `_handlers[capability_id](resolved_args)` | `CapabilityHandlerV4 = Callable[[dict[str,str]], Awaitable[CapabilityResult]]` (:41) |
| Handler table (governed registry-bound) | `agent_core_v4_pluginized.py:28,35` `handlers = registry.bind_handlers(self)`; `v4_plugin_registry.py:215-236` `bind_handlers` (handler_method / handler_builder / legacy facade, fixed_arguments override :175-188, instrumented :190-213) | every capability = same permission/schema/source-scope contract as planner use |
| Continuation re-entry | `harness/contracts.py:47-49` `HarnessRequest.resume_loaded_skills / resume_observations / required_completion_skills`; re-seeded in `agent_core_v4.py:1155-1174` (planner observations, str args) | server-owned, not client-injectable (client surface `QueryRequest`: `query, session_id, clarification_id, clarification_option` — `__init__.py:62-66`) |
| Private credit view (Stage A) | `goal_coverage.py:282-322` `_credit_prior_observations`; wiring `:340-341`, carry `:359` | REAL_AS21 + canonical shape + ≤6 obs + ≤8192 B re-validated; public `data.results` untouched |
| Public wrapper seam precedent | `harness/v4_synthesis_elision.py:41-125` `TerminalSynthesisElider` injected in `harness/runtime_factory.py:92-93` by reassigning `v4_runtime.synthesizer` (no Core edit) | exact pattern for a `process`-level wrapper |
| Bounded pending state | `__init__.py:28,32-43` TTL 15 min / `PendingClarification` / `_pending_clarifications` (100-bound + expiry sweep :449-454) | in-memory, restart-loses fail-closed (typed `clarification_context_lost` :324-336) |
| Status contract | `contracts.py:10-14` `ResponseStatus{COMPLETED, NEEDS_CLARIFICATION, PARTIAL, FAILED}`; UI already handles PARTIAL: `frontend/src/api/client.ts:15`, `resultState.ts:142`, `WorkspaceApp.tsx:224` | **partial success representable with zero protocol/enum/UI change** |

## P1 — safe execution seam: Option A (repeated governed `process`)

**A. Bounded repeated `V4Runtime.process(HarnessRequest)` for ONE typed missing goal — CHosen.**
- Goal → capability mapping reuses `check_goal_coverage`'s own table (:158-186): the capability
  that would PROVE the goal is the capability that EXECUTES it. No name/space/phrase routing is
  invented; args are the goal's immutable canonical fields (`task_key` from `_TASK_KEY` regex
  match span, `space` from `_COLLECTION` group, `reference` = resolved login).
- Canonical keys/people/sprint stay canonical because the scheduler passes **only** the goal's
  stored fields; person goals use the already-resolved `member_login` carried in the prior
  REAL_AS21 `member.resolve` observation (same binding rule as credit :123-149) — the same
  `assignees/resolve` path, no inference.
- Each execution = one full governed `process()`: skill disclosure via `resume_loaded_skills`,
  allow-list (`allowed_capabilities`), `_validate_call_literals`, fixed-argument overrides,
  REAL_AS21 handlers, instrumented logging, error taxonomy (429 → typed `v4_runtime_failure`;
  source 5xx → typed source_unavailable; both already live-proven in A229M2.2AR/A229M2.2AR2).
- Evidence: the execution's `CapabilityResult.data` is a terminal row; it becomes creditable
  the same way current-turn rows are (`_terminal_results`), and the prior-credit view
  (`_credit_prior_observations`) already validates carried rows identically — symmetric.
- Budget/termination: per missing goal ≤1 extra `process()` (planner 1-3 LLM turns + 1 source
  op each); scheduler caps (P2). No new client: same adapter, same registry, same handlers.
- **Core change: ZERO** (wrapper injected like `TerminalSynthesisElider` at the API seam).

**B. Direct plugin-capability execution (call `runtime._handlers[cap](args)` from the API).**
- Same handlers/contract, but the API layer would bypass the runtime's own governance steps
  (literal validation, fixed-arg application ordering with runtime state, trajectory/completion
  bookkeeping, session-context validation). `bind_handlers` is a runtime-bound factory
  (`handler_method` lookups on `self` — `v4_plugin_registry.py:219-224`): re-invoking handlers
  outside `process()` risks contract drift as capabilities evolve (the recurring
  A205-1/A205B/A217C signature-drift class). **Rejected**: weaker auditability, no completion/
  disclosure semantics, higher drift risk for zero latency gain (the per-goal LLM turn is the
  real cost, not handler invocation).

**C. Sidecar using the same governed executor.**
- Process isolation adds a second runtime instance (double adapter/LLM clients, separate
  pending-state store → two sources of truth for the same session), no permission benefit
  (same credentials, same source). **Rejected**: unnecessary for a bounded in-request loop.

Rejected by rule (all options): skipping permission/contract checks, inventing source facts,
or depending on the model voluntarily completing all goals.

## P2 — typed goal frontier + bounded scheduler

```
GoalFrontier(goal_id, kind, span,
             args: dict[str,str]        # immutable, from detect_goals fields + member.resolve login
             deps: tuple[goal_id]       # e.g. person_tasks -> member.resolve (same-turn)
             capability: str            # from the check_goal_coverage table
             evidence_refs: tuple[str], # observation steps that prove it
             status: PENDING | PROVEN | BLOCKED | FAILED,
             attempts: int)
```

Rules (all enforceable at the API seam, flag-gated):
1. `len(goals) ≤ 3` independent goals else typed NEEDS_CLARIFICATION (detector already returns
   them ordered; comparisons return `()` — M5 stays one analytical goal, not two lookups).
2. `attempts ≤ 2` per missing goal; `turns ≤ 8` global; LLM budget ≤ 12 calls/continuation;
   each execution has its own per-call timeout (existing uvicorn/client timeouts, ≤120 s) —
   proposed values, NOT current defaults.
3. PROVEN goals are credit-only: scheduler never re-launches a PROVEN goal (P3 proves
   `proven_not_reexecuted=true` on all COMPLETED replays).
4. Only a PENDING missing goal is launched, one at a time (`in_flight ≤ 1` per session;
   pending store already 1-entry-per-session → racing continuations impossible by key).
5. Outcome of one goal: source-backed validation of the terminal row (same `check_goal_coverage`
   predicates: source not unavailable, `source_complete` not False) → PROVEN; typed source/429
   failure → goal FAILED, continuation ends with **typed `PARTIAL`** (status exists in
   `contracts.py:13`, UI already renders it) listing proven + failed goals in
   `data._agent_core_v4.goal_coverage` — never false COMPLETED, never a misleading
   NEEDS_CLARIFICATION for an unambiguously-skipped action.
6. Genuinely ambiguous goal (no canonical arg derivable, e.g. unresolvable person) → typed
   NEEDS_CLARIFICATION with the existing options; never re-ask a clear request.
7. No repeated resume loop: the scheduler runs to exhaustion inside ONE `_run_query`
   (server-side), so the browser sees exactly one response (COMPLETED or PARTIAL).
8. Private observations never surface as public `data.results`: only rows from THIS request's
   executions are public; carried rows enter only the private credit view
   (`_credit_prior_observations` pattern already proven in A229M2.2AR2).

**Status representability PROVEN without protocol change:** `PARTIAL` already in
`ResponseStatus` (`contracts.py:13`), serialized via `HarnessResponse.to_dict`
(`contracts.py:85`), typed in the client (`client.ts:15`), rendered (`resultState.ts:142`,
`WorkspaceApp.tsx:224` COMPLETED|PARTIAL branch).

## P3 — deterministic no-code replay on exact REAL AS21 evidence (fresh oracle, read-only task-api 8241 @ 48 MCP tools)

Oracle (2026-10-15 live): K WMB = 6 (WMB-30482/30000/29890/29995/29830/29242), S DMS = 175
(live drift +2 vs A229M2.2AR2 173, drift-tolerant), DMS-267 parent = DMS-253 (decomposition,
`mcp:get_unit_links`), negative control DMS-380 = 1 relation.

| case | goals | execution trace (turn: goal → capability) | verdict | budget |
|---|---|---|---|---|
| M1 | 2 person_tasks | t1 g1→task.search_assignee(WMB); t2 g2→task.search_assignee(DMS) | COMPLETED (2 proven) | 2 LLM ≤12, turns 3 ≤8, proven-not-reexecuted ✓ |
| M2 | lookup+hierarchy | t1 g1→task.hierarchy(DMS-267,inspect); t2 g2→task.lookup(DMS-267) | COMPLETED, prior lookup never re-read (credit-only) | ✓ |
| M4 | 3 goals | t1 hierarchy; t2 lookup; t3 search_assignee(WMB) | COMPLETED (3 proven) | 3 LLM, turns 4 ✓ |
| C5 | lookup+relations | t1 lookup; t2 task.hierarchy(inspect) | COMPLETED — hierarchy evidence satisfies `task_relations` coverage for this real linked task (`check_goal_coverage:173`); interchangeability boundary = verified coverage, not assumption (negative control DMS-380 single-link proven separately) | ✓ |
| M5 | `Сравни незакрытые задачи DMS и OLP` | `detect_goals` → `()` (`_COMPARE`, goal_coverage.py:82) | guard INERT → one analytical goal, single governed path; NOT split into two lookup goals | ✓ (OPEN: comparison goal typing deferred to next stage by design) |
| C1 | 1 goal (person_tasks, multi-filter) | `len(goals)=1` | guard INERT; filters stay inside the single capability args, never split by «и» | ✓ |
| M2 + provider-429 | 2 | t1 g1 FAILED (429); t2 g2 proven | **PARTIAL (typed)** — failed goal listed, proven goal kept, no false COMPLETED | ✓ |
| M2 + AS21 outage | 2 | t1 FAILED, t2 FAILED | **PARTIAL (typed)** with source taxonomy; no local fallback | ✓ |

Additional P3 checks: expired state / cross-session replay / incomplete snapshot reduce to the
existing Stage-A fail-closed set (typed `clarification_context_lost`; wrong session key miss;
`source_complete=False` rows never credit — all re-proven A229M2.2AR2, unchanged by this design
since the scheduler reuses the same validation). **Genuinely unsupported → OPEN:** comparison
(M5) goal typing, free-text multi-intent beyond the 4 detector kinds, sprint-relative period
goals in person collections.

## P4 — security gate (pre-implementation)

Minimal authenticated-ownership contract (deployment blocker, separate track):
- Server-issued session binding: `session_id` must be minted+signed by the auth layer
  (e.g. JWT session claim); API must reject unknown/foreign session tokens BEFORE any
  pending-state access (`_prepare_query` :344-376 and `_remember_clarification` :424-466
  both key on the client-supplied `session_id` — the exact injection point).
- Continuation tokens: `clarification_id` (already uuid4, one-shot :431-433, consumed on
  restore :376) stays as the per-principal capability to consume a pending record; add
  principal claim check on the pending entry (store `principal` in
  `PendingClarification`).
- Per-principal quota: bound `_pending_clarifications` per principal (reuse the 100-entry
  sweep :449-454 with per-principal counters); TTL 15 min + eviction already proven;
  restart = in-memory loss → typed fail-closed (proven); racing clarifications impossible by
  single-key-per-session + one-shot token (proven).
- **Local-only QA proceeds** (single principal, trusted loopback) **while remote deployment
  stays blocked** — the scheduler adds no new trust surface: it executes within the same
  request/session that already passed (or will pass) the auth check; it never reads another
  session's pending state. No token/secrets in this report.

## P5 — decision: `BOUNDED_V4_PER_GOAL_EXECUTOR`

### Minimal file-level implementation spec (owner, ZERO Core edits)

1. `po-agent-platform-v2/src/po_agent/api/v1/missing_goal_execution.py` (NEW, ~150 lines):
   `GoalFrontier` dataclass + `plan_frontier(response, query, carried)` (reuses
   `detect_goals` / `check_goal_coverage` mapping table), `run_bounded_completion(bundle,
   original_query, goals, carried, session_id)` — loop ≤ `MAX_MISSING_GOALS=3` goals,
   ≤2 attempts each, one `bundle.v4_runtime.process(HarnessRequest(query=<canonical
   single-goal phrasing from goal fields>, resume_loaded_skills, resume_observations=carried))`
   per goal, `asyncio.wait_for` ≤120 s each; classify outcomes via the SAME
   `check_goal_coverage` on accumulated public results; terminate →
   COMPLETED / PARTIAL / typed NEEDS_CLARIFICATION.
2. `po-agent-platform-v2/src/po_agent/api/v1/__init__.py` (+~15 lines, behind
   `PO_AGENT_V4_MISSING_GOAL_EXECUTION=false` proposal, OFF default): in the
   `v4_goal_coverage_guard_enabled` branch, when `guard_completed_goal_coverage` produced a
   NC with `v4_goal_coverage_incomplete` AND the missing-goal flag is ON AND
   `len(unproven) ≤ 3` → call `run_bounded_completion`; on success replace response with the
   final one (public `results` = this-request executions only; carried rows stay private).
3. NO change to: Core 6 files, planner, registry, plugins, synthesis elision, UI, prompts.

### Test-before-code matrix (all non-mocked, REAL AS21 via task-api)
- 2-turn M2: single-request COMPLETED, both goals, public results=this-request, prior lookup
  credit-only (0 lookup re-reads) — the A229M2.2AR2 P1 shape, now single-turn.
- M4 3-goal single-request COMPLETED; M1 both persons; C5 relations-via-hierarchy.
- 429-injection (offline mock LLM 429) → PARTIAL typed; source-502-injection → PARTIAL typed;
  0 false COMPLETED across all.
- M5/C1/C3/C4 inertness: detector `()`/single-goal → guard not invoked, byte-identical to
  flag-OFF response.
- Security: foreign-session pending access rejected (contract test); one-shot token; TTL;
  per-principal bound; restart fail-closed.
- Flag-OFF parity: full A229M2.2AR2 gate retained (M2 3/3, M4/C5 NC-credit, 290/290).

### Exact STOP/RED boundaries (implementation gate)
1. Any Core-6 hash change → RED. 2. Any public `data.results` containing a carried row →
RED (forgery). 3. Any unproven goal claimed in answer/`goal_coverage.proven` → RED.
4. False COMPLETED on any injected failure → RED. 5. LLM/source budget exceeded → RED.
6. Flag-OFF parity drift (A229M2.2AR2 suite) → RED. 7. New tenant-wide/unscoped source call
→ RED. 8. Session-auth blocker regressed → RED.

### A/B REAL AS21 oracle (regeneration command retained in
`/private/tmp/qa229m22bd/oracle.py`): K WMB count+keys, S DMS count, DMS-267 parent DMS-253,
DMS-380 relation count; counts drift-tolerant (record at run start, re-probe at end,
before/after containment).

### (a) Local feature behavior vs (b) deployment readiness
(a) Local: feature fully usable behind the proposal flag with single-principal loopback QA —
this design proves the safe path. (b) Remote multi-user: STILL BLOCKED by absent
authenticated session ownership (P4); do not label deployment-ready until fixed separately.
Scope honesty: the bounded executor covers only the 4 detector goal kinds (lookup/hierarchy/
relations/person-collection) up to 3 goals; it is **not** universal multi-intent support.

## OPEN blockers
1. Session authentication/ownership (deployment, separate track) — unchanged.
2. Comparison (M5) + free-text multi-intent goal typing — next stage, explicitly out of scope.
3. LLM 429 rate-limit windows (environmental) — typed fail-closed, proven PARTIAL path covers it.

## Services after QA
Read-only MCP-SWTR 3000 + task-api 8241 started for the oracle (QA, no code change); agent 8004
left at `1cd6446` flags OFF (unchanged from A229M2.2AR2 restore). No flags flipped, no
checkpoint, no A229M2.2B implementation started.

## Exact next owner assignment
Implement `BOUNDED_V4_PER_GOAL_EXECUTOR` per the P5 spec (1 new file + ~15-line API wiring,
flag `PO_AGENT_V4_MISSING_GOAL_EXECUTION` default false, zero Core edits), with the
test-before-code matrix and STOP boundaries above; then a full re-gate (A/B REAL AS21, flag
parity, PARTIAL injection, security) — and separately, the authenticated session-ownership
track before any remote deployment.
